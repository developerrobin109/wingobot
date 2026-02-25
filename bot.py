import logging
import requests
import asyncio
import os
import threading
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ---------------- CONFIGURATION ---------------- #
BOT_TOKEN = "8451758265:AAE59kkZqp7R7A-riOyDVlpZ5_Ljj6Vfc3E"
ACCESS_PASSWORD = "robin1235"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"

# 🔥 ফ্রি প্রক্সি লিস্ট (এগুলো মাঝে মাঝে পরিবর্তন হতে পারে)
PROXY_LIST = [
    "http://202.162.212.164:80",
    "http://103.152.112.162:80", 
    "http://124.70.16.24:8080",
    "http://47.251.50.117:80",
    "http://8.219.97.248:80",
    "http://20.210.113.32:80",
    "http://103.49.202.252:80",
    "http://114.129.2.82:8081"
]
# ----------------------------------------------- #

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY SERVER ---
class SimpleHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is Live with Proxy!')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTP)
    server.serve_forever()

def start_dummy_server():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
# --------------------

BANNER = """
<pre>
██╗    ██╗██╗███╗   ██╗ ██████╗  ██████╗ 
██║    ██║██║████╗  ██║██╔════╝ ██╔═══██╗
██║ █╗ ██║██║██╔██╗ ██║██║  ███╗██║   ██║
██║███╗██║██║██║╚██╗██║██║   ██║██║   ██║
╚███╔███╔╝██║██║ ╚████║╚██████╔╝╚██████╔╝
 ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝ 
</pre>
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    login_msg = (
        f"{BANNER}"
        "<b>🔒 SYSTEM LOCKED: AUTHENTICATION REQUIRED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 <b>USER:</b> <code>GUEST_USER</code>\n"
        "🛡️ <b>SECURITY:</b> <code>AES-256 ENCRYPTED</code>\n"
        "📡 <b>NETWORK:</b> <code>PROXY ROTATION ACTIVE</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 <b>ENTER ACCESS KEY TO UNLOCK:</b>"
    )
    await update.message.reply_text(login_msg, parse_mode=ParseMode.HTML)

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    chat_id = update.effective_chat.id

    if context.user_data.get('logged_in'):
        await update.message.reply_text("⚠️ System already active!")
        return

    if user_msg == ACCESS_PASSWORD:
        context.user_data['logged_in'] = True
        context.user_data['wins'] = 0
        context.user_data['losses'] = 0
        context.user_data['last_period'] = None
        
        await update.message.reply_text("🔓 Access Granted! Establishing Secure Connection...")
        await asyncio.sleep(1)
        
        await update.message.reply_html(
            f"{BANNER}"
            "⚡ <b>STATUS:</b> <code>CONNECTED via PROXY</code>\n"
            "⚡ <b>MODE:</b> <code>VIP STRATEGY</code>\n"
            "🚀 <b>SCANNING WINGO SERVER...</b>"
        )
        
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id)
    else:
        await update.message.reply_text("❌ Wrong Password!")

def fetch_data():
    """স্মার্ট প্রক্সি সিস্টেম"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.ar-lottery01.com/'
    }
    params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}

    # ১. প্রথমে ডাইরেক্ট চেষ্টা করবে
    try:
        res = requests.get(API_URL, headers=headers, params=params, timeout=5)
        if res.status_code == 200 and res.json()['code'] == 0:
            return res.json()['data']['list']
    except:
        pass # ডাইরেক্ট ফেইল হলে নিচে যাবে

    # ২. ডাইরেক্ট না হলে প্রক্সি দিয়ে চেষ্টা করবে (৩ বার)
    for _ in range(3):
        try:
            proxy_ip = random.choice(PROXY_LIST)
            proxies = {"http": proxy_ip, "https": proxy_ip}
            
            # প্রক্সি দিয়ে রিকোয়েস্ট
            res = requests.get(API_URL, headers=headers, params=params, proxies=proxies, timeout=5)
            
            if res.status_code == 200 and res.json()['code'] == 0:
                return res.json()['data']['list']
        except:
            continue # এই প্রক্সি কাজ না করলে পরেরটা দেখবে

    return None

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_data = context.application.user_data[job.user_id]
    
    history = fetch_data()
    
    if not history:
        # কানেকশন না পেলে ইউজারকে জানাবে
        if not user_data.get('error_shown'):
            await context.bot.send_message(chat_id=chat_id, text="⚠️ <b>Retrying Connection with Proxy...</b>", parse_mode=ParseMode.HTML)
            user_data['error_shown'] = True
        return
    
    user_data['error_shown'] = False # কানেকশন পেলে এরর রিসেট

    current_last_period = int(history[0]['issueNumber'])
    next_period = current_last_period + 1
    
    last_period_saved = user_data.get('last_period')
    last_prediction_saved = user_data.get('last_prediction')

    # WIN/LOSS LOGIC
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            msg = f"✅ <b>WIN!</b> {real_res} 💰"
        else:
            user_data['losses'] += 1
            msg = f"❌ <b>LOSS!</b> {real_res} 💀"
        
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)
        user_data['last_period'] = None

    # PREDICTION LOGIC
    if last_period_saved != next_period:
        results = ["BIG" if int(x['number']) >= 5 else "SMALL" for x in history[:10]]
        l1, l2, l3 = results[0], results[1], results[2]

        if l2 == l3 and l1 != l2:
            pred, h_type = l1, "AABB 🧬"
        elif l1 == l2:
            pred, h_type = l1, "DRAGON 🐉"
        else:
            pred, h_type = ("SMALL" if l1 == "BIG" else "BIG"), "FLIP ⚡"

        user_data['last_period'] = next_period
        user_data['last_prediction'] = pred
        
        stream = " ".join(["B" if int(x['number']) >= 5 else "S" for x in history[:8]])
        
        msg = (
            f"😈 <b>TARGET:</b> <code>{next_period}</code>\n"
            f"🦠 <b>TYPE:</b> {h_type}\n"
            f"🎯 <b>PREDICTION:</b> <b>{pred}</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📡 DATA: <code>{stream}</code>\n"
            f"🏆 W: {user_data['wins']} | 💀 L: {user_data['losses']}"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    start_dummy_server()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_password))
    app.run_polling()
