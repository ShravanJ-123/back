from flask import Flask, render_template, request ,jsonify
import requests
import os
import json
from flask_cors import CORS  # Import CORS
from astrapy import DataAPIClient



app = Flask(__name__)
CORS(app)

# Account configuration for Langflow API
account_config = {
    "ranveer": {
        "BASE_API_URL": "https://api.langflow.astra.datastax.com",
        "LANGFLOW_ID": "50f59f86-16d5-46db-abe2-c0995d97f2b0",
        "FLOW_ID": "d8ebfc94-89df-4aff-b5e3-c47e42fe8eeb",
        "APPLICATION_TOKEN": "AstraCS:LFkXXAlxYxteywlZGjriswnT:e66f1c22e2c623019400a117f9609928ee41947b0bc5f84a65e30b4ce4580179",
    }
}

# API URLs and Key
API_URL_PLANET = "https://api.vedicastroapi.com/v3-json/horoscope/planet-report"
API_URL_GEM = "https://api.vedicastroapi.com/v3-json/extended-horoscope/gem-suggestion"
API_KEY = "fbf2e9d4-47fe-5bb9-a4ec-1a243ca55f44"

# Astra DB Connection
client = DataAPIClient("AstraCS:YHjGXrTelvIdwyLKdfQEikUg:0e3f97d040e889f40f693524220ddae0ed379dda640efc82ebe024627dc92585")
database = client.get_database("https://abaaa4b6-d3ac-4b2e-b373-4384569942fa-us-east-2.apps.astra.datastax.com")
collection = database.get_collection("data2")  # Using single collection

JSON_DIR = "/home/ranjeet/Desktop/AI"

@app.route("/name", methods=["GET"])
def get_user_name():
    # Assuming you are getting the name from a file, e.g., "John Doe.json"
    user_file = os.path.join(JSON_DIR, "User.json")  # Adjust filename as needed
    
    if os.path.exists(user_file):
        with open(user_file, "r") as file:
            user_data = json.load(file)
            return jsonify(user_data), 200
    else:
        return jsonify({"error": "User data not found"}), 404

@app.route("/planet/<planet_name>", methods=["GET"])  # Accept a dynamic planet name from the URL
def get_planet_data(planet_name):
    # Construct the path to the JSON file based on the planet name
    planet_file = os.path.join(JSON_DIR, f"{planet_name}_report.json")
    
    if os.path.exists(planet_file):
        with open(planet_file, "r") as file:
            planet_data = json.load(file)
            return jsonify(planet_data), 200
    else:
        return jsonify({"error": f"Data for {planet_name} not found"}), 404
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        name = data.get("name")
        dob = data.get("dob")
        tob = data.get("timeOfBirth")
        gender = data.get("gender")
        city =data.get("city")
        state = data.get("state")
        lat = 19
        lon = 72
        tz = 5  # Assume time zone is 5 for now
        planets = ["Sun", "Mars", "Jupiter", "Venus", "Saturn"]
        all_planet_data = {}
        
        user_data = {"name": name,"tob":tob,"dob":dob,"gender":gender,"city":city,"state":state}
    
        # Create a file to store user data with the name as the filename
        file_path = os.path.join(JSON_DIR, f"User.json")
        
        try:
            with open(file_path, "w") as file:
                json.dump(user_data, file)
            
        except Exception as e:
            jsonify({"error": f"Failed to save user data: {str(e)}"}), 500

        planet_report = None
        gem_report = None
        # Iterate over the list of planets to fetch and save their data
        for planet in planets:
            # Make request for Planet Report for each planet
            params = {
                "api_key": API_KEY,
                "dob": dob,
                "tob": tob,
                "lat": lat,
                "lon": lon,
                "tz": tz,
                "planet": planet,
                "lang": "en"
            }

            planet_response = requests.get(API_URL_PLANET, params=params)
            planet_data = planet_response.json()

            
            # Extract data from Planet API
            if planet_response.status_code == 200 and planet_data['status'] == 200:
                planet_report = planet_data['response'][0]
                all_planet_data[planet] = planet_data['response'][0]
            else:
                all_planet_data[planet] = {"error": "Unable to fetch data"}

            planet_file_path = os.path.join(JSON_DIR, f"{planet}_report.json")
            try:
                with open(planet_file_path, "w") as planet_file:
                    json.dump(all_planet_data[planet], planet_file, indent=4)
                print(f"{planet} report saved successfully.")
            except Exception as e:
                print(f"Failed to save {planet} report: {str(e)}")

            # Optional: Make request for Gem Suggestion (you can choose to store this as well)
            
            

        gem_params = {
            "api_key": API_KEY,
            "dob": dob,
            "tob": tob,
            "lat": lat,
            "lon": lon,
            "tz": tz,
            "lang": "en"
        }
        
        gem_response = requests.get(API_URL_GEM, params=gem_params)
        gem_data = gem_response.json()

        if gem_response.status_code == 200 and gem_data['status'] == 200:
            gem_report = gem_data['response']
            gem_file_path = os.path.join(JSON_DIR, "Gem_report.json")
            try:
                with open(gem_file_path, "w") as gem_file:
                    json.dump(gem_report, gem_file, indent=4)
                print("Gem report saved successfully.")
            except Exception as e:
                print(f"Failed to save gem report: {str(e)}")
        else:
            print("Unable to fetch gem report.")


        if planet_report and gem_report:
            data_to_insert = {
                "name": name,  # Storing user name
                "dob": dob,
                "tob": tob,
                "lat": lat,
                "lon": lon,
                "tz": tz,
                "planet_report": all_planet_data,
                "gem_report": gem_report
            }
            collection.insert_one(data_to_insert)

    return "Please make a POST request with the required data."

@app.route('/api/message', methods=['POST'])

def get_message():
    
    """Handle chat messages from the frontend."""
    data = request.get_json()
    print(data)
    name = data.get('name')
    message = data.get('message')
    account = "ranveer"  # Using a single account for now

    if not name or not message:
        return jsonify({"error": "Name and message are required"}), 400

    response = run_flow(name, message, account)
    return jsonify(response)

def run_flow(name, message, account):
    """Send the formatted message to the Langflow API."""
    config = account_config[account]
    api_url = f"{config['BASE_API_URL']}/lf/{config['LANGFLOW_ID']}/api/v1/run/{config['FLOW_ID']}"

    formatted_prompt = (
        f"You are an Astrology expert of {name}. "
        f"Your job is to analyze data of name: {name} and provide answers to the asked question. "
        f"User will ask you a question: {message}"
    )

    payload = {
        "input_value": formatted_prompt,
        "output_type": "chat",
        "input_type": "chat",
    }
    headers = {
        "Authorization": f"Bearer {config['APPLICATION_TOKEN']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Debugging: Print the whole response to understand its structure
        # print("API Response:", data)  # Uncomment for full response view

        # Extract only the 'text' field from the response
        text = "No response found."
        if isinstance(data, dict):
            outputs = data.get("outputs", [])
            if outputs:
                # Assuming outputs[0] -> outputs[0]['outputs'] -> message -> text
                message_data = outputs[0].get("outputs", [{}])[0].get("results", {}).get("message", {})
                text = message_data.get("text", "No text found in the message.")

        # Print only the extracted text
        print("Extracted Text:", text)  # This prints the desired text

    except requests.RequestException as e:
        text = f"Error: Unable to reach the server ({e})."
    except Exception as e:
        text = f"Error: {str(e)}"

    return {"response": text}

if __name__ == "__main__":
    app.run(debug=True)
