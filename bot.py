import logging
import requests
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ---------------- CONFIGURATION ---------------- #
BOT_TOKEN = "8451758265:AAE59kkZqp7R7A-riOyDVlpZ5_Ljj6Vfc3E"  # 🔴 এখানে তোমার বটের টোকেন বসাও
ACCESS_PASSWORD = "robin1235"
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
# ----------------------------------------------- #

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Banner Art
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
    """
    🔥 SUPER HACKER STYLE LOGIN PAGE 🔥
    """
    login_msg = (
        f"{BANNER}"
        "<b>🔒 SYSTEM LOCKED: AUTHENTICATION REQUIRED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 <b>USER:</b> <code>GUEST_USER</code>\n"
        "🛡️ <b>SECURITY:</b> <code>AES-256 ENCRYPTED</code>\n"
        "📡 <b>CONNECTION:</b> <code>SECURE GATEWAY</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b>ACCESS RESTRICTED!</b>\n"
        "This terminal is protected by <b>MD ROBIN ISLAM</b>.\n"
        "Unauthorized access attempts will be logged.\n\n"
        "🔑 <b>ENTER ACCESS KEY TO UNLOCK:</b>"
    )
    await update.message.reply_text(login_msg, parse_mode=ParseMode.HTML)

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """পাসওয়ার্ড চেক এবং অ্যানিমেশন ইফেক্ট"""
    user_msg = update.message.text
    chat_id = update.effective_chat.id

    # যদি ইউজার অলরেডি লগইন করা থাকে
    if context.user_data.get('logged_in'):
        await update.message.reply_text("⚠️ System already active! Check incoming signals.")
        return

    if user_msg == ACCESS_PASSWORD:
        context.user_data['logged_in'] = True
        context.user_data['wins'] = 0
        context.user_data['losses'] = 0
        context.user_data['last_period'] = None
        context.user_data['last_prediction'] = None
        
        # লগইন সফল হলে হ্যাকিং এনিমেশন
        status_msg = await update.message.reply_text("🔄 Verifying Credentials...")
        await asyncio.sleep(1)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="🔓 Password Accepted! Decrypting...")
        await asyncio.sleep(1)
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text="🟢 <b>SYSTEM BREACH SUCCESSFUL!</b>", parse_mode=ParseMode.HTML)
        
        await update.message.reply_html(
            f"{BANNER}"
            "⚡ <b>HACKED BY:</b> MD ROBIN ISLAM\n"
            "⚡ <b>STATUS:</b> <code>ADMIN ACCESS GRANTED</code>\n"
            "⚡ <b>MODE:</b> <code>VIP 7-STEP STRATEGY</code>"
        )
        
        # অটোমেটিক লুপ চালু করা (JobQueue)
        context.job_queue.run_repeating(game_loop, interval=5, first=1, chat_id=chat_id, user_id=chat_id)
    else:
        await update.message.reply_html("❌ <b>ACCESS DENIED!</b>\nInvalid Password. Connection Terminated.")

def fetch_data():
    """API থেকে ডেটা ফেচ"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        params = {"pageNo": 1, "pageSize": 20, "typeId": 1, "language": 0, "random": "4f3d7f7a8a3d4f3d"}
        res = requests.get(API_URL, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data['code'] == 0:
                return data['data']['list']
        return None
    except:
        return None

async def game_loop(context: ContextTypes.DEFAULT_TYPE):
    """মেইন গেম লুপ"""
    job = context.job
    chat_id = job.chat_id
    
    user_data = context.application.user_data[job.user_id]
    
    history = fetch_data()
    if not history:
        return

    current_last_period = int(history[0]['issueNumber'])
    next_period = current_last_period + 1
    
    last_period_saved = user_data.get('last_period')
    last_prediction_saved = user_data.get('last_prediction')

    # রেজাল্ট চেকিং
    if last_period_saved == current_last_period:
        real_num = int(history[0]['number'])
        real_res = "BIG" if real_num >= 5 else "SMALL"

        msg = ""
        if last_prediction_saved == real_res:
            user_data['wins'] += 1
            msg = f"✅ <b>PROFIT SECURED!</b>\nResult: <b>{real_res}</b> WON! 💰"
        else:
            user_data['losses'] += 1
            msg = f"❌ <b>LOSS DETECTED!</b>\nResult: <b>{real_res}</b> CAME! 💀"
        
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=ParseMode.HTML)
        user_data['last_period'] = None

    # নতুন সিগন্যাল জেনারেট করা
    if last_period_saved != next_period:
        
        # --- LOGIC START (Dragon + Zigzag + AABB) ---
        results = []
        for item in history[:10]:
            num = int(item['number'])
            results.append("BIG" if num >= 5 else "SMALL")

        last_1 = results[0] # Latest
        last_2 = results[1] # Previous
        last_3 = results[2] # Before Previous

        prediction = ""
        hack_type = ""

        # LOGIC 1: DOUBLE PATTERN (AABB)
        # প্যাটার্ন: BB S -> ধরব S (যাতে BB SS হয়)
        if last_2 == last_3 and last_1 != last_2:
            prediction = last_1
            hack_type = "DOUBLE PATTERN (AABB) 🧬"
        
        # LOGIC 2: DRAGON (TREND)
        # প্যাটার্ন: B B -> ধরব B
        elif last_1 == last_2:
            prediction = last_1
            hack_type = "TREND DETECTED (DRAGON) 🐉"
        
        # LOGIC 3: ZIGZAG (FLIP)
        # প্যাটার্ন: B S -> ধরব B (উল্টোটা)
        else:
            prediction = "SMALL" if last_1 == "BIG" else "BIG"
            hack_type = "ZIGZAG DETECTED (FLIP) ⚡"
        # --- LOGIC END ---

        user_data['last_period'] = next_period
        user_data['last_prediction'] = prediction

        # টেলিগ্রাম মেসেজ ডিজাইন (টার্মিনাল স্টাইল)
        color_dot = "🔵" if prediction == "BIG" else "🟡"
        stream_line = " ".join(["B" if int(x['number']) >= 5 else "S" for x in history[:8]])
        
        terminal_msg = (
            f"😈 <b>TARGET PERIOD:</b> <code>{next_period}</code>\n"
            f"🦠 <b>HACK TYPE:</b> <code>{hack_type}</code>\n"
            f"🎯 <b>PREDICTION:</b> <b>{prediction}</b> {color_dot}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 <i>INVESTMENT PLAN: USE 7-STEP</i>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📡 <b>DATA STREAM:</b> <code>{stream_line}</code>\n\n"
            f"🏆 WINS: {user_data['wins']} | 💀 LOSS: {user_data['losses']}"
        )

        await context.bot.send_message(chat_id=chat_id, text=terminal_msg, parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_password))

    print("🤖 BOT IS RUNNING... (Press Ctrl+C to stop)")
    application.run_polling()
