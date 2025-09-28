import os
from yt_dlp import YoutubeDL
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    filters, ConversationHandler
)

# ----------------------------
# CONFIGURATION
# ----------------------------
BOT_TOKEN = "8334790545:AAEYzJdvZT1M5rcpgCWD_sX08LtUXiKqd10"
FFMPEG_PATH = r"C:\ffmpeg\bin"
DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ----------------------------
# STATES
# ----------------------------
CHOOSING_FORMAT, CHOOSING_QUALITY, DOWNLOADING = range(3)
user_data_temp = {}

# ----------------------------
# START COMMAND
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Send me a YouTube link and I will download it for you. made by Samarth B"
    )

# ----------------------------
# HANDLE YOUTUBE LINK
# ----------------------------
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ This doesn't look like a valid YouTube URL.")
        return ConversationHandler.END

    user_data_temp['url'] = url
    keyboard = [["MP4 Video", "MP3 Audio"]]
    await update.message.reply_text(
        "Choose format:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return CHOOSING_FORMAT

# ----------------------------
# HANDLE FORMAT CHOICE
# ----------------------------
async def choose_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    user_data_temp['format'] = choice

    if choice == "MP4 Video":
        keyboard = [["360p", "480p"], ["720p", "1080p", "choose by checking the vid quality"]]
    else:
        keyboard = [["128kbps", "192kbps", "320kbps"]]

    await update.message.reply_text(
        "Choose quality:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return CHOOSING_QUALITY

# ----------------------------
# PROGRESS HOOK
# ----------------------------
def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        eta = d.get('_eta_str', '').strip()
        try:
            message = f"⏳ Downloading: {percent} | ETA: {eta}"
            if not hasattr(progress_hook, "last_message"):
                progress_hook.last_message = None
            # Only edit if changed to reduce spam
            if message != getattr(progress_hook, "last_message", None):
                progress_hook.last_message = message
        except:
            pass

# ----------------------------
# DOWNLOAD FUNCTION
# ----------------------------
def download_youtube(url, fmt, quality):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'ffmpeg_location': FFMPEG_PATH,
        'noplaylist': True,
        'quiet': True,
        'socket_timeout': 30,
        'http_chunk_size': 10485760,
        'progress_hooks': [progress_hook]
    }

    if fmt == "MP4 Video":
        height_map = {"360p":360, "480p":480, "720p":720, "1080p":1080}
        ydl_opts['format'] = f'bestvideo[height<={height_map.get(quality,720)}]+bestaudio/best[height<={height_map.get(quality,720)}]'
    else:
        bitrate_map = {"128kbps":"128", "192kbps":"192", "320kbps":"320"}
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate_map.get(quality, '192'),
        }]

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if fmt == "MP3 Audio":
            filename = os.path.splitext(filename)[0] + ".mp3"
    return filename

# ----------------------------
# HANDLE QUALITY CHOICE
# ----------------------------
async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quality = update.message.text
    user_data_temp['quality'] = quality
    await update.message.reply_text("⏳ Download started...")

    try:
        file_path = download_youtube(
            user_data_temp['url'],
            user_data_temp['format'],
            user_data_temp['quality']
        )

        # Send file to user
        if user_data_temp['format'] == "MP4 Video":
            await update.message.reply_video(open(file_path, 'rb'))
        else:
            await update.message.reply_document(open(file_path, 'rb'))

        os.remove(file_path)
        await update.message.reply_text("✅ Done! Made by Samarth")
    except Exception as e:
        await update.message.reply_text(f" Downloading: {e}\n Wait for seconds while i download it for you.")
    return ConversationHandler.END

# ----------------------------
# CANCEL HANDLER
# ----------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled. Please Type (/start) ")
    return ConversationHandler.END

# ----------------------------
# MAIN BOT FUNCTION
# ----------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)],
        states={
            CHOOSING_FORMAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_format)],
            CHOOSING_QUALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_quality)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()
