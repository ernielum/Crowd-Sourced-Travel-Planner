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
#import constants

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

@app.route('/users', methods=['GET'])
def get_users():
    query = client.query(kind='User')
    results = list(query.fetch())
    users = [{'user_id': user['user_id']} for user in results]
    return jsonify(users), 200

# ----------------------------------------------------------------------------- EXPERIENCES

@app.route('/experiences')
def experiences():
    #user_id = session.get('profile')['sub']  #Temporarily commented out for FE dev
    jwt_token = session.get('jwt')  
    return render_template('experiences.html', jwt=jwt_token)

# ----------------------------------------------------------------------------- TRIPS

@app.route('/trips', methods=['GET','POST'])
def trips():
    # TODO: Replace dummy test data with endpoint code and logic.

    # Dummy test data for Front-End testing
    user_trips = [
        "Paris",
        "Glacier National Park",
        "Rome",
        "Swiss Alps",
        "Bora Bora",
        "Maui",
        "London, England",
    ]
    #user_id = session.get('profile')['sub']  #Temporarily commented out for FE dev
    jwt_token = session.get('jwt')  
    return render_template('trips.html', jwt=jwt_token, trips=user_trips)

# -----------------------------------------------------------------------------

# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

