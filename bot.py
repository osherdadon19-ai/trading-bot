import time
import requests
import yfinance as yf
import pandas as pd

TELEGRAM_BOT_TOKEN = "8629057686:AAHJMtuu2ueJmFtNg3JmYb743X1rr61mNBE"
TELEGRAM_CHAT_ID = "5240416774"

WATCHLIST = [
    "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", 
    "BTC-USD", "ETH-USD", "SOL-USD"
]

# מעקב פוזיציות פעילות שנפתחו (כדי להמשיך לחקור ולעדכן עליהן)
active_positions = {}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def analyze_and_scan():
    print("AI Agent scanning all vectors (Technical, Volume, Momentum & Active Positions)...")
    
    for ticker in WATCHLIST:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="60d")
            info = stock.info if "-USD" not in ticker else {}
            
            if hist.empty or len(hist) < 30:
                continue
                
            # חישוב אינדיקטורים טכניים מתקדמים
            data = hist.copy()
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            current_rsi = data['RSI'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            # MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            macd = (exp1 - exp2).iloc[-1]
            macd_signal = (exp1 - exp2).ewm(span=9, adjust=False).mean().iloc[-1]
            
            # נפח מסחר
            avg_volume = data['Volume'].rolling(window=20).mean().iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            is_volume_spike = current_volume > (avg_volume * 1.2)
            
            asset_type = "קריפטו 🪙" if "-USD" in ticker else "מניה 📈"
            
            # ==========================================
            # חלק א': מעקב אחרי פוזיציות שכבר פתוחות (ניטור רציף)
            # ==========================================
            if ticker in active_positions:
                pos = active_positions[ticker]
                elapsed_cycles = pos['cycles'] + 1
                active_positions[ticker]['cycles'] = elapsed_cycles
                
                entry_p = pos['entry']
                profit_pct = ((current_price - entry_p) / entry_p) * 100
                
                # בדיקת תנאי יציאה או סכנה פתאומית
                is_danger = current_rsi > 78 or current_rsi < 35 or macd < macd_signal
                is_time_expired = elapsed_cycles >= 12  # הגבלת זמן שהייה בפוזיציה (כ-3 שעות סריקה)
                
                if is_danger or is_time_expired or current_price <= pos['stop_loss'] or current_price >= pos['take_profit']:
                    reason = "הגעת ליעד/סטופ"
                    if is_danger:
                        reason = "היפוך מומנטום פתאומי בגרף (סכנת ירידה)"
                    elif is_time_expired:
                        reason = "מיצוי אופק הזמן המומלץ לפוזיציה"
                        
                    exit_msg = (
                        f"🚨 *התרעת יציאה מדויקת מהסוכן!* 🚨\n\n"
                        f"🎯 *נכס:* `{ticker}`\n"
                        f"🚪 *מחיר יציאה מומלץ:* `{round(current_price, 2)}`\n"
                        f"📊 *רווח/הפסד מצטבר:* `{profit_pct:.2f}%`\n"
                        f"📌 *סיבת יציאה:* `{reason}`\n\n"
                        f"🛡️ *סטטוס:* הפוזיציה נסגרה בתיק, ממשיכים לסרוק הזדמנויות חדשות."
                    )
                    send_telegram_alert(exit_msg)
                    del active_positions[ticker] # מחיקה מרשימת המעקב הפעיל
                    continue
                else:
                    # עדכון שוטף למשקיע תוך כדי החזקת הנכס
                    update_msg = (
                        f"🔍 *עדכון מעקב סוכן חי (עבור {ticker})*\n"
                        f"• מחיר נוכחי: `{round(current_price, 2)}` | תשואה: `{profit_pct:+.2f}%`\n"
                        f"• RSI נוכחי: `{round(current_rsi, 2)}` | מומנטום: `יציב תקין`\n"
                        f"• זמן נותר מוערך בפוזיציה: `כ-{(12 - elapsed_cycles) * 15} דקות`"
                    )
                    # שולח עדכון מדי פעם כדי לעדכן אותך במצב המדויק
                    if elapsed_cycles % 4 == 0:
                        send_telegram_alert(update_msg)
                    continue

            # ==========================================
            # חלק ב': חיפוש הזדמנויות כניסה חדשות (סטאפים איכותיים)
            # ==========================================
            pe_ratio = info.get('trailingPE', 'N/A')
            is_macd_bullish = macd > macd_signal
            is_rsi_healthy = 40 <= current_rsi <= 65
            
            if is_macd_bullish and is_rsi_healthy and is_volume_spike:
                entry_price = round(current_price, 2)
                stop_loss = round(current_price * 0.96, 2)
                take_profit = round(current_price * 1.07, 2)
                
                # שמירת הפוזיציה במעקב חי
                active_positions[ticker] = {
                    'entry': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'cycles': 0
                }
                
                message = (
                    f"🎯 *הסוכן האישי - פקודת כניסה מאושרת!* 🎯\n\n"
                    f"📊 *סוג נכס:* {asset_type}\n"
                    f"🏷️ *סימבול:* `{ticker}`\n\n"
                    f"📈 *מחיר כניסה (Entry):* `{entry_price}`\n"
                    f"⏳ *אופק זמן מומלץ בפוזיציה:* `בין שעון ל-3 שעות (או עד הגעה ליעד)`\n"
                    f"🛑 *סטופ לוס (הגנה קשיחה):* `{stop_loss}`\n"
                    f"💰 *יעד רווח (Take Profit):* `{take_profit}`\n\n"
                    f"📊 *נתוני חקירה מלאים:* RSI בטווח הבריא (`{round(current_rsi, 2)}`), מומנטום MACD חיובי, ונפח מסחר חריג שתומך במהלך.\n\n"
                    f"🛡️ *הוראה:* מעקב רציף הופעל בשרת, אעדכן אותך מיד על כל שינוי או סימן יציאה!"
                )
                send_telegram_alert(message)
                print(f"New position opened and tracked for {ticker}")
                
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

if __name__ == "__main__":
    print("Autonomous Personal Financial Agent with Live Position Tracking is Online 24/7!")
    while True:
        analyze_and_scan()
        time.sleep(900) # סריקה כל 15 דקות
