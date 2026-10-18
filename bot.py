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
# Updated Bot Token
BOT_TOKEN = "8973049098:AAGg8kO-C7uKzRjxpCddjlDAeanK_2mNQ_A"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Gemini API Key keessan asitti galchaa

# Adsterra Direct Links
AD_LINK_1 = "https://your-adsterra-link-1.com"
AD_LINK_2 = "https://your-adsterra-link-2.com"

# Storage Channel / Main Hub Link
MAIN_STORAGE_LINK = "https://t.me/your_storage_channel_link"

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

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
    welcome_text = (
        "🌟 **Welcome to DesiFlix Ultimate Content & Course Hub!** 🌟\n\n"
        "🎬 **Movies & Web Series:** Netflix, Amazon Prime, Hotstar, Zee5, etc.\n"
        "📚 **Courses & Skills:** DSA in Java/Python, Web Dev, Video Editing, Design, & more!\n\n"
        "👇 *Maqaa waan barbaaddanii asitti barreessaa!*"
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
        "⚠️ **Free Access Rule:** Beeksisa (Ads) lachuu xumuraa, san booda **'Proceed'** cuqaasaa!",
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
            f"Qulqullina/Format dooradhaa `{content_name.title()}` fiif:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif data.startswith("send_final:"):
        _, item_name, quality = data.split(":", 2)
        
        delivery_text = (
            f"🚀 **Here is your requested content!**\n\n"
            f"📌 **Title:** `{item_name.title()}`\n"
            f"⚙️ **Quality/Format:** `{quality}`\n\n"
            f"📥 [Click Here to Access / Download File]({MAIN_STORAGE_LINK})\n\n"
            f"⚠️ **Security Notice:** Ergaan kun **daqiiqaa 10 keessatti kan haqamu** ta'a."
        )
        
        sent_msg = await query.message.reply_text(delivery_text, parse_mode="Markdown")
        
        # 10-minute deletion
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