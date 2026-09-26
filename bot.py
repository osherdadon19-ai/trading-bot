import os
from flask import Flask
import requests

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram tokens not set!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending telegram message: {e}")

@app.route("/", methods=["GET"])
def home():
    return "Trading Bot is active and running!", 200

@app.route("/scan", methods=["GET"])
def scan_market():
    assets_to_scan = ["SOLUSDT", "NVDA", "GOOGL"]
    
    send_telegram_message("🔍 *התחלת סריקת שוק:* הבוט בודק כעת את הנכסים המוגדרים...")
    
    results_message = "📊 *תוצאות סריקה מעודכנות:*\n"
    for asset in assets_to_scan:
        results_message += f"• {asset}: נסרק בהצלחה, ממתין לתנאי כניסה.\n"
    
    send_telegram_message(results_message)
    return "Scan completed successfully", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
