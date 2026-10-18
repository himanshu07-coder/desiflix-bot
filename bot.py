import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------------------------------------------
# 1. KEEP-ALIVE SERVER FOR RENDER
# ----------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DesiFlix Universal AI Hub is Active!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ----------------------------------------------------
# 2. CONFIGURATION SETUP
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAGg8kO-C7uKzRjxpCddjlDAeanK_2mNQ_A"

# Aapka Direct Adsterra Monetization Link
ADSTERRA_LINK = "https://asiafilm.org/4/9fff5fa87f389039e2bb5eed7db9bdae"

# Aapka Main Updates Channel
MAIN_HUB_USERNAME = "@GRANDCINEMAS"

# ----------------------------------------------------
# 3. AUTO-DELETION HELPER
# ----------------------------------------------------
async def schedule_message_deletion(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int = 600):
    await asyncio.sleep(delay_seconds)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# ----------------------------------------------------
# 4. BOT HANDLERS & LOGIC
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_name = update.effective_user.first_name
    
    # Deep-link support from channel (Tap to Search button)
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
    
    # Universal SearchIT Format Layout (Works for Movies, Web Series, & Courses)
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
        await update