from flask import Flask, request, abort
import hashlib
import hmac
import os
import base64
import json
from datetime import datetime, timedelta
import re
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage, PushMessage

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的 channel secret")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

REMINDER_FILE = "reminders.json"

def load_reminders():
    if not os.path.exists(REMINDER_FILE):
        return []
    with open(REMINDER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_reminders(reminders):
    with open(REMINDER_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

def parse_reminder(text: str) -> dict:
    """
    簡易自然語言解析提醒，支援格式如：
    "明天下午2點開會"、"6/4 14:00 開會"
    """
    now = datetime.now()
    if "明天" in text:
        base_date = now + timedelta(days=1)
        text = text.replace("明天", "")
    elif "後天" in text:
        base_date = now + timedelta(days=2)
        text = text.replace("後天", "")
    else:
        base_date = now

    # 支援 "下午2點"、"14:00"
    time_match = re.search(r'(下午)?(\d{1,2})[:點](\d{2})?', text)
    if time_match:
        hour = int(time_match.group(2))
        minute = int(time_match.group(3)) if time_match.group(3) else 0
        if time_match.group(1):  # 有"下午"
            if hour < 12:
                hour += 12
        event_time = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        event = text[time_match.end():].strip()
    else:
        # 支援 "6/4 14:00"
        date_time_match = re.search(r'(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})', text)
        if date_time_match:
            month = int(date_time_match.group(1))
            day = int(date_time_match.group(2))
            hour = int(date_time_match.group(3))
            minute = int(date_time_match.group(4))
            year = now.year
            event_time = datetime(year, month, day, hour, minute)
            event = text[date_time_match.end():].strip()
        else:
            return None

    return {
        "time": event_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": event
    }

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')

    # 驗證簽名
    hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    computed_signature = base64.b64encode(hash).decode()
    if signature != computed_signature:
        abort(400, "Invalid signature")

    events = parser.parse(body, signature)
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            reminder = parse_reminder(event.message.text)
            if reminder:
                # 加入 user_id
                reminder["user_id"] = event.source.user_id
                # 寫入 reminders.json
                reminders = load_reminders()
                reminders.append(reminder)
                save_reminders(reminders)
                print("收到提醒：", reminder)
                reply = f"已設定提醒：{reminder['event']}，時間：{reminder['time']}"
            else:
                reply = "請輸入正確的提醒格式，例如：明天下午2點開會 或 6/4 14:00 開會"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply)
            )
    return 'OK'

def notify_reminders():
    reminders = load_reminders()
    now = datetime.now()
    notify_time = now + timedelta(minutes=10)
    new_reminders = []
    for reminder in reminders:
        remind_time = datetime.strptime(reminder["time"], "%Y-%m-%dT%H:%M:%S")
        # 如果時間在10分鐘內，推播通知
        if now < remind_time <= notify_time:
            try:
                line_bot_api.push_message(
                    reminder["user_id"],
                    TextSendMessage(text=f"提醒：{reminder['event']}，時間：{reminder['time']}")
                )
                print(f"已推播提醒給 {reminder['user_id']}：{reminder['event']}，時間：{reminder['time']}")
            except Exception as e:
                print("推播失敗：", e)
        # 保留未到期的提醒
        if remind_time > now:
            new_reminders.append(reminder)
    save_reminders(new_reminders)

# 啟動 APScheduler 排程
scheduler = BackgroundScheduler()
scheduler.add_job(func=notify_reminders, trigger="interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)