import os
import requests
from flask import Flask, request, abort, redirect
from urllib.parse import urlencode

# 初始化 Flask 應用程式
app = Flask(__name__)

# 從環境變數中讀取我們在 Render 平台上設定好的秘密資訊
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
DEFAULT_GOOGLE_CLIENT_ID = os.environ.get('DEFAULT_GOOGLE_CLIENT_ID')
N8N_CALLBACK_URL = "https://7edb9afc4763.ngrok-free.app/webhook/d9f23682-12f8-42de-8b4b-4b2a80d46d0e"

# 建立一個 Webhook 端點，路徑為 /callback
# Line 官方伺服器未來會將所有訊息都送到這裡
@app.route("/callback", methods=['POST'])
def callback():
    # 取得 Line 傳來的原始 JSON 資料
    body_from_line = request.json

    # 建立一個 custom_data 物件，並填入我們的 Google Client ID
    custom_data = {
        "google_client_id": DEFAULT_GOOGLE_CLIENT_ID
    }

    # 將這個 custom_data 物件，加入到從 Line 傳來的資料中
    body_from_line['custom_data'] = custom_data

    try:
        # 將我們 "加工" 過後的資料，轉發給 n8n
        requests.post(
            N8N_WEBHOOK_URL,
            json=body_from_line,
            headers={'Content-Type': 'application/json'},
            timeout=5 # 設定5秒超時
        )
    except requests.exceptions.RequestException as e:
        # 如果轉發失敗，在 Render 的後台日誌中印出錯誤，方便除錯
        print(f"Error forwarding request to n8n: {e}")
        # 中斷請求並回應一個伺服器錯誤
        abort(500)

    # 回應一個 'OK' 給 Line 官方伺服器，表示我們已成功收到訊息
    return 'OK'

# 建立一個跳板路由，將使用者重新導向到 Google 的授權頁面
@app.route("/redirect_to_google", methods=['GET'])
def redirect_to_google():
    # 從網址參數中取得 user_id，這是 n8n 傳給我們的
    user_id = request.args.get('user_id')
    if not user_id:
        return "Error: Missing user_id", 400

    # 在後端組合出完整的 Google 授權 URL
    state = f"{DEFAULT_GOOGLE_CLIENT_ID}:{user_id}"
    scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
    
    # 使用 urlencode 來確保所有參數都經過正確的 URL 編碼
    params = {
        'client_id': DEFAULT_GOOGLE_CLIENT_ID,
        'redirect_uri': N8N_CALLBACK_URL,
        'response_type': 'code',
        'scope': scope,
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    # 回傳一個 HTTP 302 重新導向指令，讓使用者的瀏覽器跳轉到 Google
    return redirect(google_auth_url)

# 這段是為了讓 gunicorn (Render 的應用程式伺服器) 能找到 'app' 物件
if __name__ == "__main__":
    # 這行程式碼主要是在本地開發測試時使用
    app.run()
