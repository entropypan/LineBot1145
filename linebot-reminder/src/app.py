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



scheduler = BackgroundScheduler()
scheduler.add_job(func=notify_reminders, trigger="interval", minutes=1)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)