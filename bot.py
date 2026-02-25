import logging
import requests
import asyncio
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ---------------- CONFIGURATION ---------------- #
BOT_TOKEN = "8451758265:AAE59kkZqp7R7A-riOyDVlpZ5_Ljj6Vfc3E"
ACCESS_PASSWORD = "robin1235"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
# ----------------------------------------------- #

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY SERVER (Render-এ বট যাতে বন্ধ না হয়) ---
class SimpleHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot Running')

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTP)
    server.serve_forever()

def start_dummy_server():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
# --------------------------------------------------

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
    # নতুন করে শুরু করলে আগের ডাটা ক্লিয়ার হবে
    context.user_data.clear()
    
    login_msg = (
        f"{BANNER}"
        "<b>🔒 SYSTEM LOCKED: AUTHENTICATION REQUIRED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 <b>USER:</b> <code>GUEST_USER</code>\n"
        "🛡️ <b>SECURITY:</b> <code>AES-256 ENCRYPTED</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 <b>ENTER ACCESS KEY TO UNLOCK:</b>"
    )
    await update.message.reply_text(login_msg, parse_mode=ParseMode.HTML)

async def reset_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """বট রিসেট করার কমান্ড"""
    context.user_data.clear()
    # চলমান লুপগুলো বন্ধ করার চেষ্টা (JobQueue ক্লিয়ার)
    current_jobs = context.job_queue.get_jobs_by_name(str(update.effective_chat.id))
    for job in current_jobs:
        job.schedule_removal()
        
    await update.message.reply_text("🔄 <b>SYSTEM RESET SUCCESSFUL!</b>\nPlease type /start to login again.", parse_mode=ParseMode.HTML)

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    chat_id = update.effective_chat.id

    if context.user_data.get('logged_in'):
        await update.message.reply_text("⚠️ System already active! Wait for signals.\nType /reset to stop.")
        return

    if user_msg == ACCESS_PASSWORD:
        context.user_data['logged_in'] = True
        context.user_data['wins'] = 0
        context.user_data['losses'] = 0
        context.user_data['last_period'] = None
        
        await update.message.reply_text("🔓 Password Accepted! Starting Engine...")
        await asyncio.sleep(1)
        
        await update.message.reply_html(
            f"{BANNER}"
            "⚡ <b>STATUS:</b> <code>CONNECTED</code>\n"
            "⚡ <b>MODE:</b> <code>VIP STRATEGY ACTIVE</code>\n"
            "🚀 <b>WAITING FOR NEXT RESULT...</b>"
        )
        
        # লুপ শুরু (নাম হিসেবে চ্যাট আইডি ব্যবহার করা হয়েছে যাতে পরে বন্ধ করা যায়)
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id, name=str(chat_id))
    else:
        await update.message.reply_text("❌ Access Denied!")

def fetch_data():
    try:
        # হেডার পরিবর্তন করা হয়েছে যাতে ব্লক না খায়
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.ar-lottery01.com/'
        }
        params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}
        res = requests.get(API_URL, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 0:
                return data['data']['list']
        return None
    except Exception as e:
        return None

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    user_data = context.application.user_data[job.user_id]
    
    history = fetch_data()
    
    # যদি সার্ভার কানেকশন না পায়
    if not history:
        # প্রতিবার এরর মেসেজ না দিয়ে, শুধু একবার ওয়ার্নিং দিবে
        if not user_data.get('error_shown'):
            await context.bot.send_message(chat_id=chat_id, text="⚠️ <b>Server Connection Error!</b>\nRender IP might be blocked. Trying again...", parse_mode=ParseMode.HTML)
            user_data['error_shown'] = True
        return
    
    # কানেকশন ঠিক হলে এরর ফ্ল্যাগ রিসেট
    user_data['error_shown'] = False

    current_last_period = int(history[0]['issueNumber'])
    next_period = current_last_period + 1
    
    last_period_saved = user_data.get('last_period')
    last_prediction_saved = user_data.get('last_prediction')

    # WIN/LOSS CHECK
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        msg = ""
        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            msg = f"✅ <b>WIN!</b> {real_res}"
        else:
            user_data['losses'] += 1
            msg = f"❌ <b>LOSS!</b> {real_res}"
        
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)
        user_data['last_period'] = None

    # NEW SIGNAL
    if last_period_saved != next_period:
        results = ["BIG" if int(x['number']) >= 5 else "SMALL" for x in history[:10]]
        last_1, last_2, last_3 = results[0], results[1], results[2]

        if last_2 == last_3 and last_1 != last_2:
            pred, h_type = last_1, "AABB 🧬"
        elif last_1 == last_2:
            pred, h_type = last_1, "DRAGON 🐉"
        else:
            pred, h_type = ("SMALL" if last_1 == "BIG" else "BIG"), "FLIP ⚡"

        user_data['last_period'] = next_period
        user_data['last_prediction'] = pred
        
        msg = (
            f"😈 <b>TARGET:</b> <code>{next_period}</code>\n"
            f"🦠 <b>TYPE:</b> {h_type}\n"
            f"🎯 <b>PREDICTION:</b> <b>{pred}</b>\n"
            f"🏆 W: {user_data['wins']} | 💀 L: {user_data['losses']}"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    start_dummy_server()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_bot)) # নতুন রিসেট কমান্ড
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_password))
    app.run_polling()
