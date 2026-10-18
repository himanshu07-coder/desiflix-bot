import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ----------------------------------------------------
# 1. RENDER PORT SERVER (Keep-Alive)
# ----------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"DesiFlix AI Bot is Live and Running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ----------------------------------------------------
# 2. CONFIGURATION & DATABASE SETUP
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAFOEeKA_omSf8a1eXdg-1NU6_VgEJ18hPc"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"  # Apni Google AI Studio ki key yahan daalein
AD_LINK_1 = "https://your-adsterra-direct-link.com"  # Aapka Adsterra Smartlink

# Aapka Private Storage Channel ID jahan saari video files uploaded hain
STORAGE_CHANNEL_ID = -1001234567890 

# Movie / Series Database (Movie Name -> Storage Channel Message IDs for each Quality)
# Message ID woh number hai jo channel post ke link ke end mein hota hai
MOVIE_DATABASE = {
    "bigg boss season 20": {"480p": 101, "720p": 102, "1080p": 103},
    "kgf chapter 2": {"480p": 10, "720p": 11, "1080p": 12}
}

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# ----------------------------------------------------
# 3. HANDLERS & AI LOGIC
# ----------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to DesiFlix Media Bot!**\n\n"
        "🎬 Kisi bhi movie, web series, lecture ya course ka naam yahan type karein, bot turant quality ke sath file provide karega."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    
    # Gemini AI se query clean aur spelling correct karna
    try:
        prompt = f"Extract clean movie/series title in lowercase from: '{user_query}'. Return ONLY the clean title."
        response = ai_model.generate_content(prompt)
        clean_title = response.text.strip().lower()
    except Exception:
        clean_title = user_query.lower()

    # Step 1: Adsterra unlock button + Next quality button
    keyboard = [
        [InlineKeyboardButton("🔓 Step 1: Unlock Quality Options (Ad)", url=AD_LINK_1)],
        [InlineKeyboardButton("⚡ Next: Select Quality & Get File", callback_data=f"show_q:{clean_title}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎬 **Found Request:** `{clean_title.title()}`\n\n"
        "Pehle Step 1 Ad complete karein, phir 'Next' dabakar apni pasand ki Video Quality choose karein.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    target_chat_id = query.message.chat_id  # Jahan user ne request bheji thi wahi channel/group
    
    if data.startswith("show_q:"):
        movie_name = data.split("show_q:")[1]
        
        quality_keyboard = [
            [
                InlineKeyboardButton("📁 480p", callback_data=f"sendfile:{movie_name}:480p"),
                InlineKeyboardButton("📁 720p", callback_data=f"sendfile:{movie_name}:720p")
            ],
            [
                InlineKeyboardButton("📁 1080p", callback_data=f"sendfile:{movie_name}:1080p")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(quality_keyboard)
        
        await query.message.reply_text(
            f"✅ **Select Video Quality for {movie_name.title()}:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif data.startswith("sendfile:"):
        _, movie_name, quality = data.split(":")
        
        if movie_name in MOVIE_DATABASE and quality in MOVIE_DATABASE[movie_name]:
            msg_id = MOVIE_DATABASE[movie_name][quality]
            
            await query.message.reply_text("⏳ **Sending Video File instantly to this channel...**")
            
            try:
                # Storage channel se direct video file copy karke user ke channel par post karna
                await context.bot.copy_message(
                    chat_id=target_chat_id,
                    from_chat_id=STORAGE_CHANNEL_ID,
                    message_id=msg_id
                )
            except Exception as e:
                await query.message.reply_text("⚠️ File sending failed. Ensure Bot is Admin in this channel and Storage ID is correct.")
        else:
            await query.message.reply_text(
                f"🎬 **{movie_name.title()} ({quality})** ki file jald hi update ki jayegi! Kripya thodi der baad try karein."
            )

# ----------------------------------------------------
# 4. MAIN BOT RUNNER
# ----------------------------------------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    application.add_handler(CallbackQueryHandler(button_click_handler))

    application.run_polling()

if __name__ == "__main__":
    main()