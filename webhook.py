import os
import requests
import json
import asyncio  # <<< THÊM: Cần thiết để chạy hàm async
from flask import Blueprint, request, jsonify
from api.analyze import perform_full_analysis  # <<< THÊM: Import bộ não AI

# Tạo Blueprint cho Messenger webhook
webhook_blueprint = Blueprint('webhook_blueprint', __name__)

# Lấy các biến môi trường
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

print(f"VERIFY_TOKEN loaded: {VERIFY_TOKEN}")
print(f"PAGE_ACCESS_TOKEN loaded: {PAGE_ACCESS_TOKEN}")

# Endpoint để xác thực Webhook (GIỮ NGUYÊN, KHÔNG THAY ĐỔI)
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

# Endpoint để xử lý tin nhắn đến (ĐÃ NÂNG CẤP)
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
                        message = messaging_event['message']
                        message_text = message.get('text')
                        
                        if message_text:
                            print(f'Received message text: "{message_text}" from PSID: {sender_id}')
                            
                            # <<< BẮT ĐẦU TÍCH HỢP AI >>>
                            print("➡️  Bắt đầu phân tích tin nhắn với CyberShield AI...")
                            
                            # Chạy hàm async `perform_full_analysis` từ context đồng bộ của Flask
                            analysis_result = asyncio.run(perform_full_analysis(message_text, []))
                            print(f"✅ Kết quả phân tích: {json.dumps(analysis_result, ensure_ascii=False)}")

                            # Chỉ phản hồi nếu kết quả phân tích là nguy hiểm
                            if analysis_result and analysis_result.get('is_dangerous'):
                                reason = analysis_result.get('reason', 'Lý do không xác định.')
                                recommend = analysis_result.get('recommend', 'Hãy cẩn thận với tin nhắn này.')
                                score = analysis_result.get('score', 'N/A')
                                
                                # Tạo nội dung tin nhắn cảnh báo
                                reply_message = (
                                    f"⚠️ CẢNH BÁO TỪ CYBERSHIELD ⚠️\n\n"
                                    f"Tin nhắn bạn vừa nhận có dấu hiệu nguy hiểm (Điểm: {score}/5).\n\n"
                                    f"🔎 Phân tích: {reason}\n\n"
                                    f"💡 Gợi ý: {recommend}"
                                )
                                send_message(sender_id, reply_message)
                            else:
                                # Nếu tin nhắn an toàn, bot sẽ im lặng để không làm phiền
                                print(" Tin nhắn được xác định là AN TOÀN. Bỏ qua phản hồi.")
                            # <<< KẾT THÚC TÍCH HỢP AI >>>
                        
                        else:
                            print("Received a message without text content (e.g., sticker, attachment).")
                    
    except Exception as e:
        print(f"An error occurred during webhook processing: {e}")
        return 'Internal Server Error', 500

    return 'OK', 200

def send_message(recipient_id, message_text):
    """
    Gửi tin nhắn phản hồi đến người dùng.
    (Đổi tên từ send_simple_reply để tổng quát hơn)
    """
    API_URL = 'https://graph.facebook.com/v23.0/me/messages'
    
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    print(f"Preparing to send message to {recipient_id}")

    try:
        r = requests.post(API_URL, params={'access_token': PAGE_ACCESS_TOKEN}, json=payload, headers=headers)
        print(f"API request sent. Status code: {r.status_code}")
        if r.status_code != requests.codes.ok:
            print('Error sending message:', r.text)
        else:
            print('Message sent successfully!')
    except Exception as e:
        print(f"An error occurred while sending message: {e}")
