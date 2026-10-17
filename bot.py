import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------------------------------------------
# 1. RENDER PORT TIMEOUT FIX (Dummy Web Server)
# ----------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DesiFlix Search Bot is Running Live 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Start background thread for Render Port
threading.Thread(target=run_web_server, daemon=True).start()

# ----------------------------------------------------
# 2. BOT CONFIGURATION (WITH YOUR NEW TOKEN)
# ----------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8973049098:AAFOEeKA_omSf8a1eXdg-1NU6_VgEJ18hPc")
AD_LINK_1 = os.environ.get("AD_LINK_1", "https://example.com/ad1")
AD_LINK_2 = os.environ.get("AD_LINK_2", "https://example.com/ad2")

# ----------------------------------------------------
# 3. HANDLERS & LOGIC
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    welcome_text = (
        f"👋 Welcome **{user_first_name}** to **DesiFlix Search Bot**!\n\n"
        "🎬 Search for any movie, series, or video file by typing the name below.\n\n"
        "✨ Features:\n"
        "• Double Ad Verification System\n"
        "• Fast Search & Auto-Delete Links for Copyright Protection"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    
    keyboard = [
        [
            InlineKeyboardButton("🔓 Verify Ad 1", url=AD_LINK_1),
            InlineKeyboardButton("