# LINE Bot Reminder Project

This project is a LINE Bot that allows users to send reminders or to-do items. The bot will parse the messages to extract time and event information, and store the reminders in JSON format for future notifications.

## Project Structure

```
linebot-reminder
├── src
│   ├── app.py                # Entry point of the application, sets up Flask and handles LINE webhook requests.
│   ├── reminder
│   │   ├── __init__.py       # Initializes the reminder module.
│   │   ├── parser.py         # Contains the ReminderParser class for parsing reminder messages.
│   │   └── storage.py        # Contains the ReminderStorage class for storing reminders in JSON format.
│   └── types
│       └── reminder.py       # Defines data structures related to reminders.
├── requirements.txt          # Lists the required Python packages for the project.
└── README.md                 # Documentation for setting up and using the LINE Bot.
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd linebot-reminder
   ```

2. **Install dependencies**:
   Make sure you have Python and pip installed. Then run:
   ```
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   You need to set the following environment variables for the LINE Bot to work:
   - `LINE_CHANNEL_SECRET`: Your LINE channel secret.
   - `LINE_CHANNEL_ACCESS_TOKEN`: Your LINE channel access token.

4. **Run the application**:
   Start the Flask application by running:
   ```
   python src/app.py
   ```

5. **Set up the webhook**:
   Configure your LINE Messaging API settings to point to your server's `/callback` endpoint.

## Usage

Once the bot is set up, you can send messages to the bot with reminders or to-do items. The bot will parse the messages and store them for future notifications.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.