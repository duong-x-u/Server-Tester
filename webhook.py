import os
import requests
import json
import asyncio
from flask import Blueprint, request, jsonify
from api.analyze import perform_full_analysis

# Tạo Blueprint cho Messenger webhook
webhook_blueprint = Blueprint('webhook_blueprint', __name__)

# Lấy các biến môi trường
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

print(f"VERIFY_TOKEN loaded: {VERIFY_TOKEN}")
print(f"PAGE_ACCESS_TOKEN loaded: {PAGE_ACCESS_TOKEN}")

# Endpoint để xác thực Webhook (GIỮ NGUYÊN)
@webhook_blueprint.route('/messenger_webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Invalid token or mode', 403
    return 'Invalid request', 400

# Endpoint để xử lý tin nhắn đến (ĐÃ CHỈNH SỬA)
@webhook_blueprint.route('/messenger_webhook', methods=['POST'])
def handle_message():
    print("Received POST request from webhook.")
    try:
        data = request.get_json(force=True)
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event.get('message', {}).get('text')

                        if message_text:
                            print(f'Received message: "{message_text}" from PSID: {sender_id}')
                            
                            print("➡️  Bắt đầu phân tích tin nhắn với CyberShield AI...")
                            analysis_result = asyncio.run(perform_full_analysis(message_text, []))
                            print(f"✅ Kết quả phân tích: {json.dumps(analysis_result, ensure_ascii=False)}")

                            # <<< PHẦN LOGIC TRẢ LỜI CHO CẢ 2 TRƯỜNG HỢP >>>
                            if analysis_result and analysis_result.get('is_dangerous'):
                                # Trường hợp 1: Tin nhắn NGUY HIỂM
                                reason = analysis_result.get('reason', 'Lý do không xác định.')
                                recommend = analysis_result.get('recommend', 'Hãy cẩn thận.')
                                score = analysis_result.get('score', 'N/A')
                                
                                reply_message = (
                                    f"⚠️ [CyberShield] CẢNH BÁO NGUY HIỂM ⚠️\n\n"
                                    f"Điểm nguy hiểm: {score}/5\n"
                                    f"Phân tích: {reason}\n"
                                    f"Gợi ý: {recommend}"
                                )
                                send_message(sender_id, reply_message)
                            else:
                                # Trường hợp 2: Tin nhắn AN TOÀN
                                reply_message = "✅ [CyberShield] Tin nhắn này an toàn."
                                send_message(sender_id, reply_message)
                            # <<< KẾT THÚC LOGIC TRẢ LỜI >>>
                        
    except Exception as e:
        print(f"An error occurred during webhook processing: {e}")
        return 'Internal Server Error', 500
    return 'OK', 200

def send_message(recipient_id, message_text):
    API_URL = 'https://graph.facebook.com/v23.0/me/messages'
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.post(API_URL, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload, headers=headers)
        if r.status_code != 200:
            print(f'Error sending message: {r.status_code} {r.text}')
        else:
            print(f'Message sent successfully to {recipient_id}!')
    except Exception as e:
        print(f"An error occurred while sending message: {e}")
