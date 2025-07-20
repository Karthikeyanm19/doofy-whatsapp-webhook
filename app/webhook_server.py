import json
from flask import Flask, request

# =================================================================================
# --- 1. CONFIGURATION ---
# =================================================================================
# Initialize the Flask application
app = Flask(__name__)

# This is a secret token that you create.
# It should match the one you enter in the Meta App dashboard.
VERIFY_TOKEN = 'YOUR_SECRET_VERIFY_TOKEN' # Change this to a random secret string


# =================================================================================
# --- 2. WEBHOOK ENDPOINTS ---
# This is where the app receives requests from Meta.
# =================================================================================

# --- Endpoint for Webhook Verification ---
# Meta sends a GET request to this endpoint to verify your webhook's authenticity.
@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """
    Handles the webhook verification request from Meta.
    """
    # Parse the query parameters from the request
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            # Respond with 200 OK and the challenge token from the request
            print("✔ Webhook verified successfully!")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            print("❌ Webhook verification failed: Mismatched tokens.")
            return 'Forbidden', 403
    
    print("❌ Webhook verification failed: Missing parameters.")
    return 'Bad Request', 400


# --- Endpoint for Receiving Messages ---
# Meta sends a POST request with message data to this endpoint.
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Handles incoming messages and notifications from WhatsApp.
    """
    # Get the JSON data from the request
    data = request.get_json()
    print("\n--- Received Webhook Data ---")
    print(json.dumps(data, indent=2)) # Pretty-print the data for easy reading

    # Check if the notification is a message
    if data.get('object') == 'whatsapp_business_account':
        try:
            for entry in data['entry']:
                for change in entry['changes']:
                    # Check if the change contains a 'messages' field
                    if 'messages' in change['value']:
                        message = change['value']['messages'][0]
                        sender_id = message['from']
                        message_text = message['text']['body']
                        
                        print(f"✅ New message from {sender_id}: '{message_text}'")
                        
                        #
                        # --- YOUR BUSINESS LOGIC GOES HERE ---
                        # For example, you could save the message to a database,
                        # send an automated reply, or forward it to a support agent.
                        #
                        
        except (IndexError, KeyError) as e:
            # This handles cases where the message structure is not what we expect
            print(f"⚠️ Could not parse message data: {e}")
            pass

    # Return a '200 OK' response to let Meta know you've received the notification
    return 'OK', 200


# =================================================================================
# --- 3. RUN THE APPLICATION ---
# =================================================================================

if __name__ == '__main__':
    # When running locally, Flask's development server is used.
    # When deploying to a service like Render, a production server like Gunicorn will run this.
    app.run(port=5000, debug=True)
