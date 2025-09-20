import os
import requests
import json
from flask import Blueprint, request, jsonify

# Tạo Blueprint cho Messenger webhook
webhook_blueprint = Blueprint('webhook_blueprint', __name__)

# Lấy các biến môi trường
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

print(f"VERIFY_TOKEN loaded: {VERIFY_TOKEN}")
print(f"PAGE_ACCESS_TOKEN loaded: {PAGE_ACCESS_TOKEN}")

# Endpoint để xác thực Webhook
@webhook_blueprint.route('/messenger_webhook', methods=['GET'])
def verify_webhook():
    print("Received GET request for webhook verification.")
    
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print(f"hub.mode: {mode}")
    print(f"hub.verify_token: {token}")
    print(f"hub.challenge: {challenge}")

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print('Webhook VERIFIED! Responding with challenge.')
            return challenge, 200
        else:
            print('VERIFICATION FAILED: Invalid token or mode.')
            return 'Invalid token or mode', 403
    print('VERIFICATION FAILED: Missing parameters.')
    return 'Invalid request', 400

# Endpoint để xử lý tin nhắn đến
@webhook_blueprint.route('/messenger_webhook', methods=['POST'])
def handle_message():
    print("Received POST request from webhook.")
    
    try:
        data = request.get_json(force=True)
        print('Raw data received:')
        print(json.dumps(data, indent=2))
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                print("Processing entry...")
                for messaging_event in entry.get('messaging', []):
                    print("Processing messaging event.")
                    
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message = messaging_event['message']
                        message_text = message.get('text')
                        
                        print(f"Message event detected from sender_id: {sender_id}")
                        print(f"Message content: {message}")

                        if message_text:
                            print(f'Received message text: "{message_text}" from PSID: {sender_id}')
                            
                            # Gửi phản hồi đơn giản (cho mục đích demo)
                            send_simple_reply(sender_id, f"Bạn đã gửi: '{message_text}'")
                            print("Sent simple reply.")
                        else:
                            print("Received a message without text content (e.g., sticker, attachment).")
                    elif messaging_event.get('postback'):
                        sender_id = messaging_event['sender']['id']
                        postback = messaging_event['postback']
                        print(f"Postback event detected from sender_id: {sender_id}")
                        print(f"Postback content: {postback}")
                    
    except Exception as e:
        print(f"An error occurred during webhook processing: {e}")
        return 'Internal Server Error', 500

    return 'OK', 200

def send_simple_reply(recipient_id, message_text):
    """
    Gửi tin nhắn phản hồi đến người dùng.
    """
    API_URL = 'https://graph.facebook.com/v23.0/me/messages'
    
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    print(f"Preparing to send reply to {recipient_id} with message: '{message_text}'")

    try:
        r = requests.post(API_URL, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload, headers=headers)
        print(f"API request sent. Status code: {r.status_code}")
        if r.status_code != requests.codes.ok:
            print('Error sending message:', r.text)
        else:
            print('Message sent successfully!')
    except Exception as e:
        print(f"An error occurred while sending message: {e}")
