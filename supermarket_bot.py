import logging
import os
import io
import asyncio
import asyncpg
import aiohttp
import barcode
from datetime import datetime, time
from barcode.writer import ImageWriter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE")
ORDER_LINK = "https://b2b.moysklad.ru/public/Bya8IC3N6odI"
OPERATOR_PHONE = "+998975540666"
VIDEO_URL = os.environ.get("VIDEO_URL", "YOUR_VIDEO_FILE_ID")
MS_TOKEN = os.environ.get("MS_TOKEN", "a147c1756372f5ed43ead9c6b77d1b8ab56ae35a")
MS_URL = "https://api.moysklad.ru/api/remap/1.2"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:DKRngECbMYhNJQIjSUZPCPOtdKLhFrrk@postgres.railway.internal:5432/railway")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

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
        "main_menu": "Quyidagi tugmalardan birini tanlang 👇",
        "video": "📹 Video Qo'llanma",
        "order": "🛍 Buyurtma Boshlash",
        "card": "🎁 Nakopital Karta",
        "operator": "📞 Operator",
        "admin_panel": "👨‍💼 Admin Panel",
        "ai_agent": "🤖 AI Yordam",
        "order_btn": "🔗 Buyurtma sahifasiga o'tish",
        "order_text": "🛍 Buyurtma berish uchun:",
        "operator_text": "📞 Operator bilan bog'lanish:\n\n📱 Telefon: {phone}\n\nIsh vaqti: 10:00 - 22:00 (Dush-Yak)",
        "enter_phone": "🃏 Nakopital karta raqamingizni kiriting:\n\nMisol: 2900000000000",
        "wrong_phone": "❌ Noto'g'ri format. Karta raqami 13 ta raqamdan iborat.\nMisol: 2900000003262",
        "loading": "⏳ Ma'lumot yuklanmoqda...",
        "not_found": "❌ {phone} raqamli karta topilmadi.\nKassadan nakopital karta olganmisiz?\n\nKarta raqamini qayta kiriting:",
        "card_caption": "🎁 Nakopital Karta\n\n👤 Ism: {name}\n🃏 Karta raqami: {card}\n⭐ Bonus ballar: {bonus}\n\nShtrix-kodni kassirga ko'rsating!",
        "my_purchases": "🛍 Xaridlarim",
        "change_phone": "🔄 Karta raqamini o'zgartirish",
        "purchases_loading": "⏳ Xaridlar yuklanmoqda...",
        "purchases_empty": "🛍 Xaridlar tarixi bo'sh.",
        "purchases_title": "🛍 Oxirgi xaridlaringiz:\n\n",
        "my_card": "🎁 Kartam",
        "enter_new_phone": "🃏 Yangi karta raqamingizni kiriting:",
        "video_caption": "Ushbu qo'llanma orqali buyurtma berishni o'rganishingiz mumkin...",
        "ai_thinking": "🤖 Javob tayyorlanmoqda...",
        "ai_mode_on": "🤖 AI yordam rejimi yoqildi!\n\nSavolingizni yozing, javob beraman.\nAsosiy menyuga qaytish uchun /menu",
    },
    "ru": {
        "welcome": "Добро пожаловать в бот Sevimli Market!\n\nВыберите язык 👇",
        "main_menu": "Выберите одну из кнопок ниже 👇",
        "video": "📹 Видео инструкция",
        "order": "🛍 Оформить заказ",
        "card": "🎁 Карта накопителя",
        "operator": "📞 Оператор",
        "admin_panel": "👨‍💼 Admin Panel",
        "ai_agent": "🤖 AI Помощник",
        "order_btn": "🔗 Перейти к заказу",
        "order_text": "🛍 Для оформления заказа:",
        "operator_text": "📞 Связаться с оператором:\n\n📱 Телефон: {phone}\n\nРабочее время: 10:00 - 22:00 (Пн-Вс)",
        "enter_phone": "🃏 Введите номер вашей накопительной карты:\n\nПример: 2900000000000",
        "wrong_phone": "❌ Неверный формат. Номер карты состоит из 13 цифр.\nПример: 2900000003262",
        "loading": "⏳ Загрузка данных...",
        "not_found": "❌ Карта с номером {phone} не найдена.\nВы получили накопительную карту на кассе?\n\nВведите номер карты ещё раз:",
        "card_caption": "🎁 Карта накопителя\n\n👤 Имя: {name}\n🃏 Номер карты: {card}\n⭐ Бонусные баллы: {bonus}\n\nПокажите штрих-код кассиру!",
        "my_purchases": "🛍 Мои покупки",
        "change_phone": "🔄 Изменить номер карты",
        "purchases_loading": "⏳ Загрузка покупок...",
        "purchases_empty": "🛍 История покупок пуста.",
        "purchases_title": "🛍 Последние покупки:\n\n",
        "my_card": "🎁 Моя карта",
        "enter_new_phone": "🃏 Введите новый номер карты:",
        "video_caption": "С помощью этой инструкции вы узнаете как оформить заказ...",
        "ai_thinking": "🤖 Готовлю ответ...",
        "ai_mode_on": "🤖 Режим AI помощника включён!\n\nЗадайте ваш вопрос.\nДля возврата в меню: /menu",
    }
}

STORE_INFO = {
    "uz": """Sevimli Market haqida:
- Filiallar: SHAHAR SEVIMLI, UNZAVOD MARKET, SEVIMLI CAFE
- Ish vaqti: 10:00 - 22:00 (har kuni)
- Operator: +998975540666
- Buyurtma: {order_link}
- Nakopital karta: bonus ballar to'plash imkoniyati
""",
    "ru": """Sevimli Market:
- Филиалы: SHAHAR SEVIMLI, UNZAVOD MARKET, SEVIMLI CAFE
- Режим работы: 10:00 - 22:00 (ежедневно)
- Оператор: +998975540666
- Заказ: {order_link}
- Накопительная карта: накапливайте бонусные баллы
"""
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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_history (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        # Mahsulot kesh jadvali
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_cache (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                name_lower TEXT NOT NULL,
                price NUMERIC DEFAULT 0,
                code TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_product_name
            ON product_cache USING gin(to_tsvector('simple', name_lower))
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_meta (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        try:
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT 'uz'")
        except:
            pass
        try:
            await conn.execute("ALTER TABLE users ALTER COLUMN phone DROP NOT NULL")
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
            INSERT INTO users (user_id, phone, lang) VALUES ($1, NULL, $2)
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


async def get_ai_history(user_id: int, limit: int = 10):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM ai_history WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
            user_id, limit
        )
        return list(reversed(rows))


async def save_ai_message(user_id: int, role: str, content: str):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO ai_history (user_id, role, content) VALUES ($1, $2, $3)",
            user_id, role, content
        )
        await conn.execute("""
            DELETE FROM ai_history WHERE user_id = $1 AND id NOT IN (
                SELECT id FROM ai_history WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20
            )
        """, user_id)


async def clear_ai_history(user_id: int):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM ai_history WHERE user_id = $1", user_id)


def t(lang: str, key: str, **kwargs):
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


# ==============================
# MAHSULOT KESH
# ==============================
async def sync_products_from_moysklad():
    """MoySkladdan barcha mahsulotlarni yuklab PostgreSQL ga saqlash"""
    logger.info("Mahsulot sync boshlandi...")
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    all_products = []
    offset = 0
    limit = 1000

    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(
                f"{MS_URL}/entity/product",
                headers=headers,
                params={"limit": limit, "offset": offset}
            ) as resp:
                if resp.status != 200:
                    logger.error(f"MoySklad xatolik: {resp.status}")
                    break
                data = await resp.json()
                rows = data.get("rows", [])
                if not rows:
                    break
                for row in rows:
                    name = row.get("name", "")
                    price = 0
                    prices = row.get("salePrices", [])
                    if prices:
                        price = prices[0].get("value", 0) / 100
                    all_products.append({
                        "name": name,
                        "name_lower": name.lower(),
                        "price": price,
                        "code": row.get("code", "") or "",
                    })
                offset += limit
                if offset >= data.get("meta", {}).get("size", 0):
                    break
                await asyncio.sleep(0.3)

    if not all_products:
        logger.warning("Mahsulotlar topilmadi, sync bekor")
        return 0

    # DB ga yozish — eski o'chirib yangi qo'shish
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE TABLE product_cache")
            await conn.executemany(
                "INSERT INTO product_cache (name, name_lower, price, code) VALUES ($1, $2, $3, $4)",
                [(p["name"], p["name_lower"], p["price"], p["code"]) for p in all_products]
            )
            await conn.execute("""
                INSERT INTO cache_meta (key, value, updated_at)
                VALUES ('last_sync', NOW()::TEXT, NOW())
                ON CONFLICT (key) DO UPDATE SET value = NOW()::TEXT, updated_at = NOW()
            """)

    logger.info(f"Sync tugadi: {len(all_products)} mahsulot saqlandi")
    return len(all_products)


async def search_products_cache(query: str, limit: int = 8):
    """PostgreSQL keshdan mahsulot qidirish"""
    q = query.lower().strip()
    async with db_pool.acquire() as conn:
        # To'liq so'z qidirish
        rows = await conn.fetch("""
            SELECT name, price FROM product_cache
            WHERE name_lower LIKE $1
            ORDER BY name
            LIMIT $2
        """, f"%{q}%", limit)
        return [{"name": r["name"], "price": float(r["price"])} for r in rows]


async def get_cache_status():
    """Kesh holati"""
    async with db_pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM product_cache")
        meta = await conn.fetchrow("SELECT value FROM cache_meta WHERE key = 'last_sync'")
        last_sync = meta["value"] if meta else "hali sinxronizatsiya bo'lmagan"
        return count, last_sync


async def daily_sync_scheduler():
    """Har kuni soat 06:00 Toshkent vaqtida sync"""
    while True:
        now = datetime.utcnow()
        # Toshkent UTC+5, 06:00 = UTC 01:00
        target = now.replace(hour=1, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target.replace(day=target.day + 1)
        wait_seconds = (target - now).total_seconds()
        logger.info(f"Keyingi sync: {wait_seconds/3600:.1f} soatdan keyin")
        await asyncio.sleep(wait_seconds)
        try:
            count = await sync_products_from_moysklad()
            logger.info(f"Kunlik sync: {count} mahsulot")
        except Exception as e:
            logger.error(f"Sync xatolik: {e}")


# ==============================
# KEYBOARD
# ==============================
def main_reply_keyboard(lang: str, is_admin: bool = False):
    buttons = [
        [t(lang, "video")],
        [t(lang, "order"), t(lang, "card")],
        [t(lang, "operator"), t(lang, "ai_agent")],
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
# MOYSKLAD — KARTA
# ==============================
async def get_customer_by_card(card_number: str):
    headers = {"Authorization": f"Bearer {MS_TOKEN}"}
    card = card_number.strip()
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{MS_URL}/entity/counterparty",
            headers=headers,
            params={"filter": f"discountCardNumber={card}", "limit": 1}
        ) as resp:
            data = await resp.json()
            rows = data.get("rows", [])
            if rows:
                return rows[0]
        async with session.get(
            f"{MS_URL}/entity/counterparty",
            headers=headers,
            params={"search": card, "limit": 10}
        ) as resp:
            data = await resp.json()
            rows = data.get("rows", [])
            for row in rows:
                if (row.get("discountCardNumber") or "") == card:
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
# AI AGENT
# ==============================
async def ask_ai_agent(user_id: int, user_message: str, lang: str) -> str:
    if not ANTHROPIC_API_KEY:
        return "❌ AI agent sozlanmagan." if lang == "uz" else "❌ AI агент не настроен."

    # Mahsulot so'rovi aniqlash
    product_context = ""
    keywords_uz = ["narx", "bor", "sotiladi", "mahsulot", "qancha", "bormi", "mavjud", "sotib"]
    keywords_ru = ["цена", "есть", "продаётся", "товар", "сколько", "стоит", "купить"]
    keywords = keywords_uz if lang == "uz" else keywords_ru

    if any(kw in user_message.lower() for kw in keywords):
        products = await search_products_cache(user_message, limit=8)
        if products:
            if lang == "uz":
                product_context = "\n\nMahsulotlar (keshdan):\n"
                for p in products:
                    product_context += f"- {p['name']}: {p['price']:,.0f} so'm\n"
            else:
                product_context = "\n\nТовары (из кеша):\n"
                for p in products:
                    product_context += f"- {p['name']}: {p['price']:,.0f} сум\n"

    store_info = STORE_INFO.get(lang, STORE_INFO["uz"]).format(order_link=ORDER_LINK)
    if lang == "uz":
        system_prompt = f"""Sen Sevimli Market supermarketining AI yordamchisisisan.
Qoidalar:
- Faqat do'kon va mahsulotlar haqida javob ber
- Aloqasiz savollarga: "Bu savolga javob bera olmayman 🛒"
- Javob 1-2 jumladan oshmasin, juda qisqa
- Hech qanday markdown ishlatma: ** yoki * yoki _ yoki # belgisi YO'Q, oddiy matn
- Operator, filial, ish vaqtini faqat so'ralganda ayt
- Mahsulot topilsa: "Ha, bor! Narxi: [narx] so'm" — shunday qisqa
- Mahsulot topilmasa: "Aniq ma'lumot yo'q, operatorga murojaat qiling: +998975540666"
{store_info}{product_context}"""
    else:
        system_prompt = f"""Ты AI помощник супермаркета Sevimli Market.
Правила:
- Отвечай только про магазин и товары
- На другие вопросы: "Не могу ответить на это 🛒"
- Ответ максимум 1-2 предложения, очень кратко
- Никакого markdown: без ** * _ # символов, только обычный текст
- Оператора, филиалы, часы работы — только если спросили
- Если товар есть: "Да, есть! Цена: [цена] сум" — коротко
- Если нет инфо: "Точных данных нет, обратитесь к оператору: +998975540666"
{store_info}{product_context}"""

    history = await get_ai_history(user_id)
    messages = [{"role": r["role"], "content": r["content"]} for r in history]
    messages.append({"role": "user", "content": user_message})

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 512,
                    "system": system_prompt,
                    "messages": messages,
                }
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Claude API xatolik: {resp.status}")
                    return "❌ AI javob berishda xatolik." if lang == "uz" else "❌ Ошибка AI."
                data = await resp.json()
                ai_reply = data["content"][0]["text"]

        await save_ai_message(user_id, "user", user_message)
        await save_ai_message(user_id, "assistant", ai_reply)
        return ai_reply

    except Exception as e:
        logger.error(f"AI agent xatolik: {e}")
        return "❌ Xatolik yuz berdi." if lang == "uz" else "❌ Произошла ошибка."


# ==============================
# SHTRIX-KOD
# ==============================
def generate_barcode(code: str) -> io.BytesIO:
    buf = io.BytesIO()
    CODE128 = barcode.get_barcode_class('code128')
    bc = CODE128(code, writer=ImageWriter())
    bc.write(buf, options={
        "module_width": 0.4, "module_height": 15.0,
        "font_size": 10, "text_distance": 5,
        "quiet_zone": 6.5, "write_text": True,
        "background": "white", "foreground": "black",
    })
    buf.seek(0)
    return buf


# ==============================
# /start  /menu
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = await get_user_lang(user_id)
    context.user_data["ai_mode"] = False
    await update.message.reply_text(t(lang, "welcome"), reply_markup=lang_keyboard())


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = await get_user_lang(user_id)
    is_admin = user_id in ADMIN_IDS
    context.user_data["ai_mode"] = False
    context.user_data["waiting_phone"] = False
    await update.message.reply_text(t(lang, "main_menu"), reply_markup=main_reply_keyboard(lang, is_admin))


# ==============================
# ADMIN /sync  /cachestatus
# ==============================
async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    msg = await update.message.reply_text("⏳ MoySkladdan mahsulotlar yuklanmoqda...")
    try:
        count = await sync_products_from_moysklad()
        await msg.edit_text(f"✅ Sync tugadi!\n📦 {count} ta mahsulot saqlandi.")
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {e}")


async def cmd_cache_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    count, last_sync = await get_cache_status()
    await update.message.reply_text(
        f"📊 Kesh holati:\n\n"
        f"📦 Mahsulotlar: {count} ta\n"
        f"🕐 Oxirgi sync: {last_sync}\n"
        f"⏰ Keyingi sync: har kuni 06:00 (Toshkent)"
    )


# ==============================
# KARTA
# ==============================
async def show_card(message, card_number: str, lang: str):
    await message.reply_text(t(lang, "loading"))
    customer = await get_customer_by_card(card_number)
    if not customer:
        await delete_user_phone(message.chat.id)
        await message.reply_text(t(lang, "not_found", phone=card_number))
        return
    name = customer.get("name", "")
    customer_id = customer.get("id", "")
    bonus = await get_customer_bonus(customer_id)
    barcode_buf = generate_barcode(card_number)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "my_purchases"), callback_data="purchases")],
        [InlineKeyboardButton(t(lang, "change_phone"), callback_data="change_phone")],
    ])
    await message.reply_photo(
        photo=barcode_buf,
        caption=t(lang, "card_caption", name=name, card=card_number, bonus=bonus),
        reply_markup=keyboard
    )


async def show_purchases(message, card_number: str, lang: str):
    await message.reply_text(t(lang, "purchases_loading"))
    customer = await get_customer_by_card(card_number)
    if not customer:
        await message.reply_text("❌")
        return
    purchases = await get_customer_purchases(customer.get("id", ""))
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "my_card"), callback_data="card")]])
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
# ADMIN PANEL & BROADCAST
# ==============================
async def show_admin_panel(message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
    ])
    await message.reply_text("👨‍💼 Admin Panel", reply_markup=keyboard)


pending_broadcast = {}


async def send_broadcast(context, message, admin_id: int):
    user_ids = await get_all_user_ids()
    sent = failed = 0
    for user_id in user_ids:
        if user_id == admin_id:
            continue
        try:
            await message.copy(chat_id=user_id)
            sent += 1
        except Exception as e:
            logger.error(f"Broadcast xatolik {user_id}: {e}")
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

    if context.user_data.get("waiting_phone"):
        card = text.strip()
        digits = ''.join(filter(str.isdigit, card))
        if len(digits) < 10:
            await update.message.reply_text(t(lang, "wrong_phone"))
            return
        context.user_data["waiting_phone"] = False
        await save_user_phone(user_id, digits)
        await show_card(update.message, digits, lang)
        return

    if context.user_data.get("waiting_broadcast") and is_admin:
        context.user_data["waiting_broadcast"] = False
        pending_broadcast[user_id] = update.message
        user_ids = await get_all_user_ids()
        count = len([u for u in user_ids if u != user_id])
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Ha, {count} ta mijozga yuborish", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast")],
        ])
        await update.message.reply_text(f"📢 Shu xabarni {count} ta mijozga yubormoqchimisiz?", reply_markup=keyboard)
        return

    if context.user_data.get("ai_mode"):
        thinking_msg = await update.message.reply_text(t(lang, "ai_thinking"))
        reply = await ask_ai_agent(user_id, text, lang)
        await thinking_msg.delete()
        await update.message.reply_text(reply)
        return

    if text == t(lang, "video"):
        context.user_data["waiting_phone"] = False
        try:
            await update.message.reply_video(video=VIDEO_URL, caption=t(lang, "video_caption"))
        except Exception as e:
            logger.error(f"Video xatolik: {e}")

    elif text == t(lang, "order"):
        context.user_data["waiting_phone"] = False
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
        context.user_data["waiting_phone"] = False
        await update.message.reply_text(t(lang, "operator_text", phone=OPERATOR_PHONE))

    elif text == t(lang, "ai_agent"):
        context.user_data["ai_mode"] = True
        context.user_data["waiting_phone"] = False
        await clear_ai_history(user_id)
        await update.message.reply_text(t(lang, "ai_mode_on"))

    elif text == t(lang, "admin_panel") and is_admin:
        await show_admin_panel(update.message)


# ==============================
# MEDIA
# ==============================
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
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
        await update.message.reply_text(f"📢 Shu xabarni {count} ta mijozga yubormoqchimisiz?", reply_markup=keyboard)


async def get_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.video and user_id in ADMIN_IDS:
        if not context.user_data.get("waiting_broadcast"):
            file_id = update.message.video.file_id
            await update.message.reply_text(f"Video file_id: {file_id}")
            return
    await handle_media(update, context)


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
        await query.message.reply_text(t("uz", "main_menu"), reply_markup=main_reply_keyboard("uz", is_admin))
    elif query.data == "lang_ru":
        await save_user_lang(user_id, "ru")
        await query.message.reply_text(t("ru", "main_menu"), reply_markup=main_reply_keyboard("ru", is_admin))
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
        await query.message.reply_text("📢 Yubormoqchi bo'lgan xabar, rasm yoki videoni yuboring:")
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
# MAIN
# ==============================
async def post_init(application):
    await init_db()
    # Birinchi ishga tushganda kesh bo'sh bo'lsa — darhol sync
    count, _ = await get_cache_status()
    if count == 0:
        logger.info("Kesh bo'sh, birinchi sync boshlanmoqda...")
        asyncio.create_task(sync_products_from_moysklad())
    # Kunlik scheduler ishga tushirish
    asyncio.create_task(daily_sync_scheduler())


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("sync", cmd_sync))
    app.add_handler(CommandHandler("cachestatus", cmd_cache_status))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, get_video_id))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
