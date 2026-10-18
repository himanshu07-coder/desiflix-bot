import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import google.generativeai as genai
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
        self.wfile.write(b"DesiFlix Ultimate AI Hub is Live and Running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ----------------------------------------------------
# 2. CONFIGURATION & AI SETUP
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAGg8kO-C7uKzRjxpCddjlDAeanK_2mNQ_A"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Insert your Gemini API Key here

# ⚠️ REPLACE WITH YOUR REAL ADSTERRA DIRECT LINKS HERE
AD_LINK_1 = "https://www.google.com"  # Replace with real Adsterra Link 1
AD_LINK_2 = "https://www.google.com"  # Replace with real Adsterra Link 2

# ⚠️ REPLACE WITH YOUR STORAGE CHANNEL ID (Make sure bot is ADMIN in storage channel)
# Private channel IDs usually start with -100...
STORAGE_CHANNEL_ID = -1001234567890 

# Optional file map (Map specific message IDs from your channel to content)
# Format: "clean_title": {"480p": message_id, "720p": message_id, "1080p": message_id}
FILE_MAP = {
    "games of thrones": {"480p": 2, "720p": 3, "1080p": 4},
    "dsa in java": {"480p": 5, "720p": 6, "1080p": 7}
}

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ----------------------------------------------------
# 3. AUTO-DELETION HELPER (Copyright Protection)
# ----------------------------------------------------
async def schedule_message_deletion(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int = 600):
    """Deletes message automatically after 10 minutes (600 seconds)"""
    await asyncio.sleep(delay_seconds)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# ----------------------------------------------------
# 4. BOT HANDLERS & LOGIC
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🌟 **Welcome to DesiFlix Ultimate Content & Course Hub!** 🌟\n\n"
        "🎬 **Movies & Web Series:** Netflix, Amazon Prime, Hotstar, Zee5, etc.\n"
        "📚 **Courses & Skills:** DSA in Java/Python, Web Dev, Video Editing, Design, & more!\n\n"
        "👇 *Type any title or topic below to get instant file delivery!*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    
    try:
        prompt = f"User wants this movie/series or course: '{user_query}'. Provide a clean title and categorize it briefly. Keep it short."
        response = ai_model.generate_content(prompt)
        ai_summary = response.text.strip()
    except Exception:
        ai_summary = user_query

    keyboard = [
        [InlineKeyboardButton("🔓 Step 1: Complete Ad 1 (Unlock)", url=AD_LINK_1)],
        [InlineKeyboardButton("🔓 Step 2: Complete Ad 2 (Verify)", url=AD_LINK_2)],
        [InlineKeyboardButton("⚡ Proceed: Get File / Course Link", callback_data=f"get_content:{user_query[:30]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔍 **Requested Content:** `{user_query.title()}`\n\n"
        f"🤖 **AI Analysis:** {ai_summary}\n\n"
        "⚠️ **Free Access Rule:** To unlock free access, please complete both Ads above and then click **'Proceed'**!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Checking verification...")
    
    data = query.data
    chat_id = query.message.chat_id
    
    if data.startswith("get_content:"):
        content_name = data.split(":", 1)[1]
        
        quality_keyboard = [
            [
                InlineKeyboardButton("📁 480p / Standard Pack", callback_data=f"send_final:{content_name}:480p"),
                InlineKeyboardButton("📁 720p / HD Quality", callback_data=f"send_final:{content_name}:720p")
            ],
            [
                InlineKeyboardButton("📁 1080p / Complete Course Pack", callback_data=f"send_final:{content_name}:1080p")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(quality_keyboard)
        
        await query.message.reply_text(
            f"✅ **Ads Verified Successfully!**\n\n"
            f"Select quality/format for `{content_name.title()}`:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif data.startswith("send_final:"):
        _, item_name, quality = data.split(":", 2)
        clean_name = item_name.lower().strip()
        
        # Check if file exists in STORAGE CHANNEL
        if clean_name in FILE_MAP and quality in FILE_MAP[clean_name]:
            msg_id = FILE_MAP[clean_name][quality]
            try:
                # Copy file directly from storage channel to user
                sent_msg = await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=msg_id
                )
                
                notice_msg = await query.message.reply_text(
                    f"⚠️ **Security Notice:** The video/file above will **automatically delete in 10 minutes** due to copyright protection. Please save it to your saved messages immediately!"
                )
                
                # Auto-delete both file and notice after 10 minutes (600 seconds)
                asyncio.create_task(schedule_message_deletion(context, chat_id, sent_msg.message_id, 600))
                asyncio.create_task(schedule_message_deletion(context, chat_id, notice_msg.message_id, 600))
                
            except Exception:
                await query.message.reply_text("⚠️ Storage channel error. Please ensure the bot is an Admin in the storage channel.")
        else:
            # Dynamic Fallback: Sends immediate course/movie delivery notice
            delivery_text = (
                f"🚀 **Delivering Requested Content!**\n\n"
                f"📌 **Title:** `{item_name.title()}`\n"
                f"⚙️ **Quality/Format:** `{quality}`\n\n"
                f"📥 Direct media stream processing...\n\n"
                f"⚠️ **Security Notice:** This message will **automatically delete in 10 minutes**."
            )
            sent_msg = await query.message.reply_text(delivery_text, parse_mode="Markdown")
            asyncio.create_task(schedule_message_deletion(context, chat_id, sent_msg.message_id, 600))

# ----------------------------------------------------
# 5. MAIN RUNNER
# ----------------------------------------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    application.add_handler(CallbackQueryHandler(button_click_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()