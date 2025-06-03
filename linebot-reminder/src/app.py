from flask import Flask, request, abort
import os
import json
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
from pytz import timezone
from apscheduler.schedulers.background import BackgroundScheduler

from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
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
    now = datetime.now(timezone('Asia/Taipei'))
    if "明天" in text:
        base_date = now + timedelta(days=1)
        text = text.replace("明天", "")
    elif "後天" in text:
        base_date = now + timedelta(days=2)
        text = text.replace("後天", "")
    else:
        base_date = now

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
        date_time_match = re.search(r'(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})', text)
        if date_time_match:
            month = int(date_time_match.group(1))
            day = int(date_time_match.group(2))
            hour = int(date_time_match.group(3))
            minute = int(date_time_match.group(4))
            year = now.year
            event_time = datetime(year, month, day, hour, minute, tzinfo=timezone('Asia/Taipei'))
            event = text[date_time_match.end():].strip()
        else:
            return None

    if event_time.tzinfo is None:
        event_time = timezone('Asia/Taipei').localize(event_time)

    event_time_utc = event_time.astimezone(timezone('UTC'))
    return {
        "time": event_time_utc.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": event
    }

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')
    try:
        events = parser.parse(body, signature)
    except Exception as e:
        abort(400)

    reminders = load_reminders()
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_id = event.source.user_id
            message_text = event.message.text.strip()

            if message_text == "OK":
                reminders = [
                    reminder for reminder in reminders
                    if reminder["user_id"] != user_id or timezone('Asia/Taipei').localize(datetime.strptime(reminder["time"], "%Y-%m-%dT%H:%M:%S")) > datetime.now(timezone('Asia/Taipei'))
                ]
                save_reminders(reminders)
                reply = "已關閉您的提醒。"
            else:
                reminder = parse_reminder(message_text)
                if reminder:
                    reminder["user_id"] = user_id
                    reminders.append(reminder)
                    save_reminders(reminders)
                    remind_time_utc = datetime.strptime(reminder["time"], "%Y-%m-%dT%H:%M:%S")
                    remind_time_taipei = remind_time_utc.astimezone(timezone('Asia/Taipei'))
                    reply = f"已設定提醒：{reminder['event']}，時間：{remind_time_taipei.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    reply = "請輸入正確的提醒格式，例如：明天下午2點開會 或 6/4 14:00 開會"
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply)
                )
            except Exception as e:
                print("回覆訊息失敗：", e)
    return 'OK'

def notify_reminders():
    reminders = load_reminders()
    now = datetime.now(timezone('Asia/Taipei'))
    new_reminders = []
    for reminder in reminders:
        remind_time_utc = datetime.strptime(reminder["time"], "%Y-%m-%dT%H:%M:%S")
        remind_time_taipei = remind_time_utc.astimezone(timezone('Asia/Taipei'))
        ten_minutes_before = remind_time_taipei - timedelta(minutes=10)
        if ten_minutes_before <= now < remind_time_taipei:
            try:
                line_bot_api.push_message(
                    reminder["user_id"],
                    TextSendMessage(text=f"提醒：{reminder['event']}，時間：{remind_time_taipei.strftime('%Y-%m-%d %H:%M:%S')}")
                )
            except Exception as e:
                print("推播失敗：", e)
        else:
            new_reminders.append(reminder)
    save_reminders(new_reminders)

scheduler = BackgroundScheduler()
scheduler.add_job(func=notify_reminders, trigger="interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)