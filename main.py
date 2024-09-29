import requests
from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb+srv://rinputin482:Rinputin482qh@cluster0.5n8iybx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["raiden"]
const_collection = db["const"]

def get_refresh_token_from_db():
    refresh_token_doc = const_collection.find_one({"name": "refresh_code"})
    if refresh_token_doc:
        refresh_token = refresh_token_doc.get("value")
        print(f"Refresh token retrieved from MongoDB: {refresh_token}")
        return refresh_token
    else:
        print("No refresh token found in MongoDB")
        return None

def update_tokens_in_db(access_token, refresh_token, expires_in):
    const_collection.update_one(
        {"name": "auth_code"}, 
        {"$set": {"value": access_token, "expires_in": expires_in}},
        upsert=True
    )
    const_collection.update_one(
        {"name": "refresh_code"},
        {"$set": {"value": refresh_token}},
        upsert=True
    )
    print(f"Tokens updated in MongoDB: access_token = {access_token}, refresh_token = {refresh_token}, expires_in = {expires_in} seconds")

def call_get_access_token():
    refresh_token = get_refresh_token_from_db()  
    if not refresh_token:
        print("Refresh token is missing, cannot call get_access_token API")
        return False

    try:
        auth_refresh = {
            'Secret_key': '14p63uLCY20Os68NFWIU'
        }
        body_refresh = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "app_id": '1888287946753069132'
        }
        
        response = requests.post("https://oauth.zaloapp.com/v4/oa/access_token", data=body_refresh, headers=auth_refresh)
        print(response.json(), response.text)

        if response.json().get('access_token'):
            data = response.json()
            access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token", refresh_token)  
            expires_in = int(data.get("expires_in"))

            print(f"Access token received: {access_token}, expires in: {expires_in} seconds")
            
            update_tokens_in_db(access_token, new_refresh_token, expires_in)
            return True
        else:
            print(f"Failed to get access token, status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"Error calling get_access_token: {e}")
        return False

@app.route("/start-token-process")
def start_token_process():
    if call_get_access_token():
        return jsonify({"message": "Access token obtained and updated!"})
    else:
        return jsonify({"message": "Failed to obtain access token!"}), 500

if __name__ == "__main__":
    app.run(debug=True)
