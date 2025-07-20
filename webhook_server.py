import json
import os
import psycopg2 # Library to connect to the database
from flask import Flask, request

# =================================================================================
# --- 1. CONFIGURATION ---
# =================================================================================
app = Flask(__name__)

# This is a secret token that you create.
VERIFY_TOKEN = 'doofy-webhook-password-196300' # Make sure this still matches your Meta dashboard

# --- Database Connection Details ---
# These are loaded from Render's Environment Variables for security.
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT', 5432)

# =================================================================================
# --- 2. DATABASE FUNCTION ---
# This function handles saving the message to your Supabase database.
# =================================================================================
def save_message_to_db(sender_id, message_text):
    """Connects to the database and inserts a new message."""
    conn = None
    try:
        # --- UPDATED CONNECTION LOGIC ---
        # We now add the required 'pool_mode' as an option in the database name string.
        conn_string = (
            f"host={DB_HOST} "
            f"dbname={DB_NAME} "
            f"user={DB_USER} "
            f"password={DB_PASSWORD} "
            f"port={DB_PORT} "
            f"options='-c pool_mode=transaction'" # <-- THIS IS THE FIX
        )
        
        # Establish a connection to the database using the full connection string
        conn = psycopg2.connect(conn_string)
        
        # Create a cursor object
        cur = conn.cursor()
        
        # SQL query to insert data into the 'messages' table
        sql_query = "INSERT INTO messages (sender_id, message_text) VALUES (%s, %s);"
        
        # Execute the query
        cur.execute(sql_query, (sender_id, message_text))
        
        # Commit the transaction
        conn.commit()
        
        print(f"✔ Successfully saved message from {sender_id} to the database.")
        
        # Close the cursor
        cur.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        if conn is not None:
            # Close the connection
            conn.close()

# =================================================================================
# --- 3. WEBHOOK ENDPOINTS ---
# =================================================================================

@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Handles the webhook verification request from Meta."""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("✔ Webhook verified successfully!")
            return challenge, 200
        else:
            print("❌ Webhook verification failed: Mismatched tokens.")
            return 'Forbidden', 403
    
    print("❌ Webhook verification failed: Missing parameters.")
    return 'Bad Request', 400

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handles incoming messages and saves them to the database."""
    data = request.get_json()
    print("\n--- Received Webhook Data ---")
    print(json.dumps(data, indent=2))

    if data.get('object') == 'whatsapp_business_account':
        try:
            for entry in data['entry']:
                for change in entry['changes']:
                    if 'messages' in change['value']:
                        message = change['value']['messages'][0]
                        sender_id = message['from']
                        message_text = message['text']['body']
                        
                        print(f"✅ New message from {sender_id}: '{message_text}'")
                        
                        # --- Call the function to save the message ---
                        save_message_to_db(sender_id, message_text)
                        
        except (IndexError, KeyError) as e:
            print(f"⚠️ Could not parse message data: {e}")
            pass

    return 'OK', 200

# =================================================================================
# --- 4. RUN THE APPLICATION ---
# =================================================================================

if __name__ == '__main__':
    app.run(port=5000, debug=True)
