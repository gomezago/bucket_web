import json
import requests
import os
import environ
from django.shortcuts import render, redirect
from authlib.integrations.django_client import OAuth

env = environ.Env()
environ.Env.read_env()


OAUTH2_REDIRECT_URL='http://localhost:8000/bucket/auth'
CREATE_THING_URL = "https://dwd.tudelft.nl/bucket/api/things/"


oauth = OAuth()
#Register remote application on OAuth registry
oauth.register(
    name='bucket',

    access_token_url=env('OAUTH2_TOKEN_URL'),
    access_token_params=None,

    authorize_url=env('OAUTH2_AUTH_URL'),
    authorize_params=None,

    userinfo_endpoint=env('OAUTH2_PROFILE_URL'),

    client_kwargs={
        'scope':env('BUCKET_SCOPE'),
    },
    kwargs={
        'token_endpoint_auth_methods_supported': None,
        'grant_types_supported': ["refresh_token", "authorization_code"],
        'response_types_supported': ["id_token", "token", "code"],
        'introspection_endpoint' : env('OAUTH2_INTROSPECT_URL'),
        'revocation_endpoint' : env('OAUTH2_REVOKE_URL'),
        'authorization_endpoint' : env('OAUTH2_AUTH_URL'),
    }
)

def home(request):
    user = request.session.get('user')
    if user:
        user = json.dumps(user)
    return render(request, 'bucket_login.html', context={'user': user})

def bucket_login(request):
    bucket = oauth.create_client('bucket')
    redirect_uri = OAUTH2_REDIRECT_URL
    return bucket.authorize_redirect(request, redirect_uri)

def auth(request):
    token = oauth.bucket.authorize_access_token(request)

    resp = oauth.bucket.get(env('OAUTH2_PROFILE_URL'), token=token)
    resp.raise_for_status()
    profile = resp.json()

    request.session['token'] = token
    request.session['user'] = profile

    return redirect('/bucket/')

def create_thing(request):
    token = request.session['token']

    # Create a new thing
    my_thing = {
        "name": "My Thing from Django",
        "description": "Description of my Thing from Django",
        "type": "Test Thing",
        "pem": None,
    }

    hed = {'Authorization': 'bearer ' + token['access_token']}
    response = requests.post(CREATE_THING_URL, json=my_thing, headers=hed)
    if response.ok:
        my_thing_id = response.json()["id"]
        request.session["thing_id"] = my_thing_id
    else:
        response.raise_for_status()
    return render(request, 'bucket_login.html', context={'user': request.session['user'], 'thing_id': response.json()["id"]})

def create_property(request):
    token = request.session['token']
    thingId = request.session['thing_id']

    CREATE_PROPERTY_URL = f'https://dwd.tudelft.nl/bucket/api/things/{thingId}/properties'

    my_property = {
        "name": "My Property from Django",
        "description": "Description of my Property from Django",
        "type": "ACCELEROMETER",
        "typeId": None,
    }

    hed = {'Authorization': 'bearer ' + token['access_token']}
    par = {'thingId': thingId}
    response = requests.post(CREATE_PROPERTY_URL, json=my_property, headers=hed, params=par)
    if response.ok:
        my_property_id = response.json()["id"]
        request.session["property_id"] = my_property_id
    else:
        response.raise_for_status()

    return render(request, 'bucket_login.html', context={'user': request.session['user'],
                                                            'thing_id': thingId,
                                                            'property_id': response.json()["id"]})


def update_property(request):
    token = request.session['token']
    thingId = request.session['thing_id']
    propertyId = request.session['property_id']

    UPDATE_PROPERTY_URL = f'https://dwd.tudelft.nl/bucket/api/things/{thingId}/properties/{propertyId}'

    hed = {'Authorization': 'bearer ' + token['access_token']}
    par = {'thingId' : thingId, 'propertyId': propertyId}

    values = {
        "name": "My Property from Django",
        "description": "Description of my Property from Django",
        "type": "ACCELEROMETER",
        "typeId": None,
        "values": [[1626343350000, 0, 1, 2], # Timestamp in ms, x, y, z
                   [1626343350200, 3, 4, 5],
                   [1626343350400, 6, 7, 8],
                   [1626343350600, 9, 0, 1]],
    }

    response = requests.put(UPDATE_PROPERTY_URL, json=values, headers=hed, params=par)
    if response.status_code == 200:
        update = True
    else:
        update = False
        response.raise_for_status()

    return render(request, 'bucket_login.html', context={'user': request.session['user'],
                                                            'thing_id': thingId,
                                                            'property_id': propertyId,
                                                            'update' : update})

def read_property(request):
    token = request.session['token']
    thingId = request.session['thing_id']
    propertyId = request.session['property_id']
    update = request.session['update']

    UPDATE_PROPERTY_URL = f'https://dwd.tudelft.nl/bucket/api/things/{thingId}/properties/{propertyId}'

    hed = {'Authorization': 'bearer ' + token['access_token']}
    par = {'thingId': thingId, 'propertyId': propertyId, 'from' : 1626343350000, 'to': 1626343350600} # Start and End Timestamps
    response = requests.get(UPDATE_PROPERTY_URL, headers=hed, params=par)
    if response.ok:
        my_property_values = response.json()["values"]
    else:
        response.raise_for_status()
        my_property_values = None

    return render(request, 'bucket_login.html', context={'user': request.session['user'],
                                                          'thing_id': thingId,
                                                          'property_id': propertyId,
                                                          'values': my_property_values,
                                                          'update' : update,})

def bucket_logout(request):
    request.session.pop('token', None)
    request.session.pop('thingId', None)
    request.session.pop('propertyId', None)
    request.session.pop('user', None)
    return redirect('/bucket/')