import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8928485887:AAFVf0z4IwvH-LkWGg4P6x58LuIF8L_pxG8"
ADMIN_CHAT_ID = 944048718

VIDEO_DATABASE = {
    "v1": {
        "title": "វីដេអូភាគពិសេស ទី ១",
        "link": "https://drive.google.com/file/d/1tn7W9nxL7vFTPrcRzk5fuYldwqSUIO1p/view?usp=drivesdk"
    }
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        video_id = context.args[0]
        if video_id in VIDEO_DATABASE:
            context.user_data["selected_video"] = video_id
            video_info = VIDEO_DATABASE[video_id]

            await update.message.reply_text(
                f"🎬 អ្នកបានជ្រើសរើស៖ **{video_info['title']}**\n\n"
                f"📌 សូមស្កេន KHQR ដើម្បីទូទាត់ប្រាក់ (៤,០០០៛ ឬ $1)។\n"
                f"📷 បន្ទាប់ពីផ្ទេរប្រាក់រួច សូមផ្ញើរូបភាពវិក្កយបត្រ (Payment Slip) ចូលមកទីនេះ។\n\n"
                f"⚡ ប្រព័ន្ធនឹងផ្ញើតំណភ្ជាប់ Google Drive នៃវីដេអូនេះជូនភ្លាមៗ!",
                parse_mode="Markdown"
            )
            return

    await update.message.reply_text(
        "👋 សួស្តី! សូមចូលទៅកាន់ Channel ហើយចុចលើ Link វីដេអូដែលអ្នកចង់ទស្សនាជាមុនសិន។"
    )

async def handle_slip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file_id = update.message.photo[-1].file_id

    selected_video_id = context.user_data.get("selected_video", "v1")
    video_info = VIDEO_DATABASE.get(selected_video_id, VIDEO_DATABASE["v1"])

    keyboard = [
        [InlineKeyboardButton(f"🎬 ចុចទីនេះដើម្បីទស្សនា {video_info['title']}", url=video_info["link"])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=(
            f"🎉 **ការទូទាត់ទទួលបានជោគជ័យ!**\n\n"
            f"នេះជាតំណភ្ជាប់ទស្សនា៖ **{video_info['title']}**\n"
            f"សូមចុចប៊ូតុងខាងក្រោមដើម្បីទស្សនាលើ Google Drive："
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    admin_caption = (
        f"🔔 **មានការបញ្ជាទិញវីដេអូថ្មី!**\n"
        f"🎬 វីដេអូ៖ {video_info['title']}\n"
        f"👤 ភ្ញៀវ៖ {user.full_name}\n"
        f"🆔 ID: `{user.id}`"
    )
    try:
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_file_id,
            caption=admin_caption,
            parse_mode="Markdown",
        )
    except Exception:
        pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_slip))
    app.run_polling()

if __name__ == "__main__":
    main()
