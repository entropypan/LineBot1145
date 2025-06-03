from flask import Flask, request, abort

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    # 取得 LINE 傳來的請求內容
    body = request.get_data(as_text=True)
    print("Request body:", body)

    # 這裡可以加入簽名驗證（推薦）
    # signature = request.headers.get('X-Line-Signature')
    # 驗證簽名...

    # 處理 webhook 內容
    # 這裡可以根據需求解析 JSON 並回應
    return 'OK'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)