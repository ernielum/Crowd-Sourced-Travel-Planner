# Standard library imports
from functools import wraps
import json
from os import environ as env
from urllib.request import urlopen
from urllib.parse import quote_plus, urlencode

# Third-party imports
from dotenv import find_dotenv, load_dotenv
#from flask import Flask, request, jsonify, redirect, render_template, session, url_for, _request_ctx_stack
from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_cors import cross_origin
from jose import jwt
from werkzeug.exceptions import HTTPException
from authlib.integrations.flask_client import OAuth
from google.cloud import datastore
import requests

# Local application imports
# import constants

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

client = datastore.Client()

ALGORITHMS = ["RS256"]


# ----------------------------------------------------------------------------- OAUTH

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    api_base_url=f'https://{env.get("AUTH0_DOMAIN")}',
    access_token_url=f'https://{env.get("AUTH0_DOMAIN")}/oauth/token',
    authorize_url=f'https://{env.get("AUTH0_DOMAIN")}/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# This code is adapted from https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen(f'https://{env.get("AUTH0_DOMAIN")}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=env.get("AUTH0_CLIENT_ID"),
                issuer=f'https://{env.get("AUTH0_DOMAIN")}/'
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)

# ----------------------------------------------------------------------------- HOMEPAGE
@app.route('/')
def welcome():
    return render_template('welcome.html')

# ----------------------------------------------------------------------------- LOGIN/SIGN-UP

@app.route('/login')
def login():
    return oauth.auth0.authorize_redirect(redirect_uri=url_for("callback", _external=True))

@app.route('/callback')
def callback():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    jwt_token = auth0.token['id_token']
    session['jwt'] = jwt_token 
    session['profile'] = userinfo 

    # Check if user is already registered
    user_id = userinfo['sub'] 
    query = client.query(kind='User')
    query.add_filter('user_id', '=', user_id)
    results = list(query.fetch())

    # If user not registered, create new User entity
    if len(results) == 0:
        new_user = datastore.Entity(client.key('User'))
        new_user.update({
            'user_id': user_id
        })
        client.put(new_user)

    return redirect('/user-info')

@app.route('/user-info')
def user_info():
    #user_id = session.get('profile')['sub']  #Temporarily commented out for FE dev
    jwt_token = session.get('jwt')  
    #return render_template('userinfo.html', jwt=jwt_token, user_id=user_id, user_info=session.get('profile')) #Temporarily commented out for FE dev
    return render_template('userinfo.html', jwt=jwt_token, user_info=session.get('profile'))
# ----------------------------------------------------------------------------- USERS

@app.route('/user-info')
def user_info():
    """
    Gets a user's profile.
    """

    # Ensure user is logged in
    if 'profile' in session:
        return render_template('user_info.html', user_info=session['profile'])
    else:
        return redirect('/')

@app.route('/users/<userId>', methods=['PUT'])
def update_user(userId):
    """
    Updates a user's Datastore attributes.

    Since the user's basic profile (email, name, etc.) is managed by Auth0, this endpoint will focus 
    on application-specific attributes (e.g., preferences, display name) that are stored in Datastore.

    The user's password is stored by the service provider, not by OAuth or the third-party application 
    using OAuth for authentication and authorization. In the context of using OAuth for logging into a 
    third-party app with a Google account, for example, Google is the service provider that stores the 
    user's password.
    """
    try:
        payload = verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    # Ensure the authenticated user matches the userId to update
    if payload['sub'] != userId:
        return jsonify({"error": "Unauthorized"}), 403

    user_key = client.key('User', userId)
    user = client.get(key=user_key)

    # Ensure user exists
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Retrieve new user info
    content = request.get_json()

    # TODO: update user attributes that can be modified
    # Update user info (display name and preferences)
    if 'displayName' in content:
        user['displayName'] = content['displayName']
    if 'preferences' in content:
        user['preferences'] = content['preferences']

    client.put(user)

    return jsonify({"message": "User updated successfully"}), 200

@app.route('/users/<userId>', methods=['DELETE'])
def delete_user(userId):
    """
    Allows a user to be deleted.
    """
    try:
        payload = verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    # Ensure the authenticated user matches the userId to delete
    if payload['sub'] != userId:
        return jsonify({"error": "Unauthorized"}), 403

    user_key = client.key('User', userId)
    user = client.get(key=user_key)

    # Ensure user exists
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Delete user from datastore
    client.delete(user_key)

    # TODO: delete the user from Auth0 as well

    return jsonify({"message": "User deleted successfully"}), 204

# ----------------------------------------------------------------------------- TRIPS

@app.route('/users/<userId>/trips', methods=['POST'])
def create_trip(userId):
    """
    Create a new trip for a user.

    Requires: JWT authentication and authorization.
              JSON payload with trip details (name).
    """
    # TODO: integrate with google maps api

    try:
        payload = verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    if payload['sub'] != userId:
        return jsonify({"error": "Unauthorized"}), 403

    content = request.get_json()
    new_trip = datastore.Entity(key=client.key('Trip'))
    new_trip.update({
        'userId': userId,
        'name': content['name'],
    })
    client.put(new_trip)
    return jsonify(new_trip), 201

@app.route('/users/<userId>/trips', methods=['GET'])
def list_user_trips(userId):
    """
    Returns a list of all trips for a user.

    Requires JWT authentication and the user must be authorized to view their trips.
    """
    try:
        payload = verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    if payload['sub'] != userId:
        return jsonify({"error": "Unauthorized"}), 403

    query = client.query(kind='Trip')
    query.add_filter('userId', '=', userId)
    trips = list(query.fetch())
    return jsonify(trips), 200

@app.route('/trips/<tripId>', methods=['GET'])
def get_trip(tripId):
    """
    Retrieve details of a specific trip.

    Requires: JWT authentication
              tripId parameter.
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    trip_key = client.key('Trip', int(tripId))
    trip = client.get(key=trip_key)
    if not trip:
        return jsonify({"error": "Trip not found"}), 404
    return jsonify(trip), 200

@app.route('/trips/<tripId>', methods=['PUT'])
def update_trip(tripId):
    """
    Update a trip's details.

    Requires: JWT authentication and authorization.
              JSON payload with the updated trip details
              tripId parameter
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    trip_key = client.key('Trip', int(tripId))
    trip = client.get(key=trip_key)
    if not trip:
        return jsonify({"error": "Trip not found"}), 404

    content = request.get_json()
    trip.update({
        'location': content.get('location', trip['location']),
        'name': content.get('name', trip['name']),
        'description': content.get('description', trip.get('description', '')),
        'startDate': content.get('startDate', trip.get('startDate')),
        'endDate': content.get('endDate', trip.get('endDate')),
    })
    client.put(trip)
    return jsonify(trip), 200

@app.route('/trips/<tripId>', methods=['DELETE'])
def delete_trip(tripId):
    """
    Delete a trip.

    Requires: JWT authentication and authorization.
              tripId parameter 
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    trip_key = client.key('Trip', int(tripId))
    trip = client.get(key=trip_key)
    if not trip:
        return jsonify({"error": "Trip not found"}), 404

    client.delete(trip_key)
    return jsonify({"message": "Trip deleted successfully"}), 204

# ----------------------------------------------------------------------------- PINS

@app.route('/experiences', methods=['GET'])
def list_experiences():
    """
    List all experiences, with optional filters for type, location, and rating.
    Supports query parameters for filtering: 'type', 'location', and 'min_rating'.
    """
    # Extract query parameters for filtering
    exp_type = request.args.get('type', None)
    location = request.args.get('location', None)
    min_rating = request.args.get('min_rating', None)

    query = client.query(kind='Experience')
    if exp_type:
        query.add_filter('type', '=', exp_type)
    if location:
        query.add_filter('location', '=', location)
    if min_rating:
        query.add_filter('rating', '>=', float(min_rating))

    experiences = list(query.fetch())
    return jsonify(experiences), 200

@app.route('/trips/<tripId>/experiences', methods=['POST'])
def pin_experience(tripId):
    """
    Pin an experience to a trip.

    Requires: JWT authentication. 
              JSON with the experience's details.
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    content = request.get_json()
    new_pin = datastore.Entity(client.key('PinnedExperience'))
    new_pin.update({
        'tripId': tripId,
        'experienceId': content['experienceId'],
        'userId': content['userId']  # Assuming the user ID is sent in the request body
    })
    client.put(new_pin)
    return jsonify(new_pin), 201

@app.route('/trips/<tripId>/experiences', methods=['GET'])
def list_pinned_experiences(tripId):
    """
    List all pinned experiences for a trip.

    Requires JWT authentication.
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    query = client.query(kind='PinnedExperience')
    query.add_filter('tripId', '=', tripId)
    pinned_experiences = list(query.fetch())
    return jsonify(pinned_experiences), 200

@app.route('/trips/<tripId>/experiences/<experienceId>', methods=['DELETE'])
def unpin_experience(tripId, experienceId):
    """
    Unpin an experience from a trip.
    Requires JWT authentication. Removes a pinned experience from a trip.
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    # Assuming each pin has a unique ID that combines tripId and experienceId for simplicity
    pin_key = client.key('PinnedExperience', f"{tripId}_{experienceId}")
    client.delete(pin_key)
    return jsonify({"message": "Experience unpinned successfully"}), 204

# ----------------------------------------------------------------------------- RATINGS

@app.route('/experiences/<experienceId>/ratings', methods=['POST'])
def rate_experience(experienceId):
    """
    Rate an experience, associated with a user and optionally a trip.

    Requires JWT authentication. The request must include JSON with the rating and optionally a tripId.
    """
    try:
        verify_jwt(request)
    except AuthError as e:
        return handle_auth_error(e)

    content = request.get_json()
    new_rating = datastore.Entity(client.key('Rating'))
    new_rating.update({
        'experienceId': experienceId,
        'userId': content['userId'],            # Assuming the user ID is sent in the request body
        'rating': content['rating'],
        'tripId': content.get('tripId', None)   # Optional?
    })
    client.put(new_rating)
    return jsonify(new_rating), 201

@app.route('/experiences/<experienceId>/ratings', methods=['GET'])
def get_ratings(experienceId):
    """
    Get all ratings for an experience, including an aggregate score.

    Returns a list of ratings and the average rating for the specified experience.
    """
    query = client.query(kind='Rating')
    query.add_filter('experienceId', '=', experienceId)
    ratings = list(query.fetch())

    if not ratings:
        return jsonify({"message": "No ratings found"}), 404

    avg_rating = sum([r['rating'] for r in ratings]) / len(ratings)
    return jsonify({"ratings": ratings, "average_rating": avg_rating}), 200

# ----------------------------------------------------------------------------- GOOGLE MAPS

@app.route('/map/search', methods=['GET'])
def search_maps():
    """
    Search for businesses via Google Maps API based on user query or map location.
    Accepts query parameters 'query' for search terms and 'location' for a specific latitude and longitude.
    """
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    api_key = env.get("GOOGLE_MAPS_API_KEY")

    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "key": api_key
    }

    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Failed to fetch data from Google Maps"}), response.status_code
    
@app.route('/map/details/<placeId>', methods=['GET'])
def get_place_details(placeId):
    """
    Get detailed information about a place from Google Maps.
    The 'placeId' URL parameter specifies the Google Place ID of the location to retrieve details for.
    """
    api_key = env.get("GOOGLE_MAPS_API_KEY")

    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": placeId,
        "key": api_key
    }

    response = requests.get(details_url, params=params)
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"error": "Failed to fetch place details from Google Maps"}), response.status_code

# -----------------------------------------------------------------------------

# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

