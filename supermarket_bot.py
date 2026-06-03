import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==============================
# TOKEN - Railway Environment Variable orqali
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8888202399:AAEX6IY4vVleS2AGYcYocCL61LVqcYikLuU")

# ==============================
# SOZLAMALAR
# ==============================
ORDER_LINK = "https://b2b.moysklad.ru/public/Bya8IC3N6odI"
OPERATOR_PHONE = "+998900769441"

# Video - Telegram file_id yoki to'g'ridan-to'g'ri .mp4 linki
VIDEO_URL = os.environ.get("VIDEO_URL", "YOUR_VIDEO_FILE_ID_OR_URL")

VIDEO_CAPTION = """
Assalomu alaykum! Ushbu qo'llanma orqali buyurtma berishni o'rganishingiz mumkin...

Quyidagi tugmalardan birini tanlang 👇
"""

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==============================
# /start KOMANDASI
# ==============================
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
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception as e:
        # Video yuklanmasa, matn bilan javob beradi
        logger.error(f"Video yuborishda xatolik: {e}")
        await update.message.reply_text(
            VIDEO_CAPTION,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


# ==============================
# TUGMALAR ISHLOV BERISH
# ==============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "order":
        keyboard = [[InlineKeyboardButton("🔗 Buyurtma sahifasiga o'tish", url=ORDER_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "🛍 *Buyurtma berish uchun quyidagi tugmani bosing:*",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    elif query.data == "operator":
        await query.message.reply_text(
            f"📞 *Operator bilan bog'lanish:*\n\n"
            f"📱 Telefon: `{OPERATOR_PHONE}`\n\n"
            f"Ish vaqti: 09:00 - 18:00 (Dush-Shan)",
            parse_mode="Markdown"
        )


# ==============================
# MAIN
# ==============================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
