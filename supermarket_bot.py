import logging
import os
import io
import asyncpg
import aiohttp
import barcode
from barcode.writer import ImageWriter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE")
ORDER_LINK = "https://b2b.moysklad.ru/public/Bya8IC3N6odI"
OPERATOR_PHONE = "+998900769441"
VIDEO_URL = os.environ.get("VIDEO_URL", "YOUR_VIDEO_FILE_ID")
MS_TOKEN = os.environ.get("MS_TOKEN", "a147c1756372f5ed43ead9c6b77d1b8ab56ae35a")
MS_URL = "https://api.moysklad.ru/api/remap/1.2"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:DKRngECbMYhNJQIjSUZPCPOtdKLhFrrk@postgres.railway.internal:5432/railway")

ADMIN_IDS = [7093521451, 5505113497]

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

db_pool = None

# ==============================
# TILLAR
# ==============================
TEXTS = {
    "uz": {
        "welcome": "Assalomu alaykum! Sevimli Market botiga xush kelibsiz!\n\nTilni tanlang 👇",
        "choose_lang": "Tilni tanlang:",
        "main_menu": "Quyidagi tugmalardan birini tanlang 👇",
        "video": "📹 Video Qo'llanma",
        "order": "🛍 Buyurtma Boshlash",
        "card": "🎁 Nakopital Karta",
        "operator": "📞 Operator",
        "admin_panel": "👨‍💼 Admin Panel",
        "order_btn": "🔗 Buyurtma sahifasiga o'tish",
        "order_text": "🛍 Buyurtma berish uchun:",
        "operator_text": "📞 Operator bilan bog'lanish:\n\n📱 Telefon: {phone}\n\nIsh vaqti: 08:00 - 00:00 (Dush-Yak)",
        "enter_phone": "📱 Kassada ro'yxatdan o'tgan telefon raqamingizni kiriting:\n\nMisol: +998901234567",
        "wrong_phone": "❌ Noto'g'ri format. Misol: +998901234567 yoki 901234567",
        "loading": "⏳ Ma'lumot yuklanmoqda...",
        "not_found": "❌ {phone} raqamli mijoz topilmadi.\nKassada ro'yxatdan o'tganmisiz?\n\nRaqamni qayta kiriting:",
        "card_caption": "🎁 Nakopital Karta\n\n👤 Ism: {name}\n📱 Telefon: {phone}\n🃏 Karta raqami: {card}\n⭐ Bonus ballar: {bonus}\n\nShtrix-kodni kassirga ko'rsating!",
        "my_purchases": "🛍 Xaridlarim",
        "change_phone": "🔄 Raqamni o'zgartirish",
        "purchases_loading": "⏳ Xaridlar yuklanmoqda...",
        "purchases_empty": "🛍 Xaridlar tarixi bo'sh.",
        "purchases_title": "🛍 Oxirgi xaridlaringiz:\n\n",
        "my_card": "🎁 Kartam",
        "enter_new_phone": "📱 Yangi telefon raqamingizni kiriting:",
        "video_caption": "Ushbu qo'llanma orqali buyurtma berishni o'rganishingiz mumkin...",
        "lang_changed": "Til o'zgartirildi! 🇺🇿",
    },
    "ru": {
        "welcome": "Добро пожаловать в бот Sevimli Market!\n\nВыберите язык 👇",
        "choose_lang": "Выберите язык:",
        "main_menu": "Выберите одну из кнопок ниже 👇",
        "video": "📹 Видео инструкция",
        "order": "🛍 Оформить заказ",
        "card": "🎁 Карта накопителя",
        "operator": "📞 Оператор",
        "admin_panel": "👨‍💼 Admin Panel",
        "order_btn": "🔗 Перейти к заказу",
        "order_text": "🛍 Для оформления заказа:",
        "operator_text": "📞 Связаться с оператором:\n\n📱 Телефон: {phone}\n\nРабочее время: 08:00 - 00:00 (Пн-Вс)",
        "enter_phone": "📱 Введите номер телефона, которым вы зарегистрированы на кассе:\n\nПример: +998901234567",
        "wrong_phone": "❌ Неверный формат. Пример: +998901234567 или 901234567",
        "loading": "⏳ Загрузка данных...",
        "not_found": "❌ Клиент с номером {phone} не найден.\nВы зарегистрированы на кассе?\n\nВведите номер ещё раз:",
        "card_caption": "🎁 Карта накопителя\n\n👤 Имя: {name}\n📱 Телефон: {phone}\n🃏 Номер карты: {card}\n⭐ Бонусные баллы: {bonus}\n\nПокажите штрих-код кассиру!",
        "my_purchases": "🛍 Мои покупки",
        "change_phone": "🔄 Изменить номер",
        "purchases_loading": "⏳ Загрузка покупок...",
        "purchases_empty": "🛍 История покупок пуста.",
        "purchases_title": "🛍 Последние покупки:\n\n",
        "my_card": "🎁 Моя карта",
        "enter_new_phone": "📱 Введите новый номер телефона:",
        "video_caption": "С помощью этой инструкции вы узнаете как оформить заказ...",
        "lang_changed": "Язык изменён! 🇷🇺",
    }
}


# ==============================
# DATABASE
# ==============================
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                phone TEXT,
                lang TEXT DEFAULT 'uz',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        # lang ustunini qo'shish (eski bazada bo'lmasa)
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT 'uz'")
        except:
            pass
    logger.info("Database tayyor!")


async def get_user(user_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("SELECT phone, lang FROM users WHERE user_id = $1", user_id)


async def save_user_phone(user_id: int, phone: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, phone) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET phone = $2
        """, user_id, phone)


async def save_user_lang(user_id: int, lang: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, lang) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET lang = $2
        """, user_id, lang)


async def delete_user_phone(user_id: int):
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET phone = NULL WHERE user_id = $1", user_id)


async def get_all_user_ids():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM users")
        return [row["user_id"] for row in rows]


async def get_user_lang(user_id: int):
    user = await get_user(user_id)
    return user["lang"] if user and user["lang"] else "uz"


def t(lang: str, key: str, **kwargs):
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


# ==============================
# KEYBOARD
# ==============================
def main_reply_keyboard(lang: str, is_admin: bool = False):
    buttons = [
        [t(lang, "video")],
        [t(lang, "order"), t(lang, "card")],
        [t(lang, "operator")],
    ]
    if is_admin:
        buttons.append([t(lang, "admin_panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ])


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
                    return row

    return None


async def get_customer_bonus(customer_id: str):
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{MS_URL}/entity/counterparty/{customer_id}", headers=headers) as resp:
            data = await resp.json()
            bonus = data.get("bonusPoints", 0)
            for attr in data.get("attributes", []):
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
# SHTRIX-KOD
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
# /start
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = await get_user_lang(user_id)
    await update.message.reply_text(t(lang, "welcome"), reply_markup=lang_keyboard())


# ==============================
# KARTA
# ==============================
async def show_card(message, phone: str, lang: str):
    await message.reply_text(t(lang, "loading"))
    customer = await get_customer_by_phone(phone)

    if not customer:
        user_id = message.chat.id
        await delete_user_phone(user_id)
        await message.reply_text(t(lang, "not_found", phone=phone))
        return

    name = customer.get("name", "")
    customer_id = customer.get("id", "")
    discount_card = customer.get("discountCardNumber", "") or ""
    barcode_data = discount_card if discount_card else customer_id[:13]
    bonus = await get_customer_bonus(customer_id)
    barcode_buf = generate_barcode(barcode_data)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "my_purchases"), callback_data="purchases")],
        [InlineKeyboardButton(t(lang, "change_phone"), callback_data="change_phone")],
    ])

    await message.reply_photo(
        photo=barcode_buf,
        caption=t(lang, "card_caption", name=name, phone=phone, card=barcode_data, bonus=bonus),
        reply_markup=keyboard
    )


# ==============================
# XARIDLAR
# ==============================
async def show_purchases(message, phone: str, lang: str):
    await message.reply_text(t(lang, "purchases_loading"))
    customer = await get_customer_by_phone(phone)

    if not customer:
        await message.reply_text("❌")
        return

    customer_id = customer.get("id", "")
    purchases = await get_customer_purchases(customer_id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "my_card"), callback_data="card")],
    ])

    if not purchases:
        await message.reply_text(t(lang, "purchases_empty"), reply_markup=keyboard)
        return

    text = t(lang, "purchases_title")
    for i, p in enumerate(purchases[:10], 1):
        moment = p.get("moment", "")[:10]
        summa = p.get("sum", 0) / 100
        text += f"{i}. 📅 {moment} — {summa:,.0f} so'm\n"

    await message.reply_text(text, reply_markup=keyboard)


# ==============================
# ADMIN PANEL
# ==============================
async def show_admin_panel(message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
    ])
    await message.reply_text("👨‍💼 Admin Panel", reply_markup=keyboard)


# ==============================
# BROADCAST
# ==============================
pending_broadcast = {}


async def send_broadcast(context, message, admin_id: int):
    user_ids = await get_all_user_ids()
    sent = 0
    failed = 0
    for user_id in user_ids:
        if user_id == admin_id:
            continue
        try:
            await message.copy(chat_id=user_id)
            sent += 1
        except Exception as e:
            logger.error(f"Yuborishda xatolik {user_id}: {e}")
            failed += 1
    await context.bot.send_message(
        chat_id=admin_id,
        text=f"✅ Yuborildi: {sent} ta\n❌ Xatolik: {failed} ta"
    )


# ==============================
# MATN XABARLAR
# ==============================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.message.from_user.id
    lang = await get_user_lang(user_id)
    is_admin = user_id in ADMIN_IDS

    # Telefon raqam kutilayotgan bo'lsa
    if context.user_data.get("waiting_phone"):
        phone = text.strip()
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 9:
            await update.message.reply_text(t(lang, "wrong_phone"))
            return
        context.user_data["waiting_phone"] = False
        await save_user_phone(user_id, phone)
        await show_card(update.message, phone, lang)
        return

    # Admin xabar yuborish rejimi
    if context.user_data.get("waiting_broadcast") and is_admin:
        context.user_data["waiting_broadcast"] = False
        pending_broadcast[user_id] = update.message

        user_ids = await get_all_user_ids()
        count = len([u for u in user_ids if u != user_id])

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Ha, {count} ta mijozga yuborish", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast")],
        ])
        await update.message.reply_text(
            f"📢 Shu xabarni {count} ta mijozga yubormoqchimisiz?",
            reply_markup=keyboard
        )
        return

    # Tugmalar
    if text == t(lang, "video"):
        try:
            await update.message.reply_video(video=VIDEO_URL, caption=t(lang, "video_caption"))
        except Exception as e:
            logger.error(f"Video xatolik: {e}")

    elif text == t(lang, "order"):
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "order_btn"), url=ORDER_LINK)]])
        await update.message.reply_text(t(lang, "order_text"), reply_markup=keyboard)

    elif text == t(lang, "card"):
        user = await get_user(user_id)
        phone = user["phone"] if user else None
        if phone:
            await show_card(update.message, phone, lang)
        else:
            context.user_data["waiting_phone"] = True
            await update.message.reply_text(t(lang, "enter_phone"))

    elif text == t(lang, "operator"):
        await update.message.reply_text(t(lang, "operator_text", phone=OPERATOR_PHONE))

    elif text == t(lang, "admin_panel") and is_admin:
        await show_admin_panel(update.message)


# ==============================
# MEDIA (rasm, video forward)
# ==============================
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    is_admin = user_id in ADMIN_IDS

    if not is_admin:
        return

    if context.user_data.get("waiting_broadcast"):
        context.user_data["waiting_broadcast"] = False
        pending_broadcast[user_id] = update.message

        user_ids = await get_all_user_ids()
        count = len([u for u in user_ids if u != user_id])

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Ha, {count} ta mijozga yuborish", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast")],
        ])
        await update.message.reply_text(
            f"📢 Shu xabarni {count} ta mijozga yubormoqchimisiz?",
            reply_markup=keyboard
        )


# ==============================
# INLINE TUGMALAR
# ==============================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = await get_user_lang(user_id)
    is_admin = user_id in ADMIN_IDS

    if query.data == "lang_uz":
        await save_user_lang(user_id, "uz")
        await query.message.reply_text(
            t("uz", "main_menu"),
            reply_markup=main_reply_keyboard("uz", is_admin)
        )

    elif query.data == "lang_ru":
        await save_user_lang(user_id, "ru")
        await query.message.reply_text(
            t("ru", "main_menu"),
            reply_markup=main_reply_keyboard("ru", is_admin)
        )

    elif query.data == "purchases":
        user = await get_user(user_id)
        if user and user["phone"]:
            await show_purchases(query.message, user["phone"], lang)

    elif query.data == "card":
        user = await get_user(user_id)
        if user and user["phone"]:
            await show_card(query.message, user["phone"], lang)

    elif query.data == "change_phone":
        await delete_user_phone(user_id)
        context.user_data["waiting_phone"] = True
        await query.message.reply_text(t(lang, "enter_new_phone"))

    elif query.data == "admin_broadcast" and is_admin:
        context.user_data["waiting_broadcast"] = True
        await query.message.reply_text(
            "📢 Yubormoqchi bo'lgan xabar, rasm yoki videoni yuboring:"
        )

    elif query.data == "confirm_broadcast" and is_admin:
        msg = pending_broadcast.get(user_id)
        if msg:
            await query.message.reply_text("⏳ Yuborilmoqda...")
            await send_broadcast(context, msg, user_id)
            pending_broadcast.pop(user_id, None)

    elif query.data == "cancel_broadcast" and is_admin:
        pending_broadcast.pop(user_id, None)
        await query.message.reply_text("❌ Bekor qilindi.")


# ==============================
# VIDEO FILE_ID
# ==============================
async def get_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.video and user_id in ADMIN_IDS:
        if not context.user_data.get("waiting_broadcast"):
            file_id = update.message.video.file_id
            logger.info(f"VIDEO FILE_ID: {file_id}")
            await update.message.reply_text(f"Video file_id: {file_id}")
            return
    await handle_media(update, context)


# ==============================
# MAIN
# ==============================
async def post_init(application):
    await init_db()


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, get_video_id))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
