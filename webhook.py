import os
import requests
from flask import Blueprint, request, jsonify

# Tạo Blueprint cho Messenger webhook
webhook_blueprint = Blueprint('webhook_blueprint', __name__)

# Lấy các biến môi trường
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

# Endpoint để xác thực Webhook
@webhook_blueprint.route('/messenger_webhook', methods=['GET'])
def verify_webhook():
    """
    Xác thực webhook khi đăng ký trên Facebook Developers.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print('Webhook VERIFIED!')
            return challenge, 200
        else:
            return 'Invalid token or mode', 403
    return 'Invalid request', 400

# Endpoint để xử lý tin nhắn đến
@webhook_blueprint.route('/messenger_webhook', methods=['POST'])
def handle_message():
    """
    Xử lý các tin nhắn đến từ Messenger.
    """
    data = request.get_json()
    print('Received data:', data)

    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                # Kiểm tra xem event có phải là tin nhắn không
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    
                    if message_text:
                        print(f'Received message from {sender_id}: {message_text}')
                        
                        # --- Cần thêm logic xử lý AI của bạn tại đây ---
                        # Ví dụ: response_from_ai = your_ai_function(message_text)
                        
                        # Gửi phản hồi đơn giản (cho mục đích demo)
                        send_simple_reply(sender_id, f"Bạn đã gửi: '{message_text}'")

    return 'OK', 200

def send_simple_reply(recipient_id, message_text):
    """
    Gửi tin nhắn phản hồi đến người dùng.
    """
    API_URL = 'https://graph.facebook.com/v19.0/me/messages'
    
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    r = requests.post(API_URL, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload, headers=headers)
    if r.status_code != requests.codes.ok:
        print('Error sending message:', r.text)
