from flask import Flask, render_template
import boto3
import requests
import datetime
import os
import time

CLIENT_ID = os.environ.get("CLIENT_ID")  # Your Client Id
USERNAME = os.environ.get("USERNAME")  # Your Username
PASSWORD = os.environ.get("PASSWORD")  # Your Password

app = Flask(__name__)


def ircc_tracker(username, password, app_client_id):
    client = boto3.client("cognito-idp", region_name="ca-central-1")

    resp = client.initiate_auth(
        ClientId=app_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
    )

    print("Log in successfully - Getting data")

    headers = {
        "authorization": "Bearer " + resp["AuthenticationResult"]["IdToken"],
    }

    raw_data = '{"method":"get-profile-summary"}'

    response = requests.post(
        "https://api.ircc-tracker-suivi.apps.cic.gc.ca/user",
        data=raw_data,
        headers=headers,
    )
    jsonResponse = response.json()

    tasks = jsonResponse["apps"][0]["tasks"]
    status = jsonResponse["apps"][0]["status"]
    application_number = jsonResponse["apps"][0]["appNum"]

    raw_data = f'{{"method":"get-application-details","applicationNumber":"{application_number}","uci":"{USERNAME}","isAgent":false}}'

    response = requests.post(
        "https://api.ircc-tracker-suivi.apps.cic.gc.ca/user",
        data=raw_data,
        headers=headers,
    )
    jsonResponse = response.json()

    last_updated = jsonResponse["app"]["lastUpdated"]
    timestamp = last_updated

    # Convert timestamp to datetime object
    dt_object = datetime.datetime.fromisoformat(timestamp[:-1])

    # Convert datetime object to a formatted date string
    formatted_Ldate = dt_object.strftime("%Y-%m-%d %H:%M:%S")

    return {"last_updated": formatted_Ldate, "tasks": tasks, "status": status}


def run_script():
    data = ircc_tracker(USERNAME, PASSWORD, CLIENT_ID)
    return data


@app.route("/")
def index():
    data = ircc_tracker(USERNAME, PASSWORD, CLIENT_ID)
    button_click_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["button_click_time"] = button_click_time
    return render_template("index.html", data=data)


@app.route("/run-script", methods=["POST"])
def run_script_route():
    button_click_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Re-run the entire script when the button is clicked
    data = run_script()
    # Add button click time to the data
    data["button_click_time"] = button_click_time
    return render_template("index.html", data=data)


if __name__ == "__main__":
    app.run(debug=False, host="localhost", port=int(os.environ.get("PORT", 8080)))
