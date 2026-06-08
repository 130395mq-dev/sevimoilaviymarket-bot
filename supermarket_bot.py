import logging
import os
import io
import aiohttp
import barcode
from barcode.writer import ImageWriter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE")
ORDER_LINK = "https://b2b.moysklad.ru/public/Bya8IC3N6odI"
OPERATOR_PHONE = "+998900769441"
VIDEO_URL = os.environ.get("VIDEO_URL", "YOUR_VIDEO_FILE_ID")
MS_TOKEN = os.environ.get("MS_TOKEN", "a147c1756372f5ed43ead9c6b77d1b8ab56ae35a")
MS_URL = "https://api.moysklad.ru/api/remap/1.2"

user_phones = {}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================
# TELEFON VARIANTLARI
# ==============================
def phone_variants(phone: str):
    digits = ''.join(filter(str.isdigit, phone))
    variants = set()
    variants.add(phone.strip())
    variants.add(f"+{digits}")
    variants.add(digits)
    if digits.startswith("998") and len(digits) == 12:
        variants.add(digits[3:])
        variants.add(digits[2:])
    if len(digits) == 9:
        variants.add(f"998{digits}")
        variants.add(f"+998{digits}")
    if len(digits) == 10 and digits.startswith("0"):
        variants.add(f"998{digits[1:]}")
        variants.add(f"+998{digits[1:]}")
    return list(variants)


# ==============================
# MOYSKLAD API
# ==============================
async def get_customer_by_phone(phone: str):
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    variants = phone_variants(phone)
    logger.info(f"Qidirilayotgan variantlar: {variants}")

    async with aiohttp.ClientSession() as session:
        for variant in variants:
            async with session.get(
                f"{MS_URL}/entity/counterparty",
                headers=headers,
                params={"filter": f"phone={variant}", "limit": 1}
            ) as resp:
                data = await resp.json()
                rows = data.get("rows", [])
                if rows:
                    logger.info(f"Topildi: {variant}")
                    return rows[0]

        digits = ''.join(filter(str.isdigit, phone))
        short = digits[-9:] if len(digits) >= 9 else digits
        async with session.get(
            f"{MS_URL}/entity/counterparty",
            headers=headers,
            params={"search": short, "limit": 10}
        ) as resp:
            data = await resp.json()
            rows = data.get("rows", [])
            for row in rows:
                row_phones = row.get("phone", "") or ""
                row_digits = ''.join(filter(str.isdigit, row_phones))
                if short in row_digits:
                    logger.info(f"Search orqali topildi: {row_phones}")
                    return row

    return None


async def get_customer_bonus(customer_id: str):
    """SEVIMLI BONUS maxsus maydonini olish"""
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{MS_URL}/entity/counterparty/{customer_id}",
            headers=headers,
        ) as resp:
            data = await resp.json()
            # Bonus points
            bonus = data.get("bonusPoints", 0)
            # Maxsus maydonlar (attributes)
            attributes = data.get("attributes", [])
            for attr in attributes:
                name = attr.get("name", "").lower()
                if "bonus" in name or "балл" in name or "ball" in name:
                    bonus = attr.get("value", bonus)
                    break
            return bonus


async def get_customer_purchases(customer_id: str):
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{MS_URL}/entity/retaildemand",
            headers=headers,
            params={
                "filter": f"agent={MS_URL}/entity/counterparty/{customer_id}",
                "limit": 10,
                "order": "moment,desc"
            }
        ) as resp:
            data = await resp.json()
            return data.get("rows", [])


# ==============================
# SHTRIX-KOD GENERATSIYA (Code128)
# ==============================
def generate_barcode(code: str) -> io.BytesIO:
    buf = io.BytesIO()
    CODE128 = barcode.get_barcode_class('code128')
    bc = CODE128(code, writer=ImageWriter())
    bc.write(buf, options={
        "module_width": 0.4,
        "module_height": 15.0,
        "font_size": 10,
        "text_distance": 5,
        "quiet_zone": 6.5,
        "write_text": True,
        "background": "white",
        "foreground": "black",
    })
    buf.seek(0)
    return buf


# ==============================
# MENYULAR
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
        logger.error(f"Video xatolik: {e}")
        await update.message.reply_text(VIDEO_CAPTION, reply_markup=main_menu_keyboard())


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
        await query.message.reply_text("🛍 Buyurtma berish uchun:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "operator":
        await query.message.reply_text(
            f"📞 Operator bilan bog'lanish:\n\n"
            f"📱 Telefon: {OPERATOR_PHONE}\n\n"
            f"Ish vaqti: 08:00 - 00:00 (Dush-Yak)"
        )

    elif query.data == "card":
        if user_id in user_phones:
            await show_card(query.message, user_phones[user_id])
        else:
            context.user_data["waiting_phone"] = True
            await query.message.reply_text(
                "📱 Kassada ro'yxatdan o'tgan telefon raqamingizni kiriting:\n\nMisol: +998901234567"
            )

    elif query.data == "purchases":
        if user_id in user_phones:
            await show_purchases(query.message, user_phones[user_id])

    elif query.data == "change_phone":
        if user_id in user_phones:
            del user_phones[user_id]
        context.user_data["waiting_phone"] = True
        await query.message.reply_text("📱 Yangi telefon raqamingizni kiriting:")

    elif query.data == "back_menu":
        await query.message.reply_text("Asosiy menyu:", reply_markup=main_menu_keyboard())


# ==============================
# KARTA
# ==============================
async def show_card(message, phone: str):
    await message.reply_text("⏳ Ma'lumot yuklanmoqda...")
    customer = await get_customer_by_phone(phone)

    if not customer:
        await message.reply_text(
            f"❌ {phone} raqamli mijoz topilmadi.\n"
            f"Kassada ro'yxatdan o'tganmisiz?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Raqamni o'zgartirish", callback_data="change_phone")]
            ])
        )
        return

    name = customer.get("name", "Noma'lum")
    customer_id = customer.get("id", "")
    discount_card = customer.get("discountCardNumber", "") or ""
    barcode_data = discount_card if discount_card else customer_id[:13]

    # Bonus ballarni olish
    bonus = await get_customer_bonus(customer_id)

    barcode_buf = generate_barcode(barcode_data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Xaridlarim", callback_data="purchases")],
        [InlineKeyboardButton("🔄 Raqamni o'zgartirish", callback_data="change_phone")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_menu")],
    ])

    await message.reply_photo(
        photo=barcode_buf,
        caption=f"🎁 Nakopital Karta\n\n"
                f"👤 Ism: {name}\n"
                f"📱 Telefon: {phone}\n"
                f"🃏 Karta raqami: {barcode_data}\n"
                f"⭐ Bonus ballar: {bonus}\n\n"
                f"Shtrix-kodni kassirga ko'rsating!",
        reply_markup=keyboard
    )


# ==============================
# XARIDLAR
# ==============================
async def show_purchases(message, phone: str):
    await message.reply_text("⏳ Xaridlar yuklanmoqda...")
    customer = await get_customer_by_phone(phone)

    if not customer:
        await message.reply_text("❌ Mijoz topilmadi.")
        return

    customer_id = customer.get("id", "")
    purchases = await get_customer_purchases(customer_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Kartam", callback_data="card")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_menu")],
    ])

    if not purchases:
        await message.reply_text("🛍 Xaridlar tarixi bo'sh.", reply_markup=keyboard)
        return

    text = "🛍 Oxirgi xaridlaringiz:\n\n"
    for i, p in enumerate(purchases[:10], 1):
        moment = p.get("moment", "")[:10]
        summa = p.get("sum", 0) / 100
        text += f"{i}. 📅 {moment} — {summa:,.0f} so'm\n"

    await message.reply_text(text, reply_markup=keyboard)


# ==============================
# MATN QABUL QILISH
# ==============================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.user_data.get("waiting_phone"):
        return

    phone = update.message.text.strip()
    digits = ''.join(filter(str.isdigit, phone))

    if len(digits) < 9:
        await update.message.reply_text("❌ Noto'g'ri format. Misol: +998901234567 yoki 901234567")
        return

    context.user_data["waiting_phone"] = False
    user_phones[user_id] = phone
    await show_card(update.message, phone)


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
