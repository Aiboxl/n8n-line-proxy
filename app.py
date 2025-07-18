import os
import requests
from flask import Flask, request, abort

# 初始化 Flask 應用程式
app = Flask(__name__)

# 從環境變數中讀取我們在 Render 平台上設定好的秘密資訊
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
DEFAULT_GOOGLE_CLIENT_ID = os.environ.get('DEFAULT_GOOGLE_CLIENT_ID')

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
        # 設定5秒超時，避免 Line 官方伺服器等待過久
        requests.post(
            N8N_WEBHOOK_URL,
            json=body_from_line,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        # 如果轉發失敗，在 Render 的後台日誌中印出錯誤，方便除錯
        print(f"Error forwarding request to n8n: {e}")
        # 中斷請求並回應一個伺服器錯誤
        abort(500)

    # 回應一個 'OK' 給 Line 官方伺服器，表示我們已成功收到訊息
    return 'OK'

# 這段是為了讓 gunicorn (Render 的應用程式伺服器) 能找到 'app' 物件
# 在 Render 的環境中，它不會直接被執行
if __name__ == "__main__":
    # 這行程式碼主要是在本地開發測試時使用
    app.run()
