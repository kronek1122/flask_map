import os
import certifi
import ssl
from flask import Flask, jsonify, Response, request, render_template
import geopy.geocoders
from geopy.geocoders import Nominatim
from db_manager import DatabaseManager

app = Flask(__name__)

ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx
geolocator = Nominatim(user_agent="z2j_map")

def get_location_from_city(city):
    location = geolocator.geocode(city)
    return location.latitude, location.longitude

def postcode_to_city(zip: str):
    postcode = zip
    location = geolocator.geocode(postcode, addressdetails=True)

    city_name = None
    if location.raw["address"].get("city"):
        city_name = location.raw["address"]["city"]
    elif location.raw["address"].get("town"):
        city_name = location.raw["address"]["town"]
    elif location.raw["address"].get("village"):
        city_name = location.raw["address"]["village"]

    return city_name

@app.route('/')
def hello_world():
    return render_template('hello.html')

# POST endpoint
@app.route('/users', methods=['POST'])
def add_user():
    db = DatabaseManager(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'),
                         host=os.getenv('host'))
    request_data = request.get_json()
    username, zip, field = request_data["discord"], request_data["zip"], request_data["stack"]
    city_name = postcode_to_city(zip)
    latitude, longitude = get_location_from_city(city_name)[0], get_location_from_city(city_name)[1]
    result = Response(db.add_user(username, city_name, field, latitude, longitude), mimetype="application/json")
    db.close_connection() 
    return result, 201


# GET endpoint
@app.route('/users')
def get_users():
    db = DatabaseManager(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'),
                         host=os.getenv('host'))
    all_users = db.get_users()
    db.close_connection()
    return Response(all_users, mimetype='application/json'), 200

# PATCH endpoint
@app.route('/users', methods=['PATCH'])
def update_users():
    db = DatabaseManager(database=os.getenv('database'), user=os.getenv('user'), password=os.getenv('password'),
                         host=os.getenv('host'))
    data = request.get_json()
    discord = data['discord']
    updated_fields = []
    if not data:
        return {'error': 'No data provided for update'}, 400
    
    if 'discord' in data:
        updated_fields.append('discord')
        new_discord = data['discord']
        db.edit_user_name(discord, new_discord)

    if 'zip' in data:
        updated_fields.append('zip')
        zip = data['zip']
        city = postcode_to_city(zip)
        latitude, longitude = get_location_from_city(city)[0], get_location_from_city(city)[1]
        db.edit_user_city(discord, city, latitude, longitude)
        
    if 'stack' in data:
        updated_fields.append('stack')
        stack = data['stack']
        db.edit_user_stack(discord, stack)

    if len(updated_fields) > 0:
        response = jsonify({"message": f"Updated fields: {', '.join(updated_fields)}"}), 200
    else:
        response = jsonify({"error": "Invalid request."}), 400

    db.close_connection()
    return response

# DELETE endpoint


if __name__ == '__main__':
    app.run(debug=True)