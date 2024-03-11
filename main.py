# Standard library imports
from functools import wraps
import json
from os import environ as env
from urllib.request import urlopen
from urllib.parse import quote_plus, urlencode

# Third-party imports
from dotenv import find_dotenv, load_dotenv
from flask import Flask, request, jsonify, redirect, render_template, session, url_for, _request_ctx_stack
from flask_cors import cross_origin
from jose import jwt
from werkzeug.exceptions import HTTPException
from authlib.integrations.flask_client import OAuth
from google.cloud import datastore
import requests

# ------------------------------------------------------------------------------------------------------------------
# FE Test Data
# TODO: Remove dummy test data and imports
from dummy_test_data import dummy_test_user_trips, dummy_test_trip_data, dummy_test_experiences_data, dummy_user_info
import os
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


# ------------------------------------------------------------------------------------------------------------------


# Local application imports
# import constants

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
maps_key = env.get("GOOGLE_MAPS_KEY")

client = datastore.Client()

ALGORITHMS = ["RS256"]

# ------------------------------------------------------------------------------------------------------------------
# FE Test Data
# TODO: Remove dummy test data and imports
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Reference: https://tutorial101.blogspot.com/2021/04/python-flask-upload-and-display-image.html
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------------------------------------------------------------------------------------------------------

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

    return redirect('/trips')

@app.route('/user-info')
def user_info():
    #user_id = session.get('profile')['sub']  #Temporarily commented out for FE dev
    jwt_token = session.get('jwt')  
    #return render_template('userinfo.html', jwt=jwt_token, user_id=user_id, user_info=session.get('profile')) #Temporarily commented out for FE dev
    return render_template('userinfo.html', jwt=jwt_token, user_info=session.get('profile'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ----------------------------------------------------------------------------- USERS

@app.route('/users', methods=['GET'])
def get_users():
    query = client.query(kind='User')
    results = list(query.fetch())
    users = [{'user_id': user['user_id']} for user in results]
    return jsonify(users), 200

# ----------------------------------------------------------------------------- EXPERIENCES

@app.route('/experiences', methods=['GET', 'POST'])
def experiences():
    # TODO: Replace dummy FE test stuff with endpoint code and logic.
    experiences = dummy_test_experiences_data

    user_info = dummy_user_info


    #user_id = session.get('profile')['sub']  #Temporarily commented out for FE dev
    jwt_token = session.get('jwt')  
    return render_template('experiences.html', jwt=jwt_token, experiences=experiences, user_info=user_info)

@app.route('/experience_view', methods=['GET', 'POST'])
def experience_view():
    # TODO: Replace dummy FE test stuff with endpoint code and logic.
    user_info = dummy_user_info

    if request.method == 'POST':
        # check the name of the submit input: pin-experience or rate-experience
        if 'pin-experience' in request.form:
            print("Pinned experience")
        elif 'rate-experience' in request.form:
            print("Rated experience")

        experienceId = request.form.get('experienceId')
        userId = request.form.get('userId')
        tripId = request.form.get('tripId')
        userRating = request.form.get('userRating')
        print("experienceId: ", experienceId)
        print("tripId: ", tripId)
        print("userId: ", userId)
        print("userRating: ", userRating)

        # experience_data = dummy_test_experiences_data[int(experienceId)-1]

        # user_trips = dummy_test_user_trips


    jwt_token = session.get('jwt')  
    return render_template('experience_view.html', jwt=jwt_token, experience=experience_data, trips=user_trips, user_info=user_info)

@app.route('/experience_create', methods=['GET', 'POST'])
def experience_create():

    # TODO: Replace dummy FE test stuff with endpoint code and logic.
    if request.method == 'POST':
        experienceName = request.form.get('name')
        experienceDescription = request.form.get('description')
        experienceLocation = request.form.get('location')
        experienceRating = request.form.get('rating')
        
        print("experienceName: ", experienceName)
        print("experienceDescription: ", experienceDescription)
        print("experienceLocation: ", experienceLocation)
        print("experienceRating: ", experienceRating)
        
        # Handle image file form input
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("File uploaded successfully")


    #user_id = session.get('profile')['sub']  #Temporarily commented out for FE dev
    jwt_token = session.get('jwt')  
    return render_template('experience_create.html', jwt=jwt_token)

@app.route('/experience_unpin', methods=['DELETE', 'POST'])
def experience_unpin():
  
    # Get current tripId
    tripId = request.form.get('tripId')
    trip_key = client.key('Trip', int(tripId))
    trip = client.get(trip_key)

    # Get current experienceId
    experienceId = request.form.get('experienceId')
    experience_key = client.key('Experience', int(experienceId))

    experiences = trip.get('experiences')
    experiences.remove(experience_key)
    trip['experiences'] = experiences
    client.put(trip)

    return redirect(url_for('trip_view', tripId=tripId))


@app.route('/experience_pin', methods=['POST'])
def experience_pin():
    result = request.json

    # Get current tripId
    tripId = result['tripId']
    trip_key = client.key('Trip', int(tripId))
    trip = client.get(trip_key)

    # Get experience details
    experience = result['experience'][0]

    # Check if there is already an entity for this experience
    query = client.query(kind='Experience')
    query.add_filter('place_id', '=', experience['place_id']) # place_id is uniquely provided by Place API
    query_result = list(query.fetch())

    # If experience is not registered, create new Experience entity
    if query_result:
        # Experience entity already exists, use the first result
        experience_entity = query_result[0]
    else:
        # Create new Experience entity
        new_experience = datastore.Entity(client.key('Experience'))
        new_experience.update({
            'name': experience['name'],
            'address': experience['formatted_address'],
            'place_id': experience['place_id']
        })
        client.put(new_experience)
        experience_entity = new_experience

    # Add entity to list of experiences for the trip
    experiences = trip.get('experiences')
    experiences.append(experience_entity.key)
    trip['experiences'] = experiences
    client.put(trip)

    return redirect(url_for('trip_view', tripId=tripId))


@app.route('/rate_experience', methods=['GET', 'POST'])
def rate_experience():

    user_id = session.get('profile')['sub']
    jwt_token = session.get('jwt')  

    # Retrieve Rating Form details
    if request.method == 'POST':
        experienceId = request.form.get('experienceId')
        tripId = request.form.get('tripId')
        userRating = request.form.get('userRating')
        #userRatingValue = request.form.get('userRatingValue')
        print("experienceId:", experienceId)
        print("tripId:", tripId)
        print("userRating:", userRating)
        #print("userRatingValue:", userRatingValue)

        #----------------------------------
        # Rating Entity
        #
        #----------------------------------

        # Check if there is already a Rating entity for this user-experience rating
        query = client.query(kind='Rating')
        query.add_filter('user_id', '=', user_id)
        query.add_filter('experienceId', '=', experienceId)

        results = list(query.fetch())

        # If user rating is not in db, create a new Rating entity
        if not results: 
            user_rating = datastore.Entity(client.key('Rating'))
            user_rating.update({
                'experienceId': experienceId,
                'user_id': user_id,
                'rating': userRating,
            })
        # If user rating already exists, update it
        else:
            user_rating = results[0]
            user_rating.update({
                'rating': userRating,
            })

        client.put(user_rating)

        #----------------------------------
        # Calculate Average Rating of Experience
        #
        #----------------------------------
        query = client.query(kind='Rating')
        query.add_filter('experienceId', '=', experienceId)
        ratings = list(query.fetch())

        if not ratings:
            return jsonify({"message": "No ratings found"}), 404
        avg_rating = sum([int(r['rating']) for r in ratings]) / len(ratings)
        avg_rating = round(avg_rating, 1)

        #----------------------------------
        # Update Experience Entity
        #
        #----------------------------------
        experience_key = client.key('Experience', int(experienceId))
        experience = client.get(key=experience_key)
        if not experience:
            return jsonify({"error": "Experience not found"}), 404
        experience.update({
            'avg_rating': avg_rating,
        })
        client.put(experience)

    return redirect(url_for('trip_view', tripId=tripId))

# ----------------------------------------------------------------------------- TRIPS

@app.route('/trips', methods=['GET','POST'])
def trips():

    user_id = session.get('profile')['sub']
    jwt_token = session.get('jwt')  

    # Retrieve trip list for current user
    if request.method == 'GET':
        query = client.query(kind='Trip')
        query.add_filter('user_id', '=', user_id)
        user_trips = list(query.fetch())

    # Add new trip to list for current user
    if request.method == 'POST':

        # Create new trip
        new_trip_name = request.form['new_trip']
        new_trip = datastore.Entity(client.key('Trip'))
        new_trip.update({
            'user_id': user_id,
            'name': new_trip_name,
            'experiences': []
        })
        client.put(new_trip)

        # Re-query trip list
        query = client.query(kind='Trip')
        query.add_filter('user_id', '=', user_id)
        user_trips = list(query.fetch())

    return render_template('trips.html', jwt=jwt_token, trips=user_trips)

#@app.route('/trip_experiences/<tripId>', methods=['GET'])
@app.route('/trip_view', methods=['GET', 'POST'])
def trip_view():

    # Retrieve details of a specific trip.
    user_info = session.get('profile')['sub']

    if request.method == 'GET':
        tripId = request.args.get('tripId')
        trip_key = client.key('Trip', int(tripId))
        trip = client.get(trip_key)

        experiences = []

        for experience_key in trip['experiences']:
            experience = client.get(experience_key)
            experiences.append(experience)

        #----------------------------------
        # Get My Ratings
        #
        #----------------------------------
        my_ratings = []
        # Check if there is a Rating entity for this user-experience rating
        for experience in trip['experiences']:
            query = client.query(kind='Rating')
            query.add_filter('user_id', '=', user_info)
            query.add_filter('experienceId', '=', str(experience.id))
            
            results = list(query.fetch())

            if results:
                my_ratings.append(results[0])

        experience_and_rating_data = []

        for experience in experiences:
            experience_data = {'experience': experience, 'my_rating': ""}
            for rating in my_ratings:
                if rating['experienceId'] == str(experience.id):
                    experience_data['my_rating'] = rating['rating']

            experience_and_rating_data.append(experience_data)

    jwt_token = session.get('jwt')  
    # return render_template('trip_view.html', jwt=jwt_token, trip=trip, experiences=experiences, API_KEY=maps_key, user_info=user_info)
    return render_template('trip_view.html', jwt=jwt_token, trip=trip, experiences=experience_and_rating_data, API_KEY=maps_key, user_info=user_info)

@app.route('/trip_edit', methods=['GET', 'POST'])
def trip_edit():
    # TODO: Replace dummy FE test stuff with endpoint code and logic.
    user_info = dummy_user_info

    if request.method == 'GET':
        tripId = request.args.get('tripId')

        trip_data = dummy_test_trip_data.get("trip"+tripId)


    jwt_token = session.get('jwt')  
    return render_template('trip_edit.html', jwt=jwt_token, trip=trip_data, user_info=user_info)

@app.route('/trip_delete', methods=['GET', 'POST'])
def trip_delete():

    user_id = session.get('profile')['sub']
    jwt_token = session.get('jwt') 

    if request.method == 'POST':
        tripId = request.form['delete-trip']
        trip_key = client.key('Trip', int(tripId))
        client.delete(trip_key)

        # Re-query trip list
        query = client.query(kind='Trip')
        query.add_filter('user_id', '=', user_id)
        user_trips = list(query.fetch())

    # Return to trip list

    return render_template('trips.html', jwt=jwt_token, trips=user_trips)

# -----------------------------------------------------------------------------

# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

