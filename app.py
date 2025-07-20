import os
import requests
from flask import Flask, request, redirect, jsonify
from urllib.parse import urlencode

app = Flask(__name__)

# 從環境變數讀取 n8n 的 Webhook URL
# 如果您在 Render 上設定了 N8N_WEBHOOK_URL，它會自動讀取
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "")

# 從環境變數讀取 Google OAuth 的基本設定
# 如果您在 Render 上設定了這些變數，它會自動讀取
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
GOOGLE_SCOPES = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/calendar.readonly"

@app.route('/webhook_proxy', methods=['POST'])
def webhook_proxy():
    if not N8N_WEBHOOK_URL:
        return jsonify({"error": "N8N_WEBHOOK_URL is not configured"}), 500

    data = request.get_json()
    
    # 將固定的 Google Client ID 加入到 custom_data 中
    data['custom_data'] = {
        'google_client_id': GOOGLE_CLIENT_ID
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
        # 僅當中繼成功時回傳 200 OK
        if response.status_code >= 200 and response.status_code < 300:
            return jsonify({"status": "ok"}), 200
        else:
            # 如果 n8n 回傳錯誤，也將其視為一個錯誤
            return jsonify({"error": "Failed to forward to n8n", "n8n_status": response.status_code}), 502
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/redirect_to_google', methods=['GET'])
def redirect_to_google():
    user_id = request.args.get('user_id')
    if not user_id:
        return "Error: User ID is missing.", 400
    
    if not all([GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI]):
        return "Error: Google OAuth environment variables are not configured.", 500

    # 將 line_user_id 和 client_id 一起打包到 state 參數中
    # 注意：我們不再傳遞 client_id，因為後端可以從環境變數中讀取
    state_value = f"user_id={user_id}"

    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'scope': GOOGLE_SCOPES,
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': state_value
    }
    
    google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    
    return redirect(google_auth_url)

# 健康檢查端點，用於確認服務是否存活
@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "Proxy is running"}), 200

if __name__ == '__main__':
    # 使用 Gunicorn 時，通常不會執行這一段
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
