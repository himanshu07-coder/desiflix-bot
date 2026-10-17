import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "8973049098:AAFNqZ2M15kBZGFiLRST7tsgoEnYnWPD0UY"
TMDB_API_KEY = "f40f1b575b136f4946a922b5a08a55e0"

# Adsterra Smartlinks (Aap ek hi link double use kar sakte hain ya do alag links)
ADSTERRA_LINK_1 = "https://asiafilm.org/4/9fff5fa87f389039e2bb5eed7db9bdae"
ADSTERRA_LINK_2 = "https://asiafilm.org/4/9fff5fa87f389039e2bb5eed7db9bdae"

# Main Channel Username
CHANNEL_USERNAME = "@Desi_cinema_hub"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

WARNING_TEXT = (
    "\n\n⚠️ **IMPORTANT NOTICE:**\n"
    "Copyright issue ki waja se channel par video/file **10 Minutes mein delete** kar di jayegi!\n"
    "📌 *Turant video ko apne Saved Messages mein forward/save kar lein.*"
)

# Start Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to All-in-One Custom Search Hub!**\n\n"
        "🎬 **Movies & Series:** Select Quality (480p, 720p, 1080p) & Language!\n"
        "💻 **Courses & Skills:** Select Teacher, Language & Batch!\n\n"
        "👉 Bas apna item search karein!"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# Search Handler
async def smart_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.strip()
    query_lower = user_query.lower()
    
    is_course = any(word in query_lower for word in ['course', 'learn', 'tutorial', 'python', 'java', 'coding', 'editing', 'skill', 'playlist', 'dsa'])
    
    if is_course:
        # COURSE FLOW
        text = (
            f"🎓 **Course Found:** `{user_query}`\n\n"
            f"Pehle Step 1 Ad complete karein, phir Teacher & Language select karein."
        )
        keyboard = [
            [InlineKeyboardButton("🔓 Step 1: Unlock Course Filters (Ad 1)", url=ADSTERRA_LINK_1)],
            [InlineKeyboardButton("⚡ Next: Select Teacher & Language", callback_data=f"course_filter|{user_query}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
        
    else:
        # MOVIE FLOW
        tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={user_query}"
        try:
            res = requests.get(tmdb_url).json()
            if res.get('results'):
                movie = res['results'][0]
                title = movie.get('title', user_query)
                poster_path = movie.get('poster_path')
                
                text = (
                    f"🎬 **Movie Found:** `{title}`\n\n"
                    f"Pehle Step 1 Ad complete karein, phir Video Quality (480p/720p/1080p) choose karein."
                )
                keyboard = [
                    [InlineKeyboardButton("🔓 Step 1: Unlock Quality Options (Ad 1)", url=ADSTERRA_LINK_1)],
                    [InlineKeyboardButton("⚡ Next: Select Quality & Audio", callback_data=f"movie_filter|{title}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if poster_path:
                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                    await update.message.reply_photo(photo=poster_url, caption=text, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                # Fallback Movie/Series
                text = f"🎬 **Content Found:** `{user_query}`\n\nPehle Step 1 Ad complete karein."
                keyboard = [
                    [InlineKeyboardButton("🔓 Step 1: Unlock Options (Ad 1)", url=ADSTERRA_LINK_1)],
                    [InlineKeyboardButton("⚡ Next: Select Quality & Audio", callback_data=f"movie_filter|{user_query}")]
                ]
                await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except Exception as e:
            logging.error(f"Search Error: {e}")

# Callback Handler (Buttons Filtering)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("movie_filter"):
        title = data.split("|")[1]
        text = (
            f"🎬 **Select Video Quality & Audio for:** `{title}`\n\n"
            f"Apni choice select karein:"
        )
        keyboard = [
            [InlineKeyboardButton("🔊 Hindi Dual Audio - 480p (300MB)", callback_data=f"final_get|{title}|480p")],
            [InlineKeyboardButton("🔊 Hindi Dual Audio - 720p (800MB)", callback_data=f"final_get|{title}|720p")],
            [InlineKeyboardButton("🔊 Multi-Audio - 1080p Full HD (2GB)", callback_data=f"final_get|{title}|1080p")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("course_filter"):
        title = data.split("|")[1]
        text = (
            f"🎓 **Select Course Teacher / Batch for:** `{title}`\n\n"
            f"Apni preference select karein:"
        )
        keyboard = [
            [InlineKeyboardButton("👨‍🏫 Complete Hindi Full Course (Best Teacher)", callback_data=f"final_get|{title}|Hindi")],
            [InlineKeyboardButton("👨‍💻 English Complete Playlist & Notes", callback_data=f"final_get|{title}|English")],
            [InlineKeyboardButton("🚀 Beginner to Advanced Live Batch", callback_data=f"final_get|{title}|Advanced")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data.startswith("final_get"):
        parts = data.split("|")
        item = parts[1]
        selected_option = parts[2]
        
        text = (
            f"✅ **Your Selection Ready:** `{item}` ({selected_option})\n\n"
            f"👇 Video/File access karne ke liye Final Step Ad complete karein aur channel par file paayein!"
            f"{WARNING_TEXT}"
        )
        keyboard = [
            [InlineKeyboardButton("📥 Step 2: Final Link Unlock (Ad 2)", url=ADSTERRA_LINK_2)],
            [InlineKeyboardButton("📢 Get File From Official Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), smart_search))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("🚀 Double Ad & Filter Selection Bot Running Successfully!")
    app.run_polling()

if __name__ == '__main__':
    main()