import logging
import os
import qrcode
import io
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE")
ORDER_LINK = "https://b2b.moysklad.ru/public/Bya8IC3N6odI"
OPERATOR_PHONE = "+998900769441"
VIDEO_URL = os.environ.get("VIDEO_URL", "YOUR_VIDEO_FILE_ID")
MS_TOKEN = os.environ.get("MS_TOKEN", "a147c1756372f5ed43ead9c6b77d1b8ab56ae35a")
MS_URL = "https://api.moysklad.ru/api/remap/1.2"

# Foydalanuvchi telefon raqamlarini saqlash (xotira)
user_phones = {}

# ConversationHandler holatlari
ASK_PHONE = 1

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================
# MOYSKLAD API FUNKSIYALAR
# ==============================
async def get_customer_by_phone(phone: str):
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{MS_URL}/entity/counterparty",
            headers=headers,
            params={"filter": f"phone={phone}", "limit": 1}
        ) as resp:
            data = await resp.json()
            rows = data.get("rows", [])
            if rows:
                return rows[0]
            # Ikkinchi urinish — +998 formatisiz
            async with session.get(
                f"{MS_URL}/entity/counterparty",
                headers=headers,
                params={"search": clean_phone, "limit": 5}
            ) as resp2:
                data2 = await resp2.json()
                rows2 = data2.get("rows", [])
                return rows2[0] if rows2 else None


async def get_customer_operations(customer_id: str):
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{MS_URL}/entity/retaildemand",
            headers=headers,
            params={"filter": f"agent={MS_URL}/entity/counterparty/{customer_id}", "limit": 10, "order": "moment,desc"}
        ) as resp:
            data = await resp.json()
            return data.get("rows", [])


def generate_qr(data: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ==============================
# ASOSIY MENYU
# ==============================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Buyurtma Boshlash", callback_data="order")],
        [InlineKeyboardButton("🎁 Nakopital Karta", callback_data="card")],
        [InlineKeyboardButton("📞 Operator bilan Bog'lanish", callback_data="operator")],
    ])


VIDEO_CAPTION = "Assalomu alaykum! Ushbu qo'llanma orqali buyurtma berishni o'rganishingiz mumkin...\n\nQuyidagi tugmalardan birini tanlang 👇"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_video(
            video=VIDEO_URL,
            caption=VIDEO_CAPTION,
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Video yuborishda xatolik: {e}")
        await update.message.reply_text(VIDEO_CAPTION, reply_markup=main_menu_keyboard())


# ==============================
# VIDEO FILE_ID OLISH
# ==============================
async def get_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        file_id = update.message.video.file_id
        logger.info(f"VIDEO FILE_ID: {file_id}")
        await update.message.reply_text(f"Video file_id: {file_id}")


# ==============================
# TUGMALAR
# ==============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "order":
        keyboard = [[InlineKeyboardButton("🔗 Buyurtma sahifasiga o'tish", url=ORDER_LINK)]]
        await query.message.reply_text("🛍 Buyurtma berish uchun quyidagi tugmani bosing:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "operator":
        await query.message.reply_text(
            f"📞 Operator bilan bog'lanish:\n\n"
            f"📱 Telefon: {OPERATOR_PHONE}\n\n"
            f"Ish vaqti: 08:00 - 00:00 (Dush-Yak)"
        )

    elif query.data == "card":
        if user_id in user_phones:
            await show_card(query, user_phones[user_id])
        else:
            await query.message.reply_text("📱 Telefon raqamingizni kiriting:\n\nMisol: +998901234567")
            context.user_data["waiting_phone"] = True

    elif query.data == "purchases":
        if user_id in user_phones:
            await show_purchases(query, user_phones[user_id])

    elif query.data == "back_menu":
        await query.message.reply_text("Asosiy menyu:", reply_markup=main_menu_keyboard())


# ==============================
# KARTA KO'RSATISH
# ==============================
async def show_card(query, phone: str):
    await query.message.reply_text("⏳ Ma'lumot yuklanmoqda...")
    customer = await get_customer_by_phone(phone)

    if not customer:
        await query.message.reply_text(
            f"❌ {phone} raqamli mijoz topilmadi.\n\nRaqamni qayta kiriting:",
        )
        return

    name = customer.get("name", "Noma'lum")
    bonus = customer.get("bonusPoints", 0)
    customer_id = customer.get("id", "")
    code = customer.get("code", customer_id[:8])

    # QR kod generatsiya
    qr_buf = generate_qr(f"sevimli:{customer_id}")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Xaridlarim", callback_data="purchases")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_menu")],
    ])

    await query.message.reply_photo(
        photo=qr_buf,
        caption=f"🎁 Nakopital Karta\n\n"
                f"👤 Ism: {name}\n"
                f"📱 Telefon: {phone}\n"
                f"⭐ Bonus ballar: {bonus}\n\n"
                f"QR kodni kassirga ko'rsating!",
        reply_markup=keyboard
    )


# ==============================
# XARIDLAR
# ==============================
async def show_purchases(query, phone: str):
    await query.message.reply_text("⏳ Xaridlar yuklanmoqda...")
    customer = await get_customer_by_phone(phone)

    if not customer:
        await query.message.reply_text("❌ Mijoz topilmadi.")
        return

    customer_id = customer.get("id", "")
    purchases = await get_customer_operations(customer_id)

    if not purchases:
        await query.message.reply_text("🛍 Xaridlar tarixi bo'sh.")
        return

    text = "🛍 Oxirgi xaridlaringiz:\n\n"
    for i, p in enumerate(purchases[:10], 1):
        moment = p.get("moment", "")[:10]
        summa = p.get("sum", 0) / 100
        text += f"{i}. 📅 {moment} — {summa:,.0f} so'm\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Kartam", callback_data="card")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_menu")],
    ])

    await query.message.reply_text(text, reply_markup=keyboard)


# ==============================
# TELEFON RAQAM QABUL QILISH
# ==============================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if context.user_data.get("waiting_phone"):
        phone = update.message.text.strip()
        if not (phone.startswith("+") and len(phone) >= 10):
            await update.message.reply_text("❌ Noto'g'ri format. Misol: +998901234567")
            return

        user_phones[user_id] = phone
        context.user_data["waiting_phone"] = False

        customer = await get_customer_by_phone(phone)
        if not customer:
            await update.message.reply_text(
                f"❌ {phone} raqamli mijoz topilmadi.\n"
                f"Kassada ro'yxatdan o'tganmisiz?\n\n"
                f"Qayta kiriting yoki /start bosing."
            )
            del user_phones[user_id]
            return

        name = customer.get("name", "")
        bonus = customer.get("bonusPoints", 0)
        customer_id = customer.get("id", "")

        qr_buf = generate_qr(f"sevimli:{customer_id}")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍 Xaridlarim", callback_data="purchases")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_menu")],
        ])

        await update.message.reply_photo(
            photo=qr_buf,
            caption=f"🎁 Nakopital Karta\n\n"
                    f"👤 Ism: {name}\n"
                    f"📱 Telefon: {phone}\n"
                    f"⭐ Bonus ballar: {bonus}\n\n"
                    f"QR kodni kassirga ko'rsating!",
            reply_markup=keyboard
        )


# ==============================
# MAIN
# ==============================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, get_video_id))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
