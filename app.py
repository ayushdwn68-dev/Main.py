from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Facebook Page Access Token (you'll get this from Facebook Developer Portal)
PAGE_ACCESS_TOKEN = 'YOUR_PAGE_ACCESS_TOKEN'

# Verify Token (you can set this to any string you want)
VERIFY_TOKEN = 'YOUR_VERIFY_TOKEN'

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    This endpoint is for verifying the webhook with Facebook
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("WEBHOOK VERIFIED")
            return challenge, 200
        else:
            return "Verification token mismatch", 403
    
    return "Missing parameters", 400

@app.route('/webhook', methods=['POST'])
def handle_messages():
    """
    This endpoint processes incoming messages
    """
    data = request.get_json()
    
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    # Extract details
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text', '')
                    
                    # Handle the message
                    handle_message(sender_id, message_text)
    
    return "OK", 200

def handle_message(sender_id, message_text):
    """
    Process the message and send a response
    """
    # Simple echo bot - you can customize this logic
    response_text = f"You said: {message_text}"
    
    # Send response back to Facebook
    send_message(sender_id, response_text)

def send_message(recipient_id, message_text):
    """
    Send message to user using Facebook Graph API
    """
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code} {response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)