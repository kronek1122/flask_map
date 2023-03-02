import os
from flask import Flask, jsonify, Response, request, render_template
from utility_functions.geolocation import postcode_to_city, get_location_from_city
from db_manager import DatabaseManager

app = Flask(__name__)


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