            import os
            import requests
            from flask import Flask, request, abort
            
            app = Flask(__name__)
            
            N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
            DEFAULT_GOOGLE_CLIENT_ID = os.environ.get('DEFAULT_GOOGLE_CLIENT_ID')
            
            @app.route("/callback", methods=['POST'])
            def callback():
                body_from_line = request.json
            
                custom_data = {
                    "google_client_id": DEFAULT_GOOGLE_CLIENT_ID
                }
            
                body_from_line['custom_data'] = custom_data
            
                try:
                    requests.post(
                        N8N_WEBHOOK_URL,
                        json=body_from_line,
                        headers={'Content-Type': 'application/json'},
                        timeout=5
                    )
                except requests.exceptions.RequestException as e:
                    print(f"Error forwarding request to n8n: {e}")
                    abort(500)
            
                return 'OK'
            
            # gunicorn 會自動找到 'app' 物件，所以這段在 Render 上不會被執行
            if __name__ == "__main__":
                app.run()
