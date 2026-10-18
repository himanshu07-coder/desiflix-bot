import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAGg8kO-C7uKzRjxpCddjlDAeanK_2mNQ_A"
ADSTERRA_LINK = "https://asiafilm.org/4/9fff5fa87f389039e2bb5eed7db9bdae"
MAIN_HUB_USERNAME = "@GRANDCINEMAS"

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://desiflix-bot.onrender.com")

app = Flask(__name__)
telegram_app = None

async def setup_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    application.add_handler(CallbackQueryHandler(button_click_handler))
    
    await application.initialize()
    webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    
    return application

# ----------------------------------------------------
# BOT HANDLERS (3-STEP EARNING & FILE DELIVERY FLOW)
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        search_query = " ".join(args).replace("_", " ")
        await show_search_results(update, context, search_query)
        return

    welcome_text = (
        f"👋 **Welcome to {MAIN_HUB_USERNAME} Bot!**\n\n"
        f"🎬 *Yahan aap koi bhi Movie, Web Series ya Skill Course mang sakte hain.*\n\n"
        f"👇 **Bas apna item search karne ke liye naam type karein!**"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    await show_search_results(update, context, user_query)

async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, query_text: str):
    clean_title = query_text.title()
    
    # Search options list for user
    keyboard = [
        [InlineKeyboardButton(f"[2.26 GB] {clean_title} 1080p BluRay", callback_data=f"ad_gate:{query_text[:12]}:1080p")],
        [InlineKeyboardButton(f"[1.10 GB] {clean_title} 720p BluRay", callback_data=f"ad_gate:{query_text[:12]}:720p")],
        [InlineKeyboardButton(f"[450 MB] {clean_title} 480p Fast Rip", callback_data=f"ad_gate:{query_text[:12]}:480p")],
        [InlineKeyboardButton("🗓️ Page 1/1", callback_data="noop"), InlineKeyboardButton("NEXT ⏩", callback_data="noop")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"🔎 **Results found for:** `{clean_title}`\n\n"
        f"👇 *Apni pasand ki quality select karein:*"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = query.message.chat_id
    
    if data.startswith("ad_gate:"):
        _, item_name, quality = data.split(":", 2)
        
        # Step 2: Adsterra Monetization Gate
        ad_keyboard = [
            [InlineKeyboardButton("🔓 Step 1: Open Sponsor Ad (Earn)", url=ADSTERRA_LINK)],
            [InlineKeyboardButton("⚡ Step 2: Get File Now", callback_data=f"deliver:{item_name}:{quality}")]
        ]
        
        await query.message.reply_text(
            f"⚠️ **Monetization Step Required:**\n\n"
            f"File unlock karne ke liye:\n"
            f"1. **'Step 1'** par click karke ad dekhein.\n"
            f"2. Phir **'Step 2'** dabakar file prapt karein!",
            reply_markup=InlineKeyboardMarkup(ad_keyboard),
            parse_mode="Markdown"
        )
        
    elif data.startswith("deliver:"):
        _, item_name, quality = data.split(":", 2)
        
        file_caption = (
            f"🚀 **{item_name.title()} ({quality})**\n\n"
            f"📄 `{item_name.title()}_File.mkv`\n"
            f"🌐 **Hub:** {MAIN_HUB_USERNAME}\n\n"
            f"⚠️ **Security Notice:** Yeh message **1 minute** mein automatic delete ho jayega! Saved Messages mein forward kar lein."
        )
        
        timer_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("⌛ Auto-Delete in 1 min ⌛", callback_data="timer_info")]
        ])
        
        # Step 3: Send actual file document with 1-minute auto-delete timer
        try:
            sent_msg = await context.bot.send_document(
                chat_id=chat_id,
                document="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                caption=file_caption,
                reply_markup=timer_btn,
                parse_mode="Markdown"
            )
            asyncio.create_task(auto_delete_message(context, chat_id, sent_msg.message_id, 60))
        except Exception as e:
            logger.error(f"File send error: {e}")

async def auto_delete_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# ----------------------------------------------------
# FLASK WEBHOOK RUNNER
# ----------------------------------------------------
@app.route('/')
def index():
    return "Bot is Live and Optimized!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    global telegram_app
    if telegram_app is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        telegram_app = loop.run_until_complete(setup_bot())

    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    
    asyncio.run(telegram_app.process_update(update))
    return "OK", 200

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        telegram_app = loop.run_until_complete(setup_bot())
    except Exception as e:
        logger.error(f"Error: {e}")

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)