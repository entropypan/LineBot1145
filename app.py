from flask import Flask, request, abort
import hashlib
import hmac
import os
# 需要安裝 line-bot-sdk
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage


app = Flask(__name__)

# 設定你的 LINE Channel Secret
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的 channel secret")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # 取得 LINE 傳來的請求內容
    body = request.get_data(as_text=True)
    print("Request body:", body)

    # 取得 X-Line-Signature 標頭
    signature = request.headers.get('X-Line-Signature', '')

    # 驗證簽名
    hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    computed_signature = hashlib.base64.b64encode(hash).decode()
    if signature != computed_signature:
        abort(400, "Invalid signature")

    # 處理 webhook 內容
    # 這裡可以根據需求解析 JSON 並回應
    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)