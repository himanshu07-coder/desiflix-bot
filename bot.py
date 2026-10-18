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
# 1. CONFIGURATION SETUP
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAGg8kO-C7uKzRjxpCddjlDAeanK_2mNQ_A"
ADSTERRA_LINK = "https://asiafilm.org/4/9fff5fa87f389039e2bb5eed7db9bdae"
MAIN_HUB_USERNAME = "@GRANDCINEMAS"

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://desiflix-bot.onrender.com")

app = Flask(__name__)
telegram_app = None
init_lock = asyncio.Lock()

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
# 2. BOT HANDLERS & LOGIC
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_name = update.effective_user.first_name
    
    if args:
        search_query = " ".join(args).replace("_", " ")
        await process_content_results(update, context, search_query)
        return

    welcome_text = (
        f"👋 **Hey @{update.effective_user.username or user_name}!**\n\n"
        f"🎬 **Movies, Series & Skill Courses Ready.**\n"
        f"Explore our main channel:\n"
        f"👉 {MAIN_HUB_USERNAME} |\n\n"
        f"👇 *Type any Movie, Web Series, or Skill Course name below!*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    await process_content_results(update, context, user_query)

async def process_content_results(update: Update, context: ContextTypes.DEFAULT_TYPE, query_text: str):
    clean_title = query_text.title()
    
    keyboard = [
        [InlineKeyboardButton(f"[Full HD / 1080p Pack] {clean_title}", callback_data=f"ad_gate:{query_text[:15]}:1080p")],
        [InlineKeyboardButton(f"[Standard HD / 720p Pack] {clean_title}", callback_data=f"ad_gate:{query_text[:15]}:720p")],
        [InlineKeyboardButton(f"[Compressed / 480p Pack] {clean_title}", callback_data=f"ad_gate:{query_text[:15]}:480p")],
        [InlineKeyboardButton(f"[Complete Zip / Drive Resource] {clean_title}", callback_data=f"ad_gate:{query_text[:15]}:zip")],
        [
            InlineKeyboardButton("🗓️ 1/10", callback_data="page_noop"),
            InlineKeyboardButton("NEXT ⏩", callback_data="page_next")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    header_text = (
        f"👋 **Hey @{update.effective_user.username or update.effective_user.first_name}!**\n"
        f"🔍 **Results ready for:** `{clean_title}`\n"
        f"Explore our hubs:\n"
        f"👉 {MAIN_HUB_USERNAME} |"
    )
    
    if update.message:
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=header_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("ad_gate:"):
        _, item_name, quality = data.split(":", 2)
        
        ad_keyboard = [
            [InlineKeyboardButton("🔓 Step 1: Open Adsterra Sponsor", url=ADSTERRA_LINK)],
            [InlineKeyboardButton("⚡ Step 2: Get File / Content Link", callback_data=f"deliver_file:{item_name}:{quality}")]
        ]
        
        await query.message.reply_text(
            f"⚠️ **Monetization Step Required:**\n\n"
            f"Please click **'Step 1'** to unlock sponsorship, then tap **'Step 2'** to receive `{item_name.title()}` ({quality})!",
            reply_markup=InlineKeyboardMarkup(ad_keyboard),
            parse_mode="Markdown"
        )
        
    elif data.startswith("deliver_file:"):
        _, item_name, quality = data.split(":", 2)
        
        caption_text = (
            f"🚀 **{item_name.title()} ({quality})**\n\n"
            f"📄 `{item_name.title()}_Full_Pack.mkv`\n"
            f"🔊 **Audio / Format:** Hindi, English / Digital Resource\n"
            f"🌐 **Content Hub:** {MAIN_HUB_USERNAME}\n\n"
            f"⚠️ **Auto-delete notice:** Message will auto-delete in **10 minutes**.\n"
            f"Forward to Saved Messages to keep it permanently."
        )
        
        timer_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("⌛ Auto-Delete in 10 min ⌛", callback_data="timer_info")]
        ])
        
        await query.message.reply_text(caption_text, reply_markup=timer_btn, parse_mode="Markdown")

# ----------------------------------------------------
# 3. FLASK WEBHOOK ROUTE
# ----------------------------------------------------
@app.route('/')
def index():
    return "DesiFlix Webhook Bot is Running Smoothly!"

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
        logger.error(f"Initialization error: {e}")

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)