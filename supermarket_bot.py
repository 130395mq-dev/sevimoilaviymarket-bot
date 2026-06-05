import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE")
ORDER_LINK = "https://b2b.moysklad.ru/public/Bya8IC3N6odI"
OPERATOR_PHONE = "+998900769441"
VIDEO_URL = os.environ.get("VIDEO_URL", "YOUR_VIDEO_FILE_ID_OR_URL")

VIDEO_CAPTION = "Assalomu alaykum! Ushbu qo'llanma orqali buyurtma berishni o'rganishingiz mumkin...\n\nQuyidagi tugmalardan birini tanlang 👇"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Buyurtma Boshlash", callback_data="order")],
        [InlineKeyboardButton("📞 Operator bilan Bog'lanish", callback_data="operator")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await update.message.reply_video(
            video=VIDEO_URL,
            caption=VIDEO_CAPTION,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Video yuborishda xatolik: {e}")
        await update.message.reply_text(VIDEO_CAPTION, reply_markup=reply_markup)


async def get_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        file_id = update.message.video.file_id
        logger.info(f"VIDEO FILE_ID: {file_id}")
        await update.message.reply_text(f"Video file_id: {file_id}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "order":
        keyboard = [[InlineKeyboardButton("🔗 Buyurtma sahifasiga o'tish", url=ORDER_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("🛍 Buyurtma berish uchun quyidagi tugmani bosing:", reply_markup=reply_markup)

    elif query.data == "operator":
        await query.message.reply_text(
            f"📞 Operator bilan bog'lanish:\n\n"
            f"📱 Telefon: {OPERATOR_PHONE}\n\n"
            f"Ish vaqti: 08:00 - 00:00 (Dush-Yak)"
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, get_video_id))
    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
