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
# 1. RENDER PORT SERVER (Prevents Timeout)
# ----------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DesiFlix Search Bot is Active 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ----------------------------------------------------
# 2. BOT CONFIGURATION
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAFOEeKA_omSf8a1eXdg-1NU6_VgEJ18hPc"
# Aapka Adsterra Direct Link
AD_LINK_1 = "https://example.com/ad1"

# ----------------------------------------------------
# 3. HANDLERS
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to DesiFlix Search Bot!**\n\n"
        "🎬 Type any movie or series name below to search and unlock download links."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    
    keyboard = [
        [
            InlineKeyboardButton("🔓 Step 1: Unlock Quality Options (Ad 1)", url=AD_LINK_1)
        ],
        [
            InlineKeyboardButton("⚡ Next: Select Quality & Audio", callback_data=f"show_q:{query}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎬 **Movie Found:** `{query}`\n\n"
        "Pehle Step 1 Ad complete karein, phir Video Quality (480p/720p/1080p) choose karein.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("show_q:"):
        movie_name = data.split("show_q:")[1]
        
        quality_keyboard = [
            [
                InlineKeyboardButton("📥 480p (400MB)", callback_data=f"dl:{movie_name}:480p"),
                InlineKeyboardButton("📥 720p (900MB)", callback_data=f"dl:{movie_name}:720p")
            ],
            [
                InlineKeyboardButton("📥 1080p (1.8GB)", callback_data=f"dl:{movie_name}:1080p")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(quality_keyboard)
        
        await query.message.reply_text(
            f"✅ **Ad Verified! Select Quality for {movie_name}:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif data.startswith("dl:"):
        _, movie_name, quality = data.split(":")
        
        await query.message.reply_text(
            f"🎉 **Here is your link for {movie_name} ({quality}):**\n\n"
            f"🔗 [Click Here to Stream / Download File](https://example.com/download)\n\n"
            "⚠️ Link auto-deletes in 10 minutes.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

# ----------------------------------------------------
# 4. MAIN APPLICATION
# ----------------------------------------------------
def main():
    print("Starting bot...")
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    application.add_handler(CallbackQueryHandler(button_click_handler))

    application.run_polling()

if __name__ == "__main__":
    main()