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
        self.wfile.write(b"DesiFlix Universal Hub is Active!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ----------------------------------------------------
# 2. CONFIGURATION SETUP
# ----------------------------------------------------
BOT_TOKEN = "8973049098:AAGg8kO-C7uKzRjxpCddjlDAeanK_2mNQ_A"
ADSTERRA_LINK = "https://asiafilm.org/4/9fff5fa87f389039e2bb5eed7db9bdae"
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
    chat_id = query.message.chat_id
    
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
        
        sent_msg = await query.message.reply_text(caption_text, reply_markup=timer_btn, parse_mode="Markdown")
        asyncio.create_task(schedule_message_deletion(context, chat_id, sent_msg.message_id, 600))

# ----------------------------------------------------
# 5. MAIN RUNNER
# ----------------------------------------------------
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    application.add_handler(CallbackQueryHandler(button_click_handler))

    # drop_pending_updates=True lagane se purane conflict errors solve ho jayenge
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()