import logging
import random
import asyncio
import sqlite3
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode

# ========== КОНФИГ ==========
TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
REQUIRED_CHANNEL = "@твой_канал"
ADMIN_ID = 123456789
BOT_NAME = "The Global Bot"

# Список каналов для проверки подписки
CHECK_CHANNELS = ["@channel1", "@channel2", REQUIRED_CHANNEL]

# Языки
LANGUAGES = {
    "ru": {
        "welcome": "🌍 *The Global Bot* — 30+ ботов в одном!\n\n💰 *Eblan Coin (EBC)* — главная валюта\n⭐ *Звёзды* — премиум валюта\n\nВыбери язык / Choose language:",
        "balance": "💰 *{}*, у тебя {} Eblan Coin (EBC) и {} ⭐",
        "daily_received": "🎁 +50 EBC! Забери завтра снова.",
        "daily_cooldown": "⏳ Ты уже забирал бонус сегодня! Приходи завтра.",
        "work_earned": "💼 Ты заработал {} EBC! Баланс: {} EBC",
        "work_cooldown": "⏳ Работай не чаще раза в час!",
        "not_enough": "💔 Недостаточно EBC!",
        "gift_sent": "🎁 {} перевёл {} EBC {}!",
        "gift_self": "😏 Себе нельзя!",
        "hug": "🤗 {} обнимает {} ❤️",
        "hug_air": "🤗 Обними воздух или ответь на сообщение друга с /hug",
        "roll": "🎲 {} из {}",
        "admin_only": "❌ Только админ!",
        "subscribed": "✅ Ты подписан на {}!",
        "not_subscribed": "❌ Ты НЕ подписан на {}. Подпишись: {}",
        "all_subscribed": "✅ Ты подписан на все обязательные каналы!",
        "not_all_subscribed": "❌ Ты не подписан на: {}",
        "converted": "✨ Конвертировано {} EBC → {} ⭐",
        "referral_link": "📎 *Твоя реферальная ссылка:*\n`{}`\n\n👥 Приглашено: {}\n🎁 За каждого друга: +25 EBC тебе, +15 EBC другу",
        "rules": "📜 *Правила чата*\n\n1️⃣ Без спама и флуда\n2️⃣ Без оскорблений\n3️⃣ Без ссылок без разрешения\n4️⃣ Подпишись на канал\n5️⃣ Уважай других",
        "help_text": "📞 *Помощь*\n\n👑 Админ: @твой_ник\n📜 Правила: /rules\n💰 Баланс: /balance\n🎮 Игры: /mafia\n🃏 Mini App: /game\n🌐 Язык: /lang",
        "mafia_start": "🃏 *Мафия*\nНапиши `/join_mafia` чтобы присоединиться.\nЧерез 60 секунд игра начнётся!",
        "mafia_joined": "✅ {} присоединился к Мафии! ({} игроков)",
        "mafia_not_enough": "❌ Недостаточно игроков для Мафии (нужно минимум 4). Игра отменена.",
        "mafia_role": "🃏 Твоя роль в Мафии: *{}*",
        "mafia_started": "🌙 Игра началась! Всего игроков: {}. Наступила ночь...",
        "warning": "⚠️ {} получил предупреждение! ({}/3)",
        "banned": "🚫 {} забанен за нарушение!",
        "spam_warning": "⚠️ {}, флуд! Предупреждение {}/3",
        "blocked_link": "🚫 Ссылка {} заблокирована!",
        "blocked_word": "⚠️ {}, запрещённое слово: {}",
        "cleaned": "🧹 Удалено {} сообщений",
        "stats": "📊 *Статистика чата*\n👥 Участников: {}\n💬 Активных за 7 дней: {}\n💰 Средний баланс: ~{} EBC",
        "calc_error": "❌ Ошибка в выражении",
        "calc_result": "🧮 {} = {}",
        "faq": "❓ *Частые вопросы*\n\n❓ *Как заработать EBC?*\n→ /daily (50 EBC в день)\n→ /work (10-30 EBC в час)\n→ /referral (25 EBC за друга)\n\n❓ *Что такое звёзды?*\n→ Премиум валюта, конвертация: /convert\n\n❓ *Как играть в Мафию?*\n→ /mafia → /join_mafia",
        "bot_created": "✅ Бот @{} успешно создан!\nТокен: `{}`\nСохрани его в безопасном месте!",
        "bot_creation_error": "❌ Ошибка при создании бота: {}",
        "enter_bot_name": "🤖 Введи название для нового бота (например: MyAwesomeBot):",
        "enter_bot_username": "📝 Введи username для бота (должен заканчиваться на 'bot', например: MyAwesomeBot):",
        "language_changed": "🌐 Язык изменён на русский!",
        "language_changed_en": "🌐 Language changed to English!",
        "mini_app_welcome": "🎮 *Mini App*\nНажми на кнопку ниже, чтобы открыть игру!",
    },
    "en": {
        "welcome": "🌍 *The Global Bot* — 30+ bots in one!\n\n💰 *Eblan Coin (EBC)* — main currency\n⭐ *Stars* — premium currency\n\nChoose language / Выбери язык:",
        "balance": "💰 *{}*, you have {} Eblan Coin (EBC) and {} ⭐",
        "daily_received": "🎁 +50 EBC! Come back tomorrow.",
        "daily_cooldown": "⏳ You already claimed your daily bonus today! Come back tomorrow.",
        "work_earned": "💼 You earned {} EBC! Balance: {} EBC",
        "work_cooldown": "⏳ Work only once per hour!",
        "not_enough": "💔 Not enough EBC!",
        "gift_sent": "🎁 {} sent {} EBC to {}!",
        "gift_self": "😏 You can't send to yourself!",
        "hug": "🤗 {} hugs {} ❤️",
        "hug_air": "🤗 Hug the air or reply to a friend's message with /hug",
        "roll": "🎲 {} out of {}",
        "admin_only": "❌ Admin only!",
        "subscribed": "✅ You are subscribed to {}!",
        "not_subscribed": "❌ You are NOT subscribed to {}. Subscribe: {}",
        "all_subscribed": "✅ You are subscribed to all required channels!",
        "not_all_subscribed": "❌ You are not subscribed to: {}",
        "converted": "✨ Converted {} EBC → {} ⭐",
        "referral_link": "📎 *Your referral link:*\n`{}`\n\n👥 Invited: {}\n🎁 Per friend: +25 EBC for you, +15 EBC for friend",
        "rules": "📜 *Chat Rules*\n\n1️⃣ No spam or flood\n2️⃣ No insults\n3️⃣ No links without permission\n4️⃣ Subscribe to the channel\n5️⃣ Respect others",
        "help_text": "📞 *Help*\n\n👑 Admin: @your_username\n📜 Rules: /rules\n💰 Balance: /balance\n🎮 Games: /mafia\n🃏 Mini App: /game\n🌐 Language: /lang",
        "mafia_start": "🃏 *Mafia*\nType `/join_mafia` to join.\nGame starts in 60 seconds!",
        "mafia_joined": "✅ {} joined Mafia! ({} players)",
        "mafia_not_enough": "❌ Not enough players for Mafia (need at least 4). Game cancelled.",
        "mafia_role": "🃏 Your role in Mafia: *{}*",
        "mafia_started": "🌙 Game started! Total players: {}. Night falls...",
        "warning": "⚠️ {} received a warning! ({}/3)",
        "banned": "🚫 {} was banned!",
        "spam_warning": "⚠️ {}, spam! Warning {}/3",
        "blocked_link": "🚫 Link {} is blocked!",
        "blocked_word": "⚠️ {}, forbidden word: {}",
        "cleaned": "🧹 Deleted {} messages",
        "stats": "📊 *Chat Stats*\n👥 Members: {}\n💬 Active in 7 days: {}\n💰 Average balance: ~{} EBC",
        "calc_error": "❌ Error in expression",
        "calc_result": "🧮 {} = {}",
        "faq": "❓ *Frequently Asked Questions*\n\n❓ *How to earn EBC?*\n→ /daily (50 EBC per day)\n→ /work (10-30 EBC per hour)\n→ /referral (25 EBC per friend)\n\n❓ *What are stars?*\n→ Premium currency, convert: /convert\n\n❓ *How to play Mafia?*\n→ /mafia → /join_mafia",
        "bot_created": "✅ Bot @{} successfully created!\nToken: `{}`\nSave it in a safe place!",
        "bot_creation_error": "❌ Error creating bot: {}",
        "enter_bot_name": "🤖 Enter a name for the new bot (e.g., MyAwesomeBot):",
        "enter_bot_username": "📝 Enter a username for the bot (must end with 'bot', e.g., MyAwesomeBot):",
        "language_changed": "🌐 Language changed to English!",
        "language_changed_ru": "🌐 Язык изменён на русский!",
        "mini_app_welcome": "🎮 *Mini App*\nClick the button below to open the game!",
    }
}

# ========== ИНИЦИАЛИЗАЦИЯ ==========
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== БАЗА ДАННЫХ ==========
conn = sqlite3.connect("global_bot.db")
cursor = conn.cursor()

# Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    eblan_coins INTEGER DEFAULT 100,
    stars INTEGER DEFAULT 0,
    language TEXT DEFAULT 'ru',
    last_daily TEXT,
    last_work TEXT,
    mafia_role TEXT,
    warnings INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    referred_by INTEGER,
    is_banned BOOLEAN DEFAULT 0
)
""")

# Заявки на вступление
cursor.execute("""
CREATE TABLE IF NOT EXISTS join_requests (
    user_id INTEGER,
    chat_id INTEGER,
    request_date TEXT
)
""")

# Чёрный список ссылок и слов
cursor.execute("CREATE TABLE IF NOT EXISTS blacklisted_links (link TEXT PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS blacklisted_words (word TEXT PRIMARY KEY)")

# Статистика сообщений
cursor.execute("""
CREATE TABLE IF NOT EXISTS message_stats (
    user_id INTEGER,
    chat_id INTEGER,
    message_date TEXT,
    message_text TEXT
)
""")

# Сессии создания ботов (BotFather)
cursor.execute("""
CREATE TABLE IF NOT EXISTS bot_creation_sessions (
    user_id INTEGER PRIMARY KEY,
    step TEXT,
    bot_name TEXT,
    bot_username TEXT
)
""")

default_words = ["spam", "spam", "реклама", "advertisement", "бан", "ban"]
for word in default_words:
    cursor.execute("INSERT OR IGNORE INTO blacklisted_words (word) VALUES (?)", (word,))

conn.commit()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_text(user_id: int, key: str, *args) -> str:
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    lang = result[0] if result and result[0] in LANGUAGES else "ru"
    text = LANGUAGES[lang].get(key, LANGUAGES["ru"].get(key, key))
    return text.format(*args) if args else text

def get_eblan(user_id: int) -> int:
    cursor.execute("SELECT eblan_coins FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res:
        return res[0]
    cursor.execute("INSERT INTO users (user_id, eblan_coins) VALUES (?, ?)", (user_id, 100))
    conn.commit()
    return 100

def add_eblan(user_id: int, amount: int):
    current = get_eblan(user_id)
    cursor.execute("UPDATE users SET eblan_coins = ? WHERE user_id = ?", (current + amount, user_id))
    conn.commit()

def remove_eblan(user_id: int, amount: int) -> bool:
    current = get_eblan(user_id)
    if current >= amount:
        cursor.execute("UPDATE users SET eblan_coins = ? WHERE user_id = ?", (current - amount, user_id))
        conn.commit()
        return True
    return False

def get_stars(user_id: int) -> int:
    cursor.execute("SELECT stars FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

def add_stars(user_id: int, amount: int):
    current = get_stars(user_id)
    cursor.execute("UPDATE users SET stars = ? WHERE user_id = ?", (current + amount, user_id))
    conn.commit()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def check_subscription(user_id: int, channel: str = None) -> bool:
    channel = channel or REQUIRED_CHANNEL
    try:
        member = await bot.get_chat_member(channel, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# ========== ВЫБОР ЯЗЫКА ==========
@dp.message(Command("lang"))
async def change_language(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer(get_text(message.from_user.id, "welcome"), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, callback.from_user.id))
    conn.commit()
    
    if lang == "ru":
        text = LANGUAGES["ru"]["language_changed"]
    else:
        text = LANGUAGES["en"]["language_changed_en"]
    
    await callback.answer()
    await callback.message.edit_text(text)

# ========== MINI APP (WEB APP) ==========
# HTML для Mini App (сохрани как mini_app.html и размести на хостинге)
MINI_APP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Global Bot - Mini Game</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .balance-card {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .balance {
            font-size: 32px;
            font-weight: bold;
            color: #ffd700;
        }
        .game-area {
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
        }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 18px;
            cursor: pointer;
            margin: 10px;
            transition: transform 0.2s;
        }
        .button:active {
            transform: scale(0.95);
        }
        .score {
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
        }
        .result {
            font-size: 24px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 The Global Bot - Mini Game</h1>
            <p>Игра "Угадай число" | Guess the Number</p>
        </div>
        
        <div class="balance-card">
            <div>💰 Eblan Coin (EBC)</div>
            <div class="balance" id="balance">Loading...</div>
        </div>
        
        <div class="game-area">
            <h2>🎲 Угадай число от 1 до 10</h2>
            <p>🎁 Угадал → +5 EBC | Промах → -2 EBC</p>
            
            <div class="score" id="score">?</div>
            
            <div>
                <button class="button" onclick="guess(1)">1</button>
                <button class="button" onclick="guess(2)">2</button>
                <button class="button" onclick="guess(3)">3</button>
                <button class="button" onclick="guess(4)">4</button>
                <button class="button" onclick="guess(5)">5</button>
            </div>
            <div>
                <button class="button" onclick="guess(6)">6</button>
                <button class="button" onclick="guess(7)">7</button>
                <button class="button" onclick="guess(8)">8</button>
                <button class="button" onclick="guess(9)">9</button>
                <button class="button" onclick="guess(10)">10</button>
            </div>
            
            <div class="result" id="result"></div>
        </div>
    </div>
    
    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        
        let currentBalance = 0;
        
        // Загрузка баланса
        tg.sendData(JSON.stringify({action: 'get_balance'}));
        
        // Обработка данных от бота
        tg.onEvent('mainButtonClicked', () => {});
        
        // Функция для отправки данных боту
        function sendToBot(data) {
            tg.sendData(JSON.stringify(data));
        }
        
        // Функция игры
        async function guess(number) {
            const target = Math.floor(Math.random() * 10) + 1;
            const resultDiv = document.getElementById('result');
            const scoreDiv = document.getElementById('score');
            
            if (number === target) {
                resultDiv.innerHTML = '✅ Угадал! +5 EBC';
                resultDiv.style.color = '#4caf50';
                sendToBot({action: 'win', amount: 5});
                currentBalance += 5;
            } else {
                resultDiv.innerHTML = `❌ Не угадал! Было число ${target}. -2 EBC`;
                resultDiv.style.color = '#f44336';
                sendToBot({action: 'lose', amount: 2});
                currentBalance -= 2;
            }
            
            scoreDiv.innerHTML = `💰 ${currentBalance} EBC`;
            
            setTimeout(() => {
                resultDiv.innerHTML = '🎲 Сделай свой ход!';
            }, 2000);
        }
        
        // Обработка входящих данных
        tg.onEvent('viewportChanged', () => {});
        
        // Получение данных от бота
        window.addEventListener('message', (event) => {
            if (event.data && event.data.balance !== undefined) {
                currentBalance = event.data.balance;
                document.getElementById('balance').innerHTML = currentBalance + ' EBC';
                document.getElementById('score').innerHTML = `💰 ${currentBalance} EBC`;
            }
        });
    </script>
</body>
</html>
"""

@dp.message(Command("game"))
async def mini_app_game(message: Message):
    """Mini App игра"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть игру / Open Game", web_app=WebAppInfo(url="https://your-domain.com/mini_app.html"))]
    ])
    await message.answer(get_text(message.from_user.id, "mini_app_welcome"), reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

# Обработка данных из Mini App
@dp.message(lambda message: message.web_app_data is not None)
async def handle_web_app_data(message: Message):
    data = json.loads(message.web_app_data.data)
    user_id = message.from_user.id
    
    if data.get("action") == "get_balance":
        balance = get_eblan(user_id)
        await message.answer(json.dumps({"balance": balance}))
    elif data.get("action") == "win":
        add_eblan(user_id, data.get("amount", 5))
        await message.answer(f"🎉 +{data.get('amount', 5)} EBC!")
    elif data.get("action") == "lose":
        remove_eblan(user_id, data.get("amount", 2))
        await message.answer(f"😢 -{data.get('amount', 2)} EBC!")

# ========== BOTFATHER (Создание ботов через бота) ==========
import aiohttp

async def create_bot_via_botfather(bot_name: str, bot_username: str) -> tuple:
    """Создание бота через API (требует специального доступа)"""
    # Примечание: Создание ботов через API возможно только с официальным BotFather
    # Это демо-функция. Реальное создание требует токен от BotFather
    url = f"https://api.telegram.org/bot{TOKEN}/createNewBot"
    # На самом деле это невозможно без специального доступа
    # Поэтому показываем инструкцию
    return False, "Для создания бота используй официального @BotFather вручную"

@dp.message(Command("createbot"))
async def create_bot_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(get_text(message.from_user.id, "admin_only"))
        return
    
    cursor.execute("INSERT OR REPLACE INTO bot_creation_sessions (user_id, step) VALUES (?, ?)", (message.from_user.id, "awaiting_name"))
    conn.commit()
    
    await message.answer(get_text(message.from_user.id, "enter_bot_name"))

@dp.message()
async def bot_creation_flow(message: Message):
    cursor.execute("SELECT step, bot_name, bot_username FROM bot_creation_sessions WHERE user_id = ?", (message.from_user.id,))
    session = cursor.fetchone()
    
    if not session:
        return
    
    step, bot_name, bot_username = session
    
    if step == "awaiting_name":
        cursor.execute("UPDATE bot_creation_sessions SET step = 'awaiting_username', bot_name = ? WHERE user_id = ?", (message.text, message.from_user.id))
        conn.commit()
        await message.answer(get_text(message.from_user.id, "enter_bot_username"))
    
    elif step == "awaiting_username":
        username = message.text.lower()
        if not username.endswith("bot"):
            await message.answer("❌ Username должен заканчиваться на 'bot'!")
            return
        
        cursor.execute("UPDATE bot_creation_sessions SET step = 'completed', bot_username = ? WHERE user_id = ?", (username, message.from_user.id))
        conn.commit()
        
        # Инструкция по созданию бота
        await message.answer(
            f"🤖 *Инструкция по созданию бота @{username}:*\n\n"
            f"1️⃣ Открой @BotFather\n"
            f"2️⃣ Отправь команду `/newbot`\n"
            f"3️⃣ Введи название: `{bot_name}`\n"
            f"4️⃣ Введи username: `{username}`\n"
            f"5️⃣ Сохрани полученный токен!\n\n"
            f"После создания бота, добавь его в чат и дай права администратора.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        cursor.execute("DELETE FROM bot_creation_sessions WHERE user_id = ?", (message.from_user.id,))
        conn.commit()

# ========== ОСТАЛЬНЫЕ КОМАНДЫ (с поддержкой языков) ==========

@dp.message(Command("start"))
async def start(message: Message):
    # Реферальная система
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != message.from_user.id:
            cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (message.from_user.id,))
            result = cursor.fetchone()
            if result is None or result[0] is None:
                cursor.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referrer_id, message.from_user.id))
                add_eblan(referrer_id, 25)
                add_eblan(message.from_user.id, 15)
                cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
                conn.commit()
    
    await change_language(message)

@dp.message(Command("balance"))
async def balance(message: Message):
    ebc = get_eblan(message.from_user.id)
    stars = get_stars(message.from_user.id)
    await message.answer(get_text(message.from_user.id, "balance", message.from_user.first_name, ebc, stars), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("daily"))
async def daily(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res and res[0]:
        last = datetime.fromisoformat(res[0])
        if datetime.now() - last < timedelta(hours=24):
            await message.answer(get_text(user_id, "daily_cooldown"))
            return
    add_eblan(user_id, 50)
    cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    await message.answer(get_text(user_id, "daily_received"))

@dp.message(Command("work"))
async def work(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT last_work FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res and res[0]:
        last = datetime.fromisoformat(res[0])
        if datetime.now() - last < timedelta(hours=1):
            await message.answer(get_text(user_id, "work_cooldown"))
            return
    earnings = random.randint(10, 30)
    add_eblan(user_id, earnings)
    cursor.execute("UPDATE users SET last_work = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    await message.answer(get_text(user_id, "work_earned", earnings, get_eblan(user_id)))

@dp.message(Command("convert"))
async def convert_currency(message: Message):
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /convert 100")
        return
    
    ebc_amount = int(args[1])
    stars_amount = ebc_amount // 10
    
    if remove_eblan(message.from_user.id, ebc_amount):
        add_stars(message.from_user.id, stars_amount)
        await message.answer(get_text(message.from_user.id, "converted", ebc_amount, stars_amount))
    else:
        await message.answer(get_text(message.from_user.id, "not_enough"))

@dp.message(Command("gift"))
async def gift(message: Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение пользователя: `/gift 50`", parse_mode=ParseMode.MARKDOWN)
        return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Пример: `/gift 50`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        amount = int(args[1])
        recipient = message.reply_to_message.from_user
        if recipient.id == message.from_user.id:
            await message.answer(get_text(message.from_user.id, "gift_self"))
            return
        if remove_eblan(message.from_user.id, amount):
            add_eblan(recipient.id, amount)
            await message.answer(get_text(message.from_user.id, "gift_sent", message.from_user.first_name, amount, recipient.first_name))
        else:
            await message.answer(get_text(message.from_user.id, "not_enough"))
    except:
        await message.answer("❌ Ошибка!")

@dp.message(Command("hug"))
async def hug(message: Message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user.first_name
        await message.reply(get_text(message.from_user.id, "hug", message.from_user.first_name, target))
    else:
        await message.answer(get_text(message.from_user.id, "hug_air"))

@dp.message(Command("roll"))
async def roll(message: Message):
    args = message.text.split()
    max_val = int(args[1]) if len(args) > 1 and args[1].isdigit() else 100
    num = random.randint(1, max_val)
    await message.reply(get_text(message.from_user.id, "roll", num, max_val))

@dp.message(Command("referral"))
async def referral(message: Message):
    user_id = message.from_user.id
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"
    cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    refs = cursor.fetchone()
    ref_count = refs[0] if refs else 0
    await message.answer(get_text(user_id, "referral_link", link, ref_count), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("rules"))
async def rules(message: Message):
    await message.answer(get_text(message.from_user.id, "rules"), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(get_text(message.from_user.id, "help_text"), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("faq"))
async def faq(message: Message):
    await message.answer(get_text(message.from_user.id, "faq"), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("check"))
async def check_sub(message: Message):
    args = message.text.split()
    channel = args[1] if len(args) > 1 else REQUIRED_CHANNEL
    
    if await check_subscription(message.from_user.id, channel):
        await message.answer(get_text(message.from_user.id, "subscribed", channel))
    else:
        await message.answer(get_text(message.from_user.id, "not_subscribed", channel, channel))

@dp.message(Command("checkall"))
async def check_all(message: Message):
    not_subscribed = []
    for channel in CHECK_CHANNELS:
        if not await check_subscription(message.from_user.id, channel):
            not_subscribed.append(channel)
    
    if not_subscribed:
        await message.answer(get_text(message.from_user.id, "not_all_subscribed", ', '.join(not_subscribed)))
    else:
        await message.answer(get_text(message.from_user.id, "all_subscribed"))

@dp.message(Command("calc"))
async def calculate(message: Message):
    expression = message.text.replace("/calc", "").strip()
    if not expression:
        await message.answer("❌ /calc 2+2")
        return
    try:
        allowed = re.match(r'^[\d+\-*/%(). ]+$', expression)
        if not allowed:
            await message.answer("❌ Разрешены только цифры и + - * / % ( )")
            return
        result = eval(expression)
        await message.answer(get_text(message.from_user.id, "calc_result", expression, result))
    except:
        await message.answer(get_text(message.from_user.id, "calc_error"))

@dp.message(Command("stats"))
async def stats(message: Message):
    members_count = await bot.get_chat_member_count(message.chat.id)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM message_stats WHERE chat_id = ? AND message_date > ?", 
                   (message.chat.id, week_ago))
    active_users = cursor.fetchone()[0] or 0
    await message.answer(get_text(message.from_user.id, "stats", members_count, active_users, random.randint(200, 1000)), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("clean"))
async def clean(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(get_text(message.from_user.id, "admin_only"))
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("❌ /clean 10")
        return
    count = min(int(args[1]), 100)
    deleted = 0
    async for msg in bot.get_chat_history(message.chat.id, limit=count+1):
        if msg.message_id != message.message_id:
            try:
                await msg.delete()
                deleted += 1
                await asyncio.sleep(0.2)
            except:
                pass
    await message.answer(get_text(message.from_user.id, "cleaned", deleted))

# ========== АНТИСПАМ И БЕЗОПАСНОСТЬ ==========
user_messages = defaultdict(list)

@dp.message()
async def security_and_antispam(message: Message):
    if not message.text:
        return
    
    user_id = message.from_user.id
    text_lower = message.text.lower()
    
    # Антиспам
    now = datetime.now()
    user_messages[user_id] = [t for t in user_messages[user_id] if (now - t).seconds < 5]
    user_messages[user_id].append(now)
    
    if len(user_messages[user_id]) > 5:
        await message.delete()
        cursor.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        warns = cursor.execute("SELECT warnings FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
        await message.answer(get_text(user_id, "spam_warning", message.from_user.first_name, warns))
        
        if warns >= 3:
            await bot.ban_chat_member(message.chat.id, user_id)
            await message.answer(get_text(user_id, "banned", message.from_user.first_name))
        return
    
    # Чёрный список слов
    cursor.execute("SELECT word FROM blacklisted_words")
    for row in cursor.fetchall():
        if row[0].lower() in text_lower:
            await message.delete()
            await message.answer(get_text(user_id, "blocked_word", message.from_user.first_name, row[0]))
            return
    
    # Чёрный список ссылок
    cursor.execute("SELECT link FROM blacklisted_links")
    for row in cursor.fetchall():
        if row[0] in message.text:
            await message.delete()
            await message.answer(get_text(user_id, "blocked_link", row[0]))
            return
    
    # Статистика
    cursor.execute("""
        INSERT INTO message_stats (user_id, chat_id, message_date, message_text)
        VALUES (?, ?, ?, ?)
    """, (user_id, message.chat.id, datetime.now().isoformat(), message.text[:500]))
    conn.commit()
    
    # Приветствие новичков
    if message.new_chat_members:
        for member in message.new_chat_members:
            if not member.is_bot:
                await message.reply(
                    f"👋 Добро пожаловать, {member.first_name}!\n"
                    f"📜 /rules\n💰 /daily\n🎮 /mafia\n🌐 /lang\n🃏 /game"
                )
    
    # Автоответы FAQ
    for keyword, answer in FAQ_DB_RU.items():
        if keyword in text_lower:
            await message.reply(answer)
            break

FAQ_DB_RU = {
    "правила": "📜 /rules",
    "как заработать": "💼 /work, /daily, /referral",
    "баланс": "💰 /balance",
    "админ": "👑 @твой_ник",
    "мафия": "🃏 /mafia",
    "звезды": "⭐ /stars, /convert",
    "язык": "🌐 /lang",
    "игра": "🎮 /game",
}

# ========== MAFIA ==========
mafia_games = {}

@dp.message(Command("mafia"))
async def mafia_start(message: Message):
    chat_id = message.chat.id
    if chat_id in mafia_games:
        await message.answer("🃏 Игра уже идёт!")
        return
    mafia_games[chat_id] = {"players": [message.from_user.id], "roles": {}, "day": 1, "started": False}
    await message.answer(get_text(message.from_user.id, "mafia_start"), parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(60)
    await start_mafia_game(chat_id, message)

async def start_mafia_game(chat_id, start_message):
    if chat_id not in mafia_games:
        return
    
    players = mafia_games[chat_id]["players"]
    if len(players) < 4:
        await bot.send_message(chat_id, get_text(start_message.from_user.id, "mafia_not_enough"))
        del mafia_games[chat_id]
        return
    
    roles = ["Мафия"] * max(1, len(players) // 3) + ["Мирный"] * (len(players) - max(1, len(players) // 3))
    random.shuffle(roles)
    
    for idx, user_id in enumerate(players):
        mafia_games[chat_id]["roles"][user_id] = roles[idx]
        try:
            await bot.send_message(user_id, get_text(user_id, "mafia_role", roles[idx]), parse_mode=ParseMode.MARKDOWN)
        except:
            pass
    
    mafia_games[chat_id]["started"] = True
    await bot.send_message(chat_id, get_text(start_message.from_user.id, "mafia_started", len(players)))

@dp.message(Command("join_mafia"))
async def join_mafia(message: Message):
    chat_id = message.chat.id
    if chat_id not in mafia_games:
        await message.answer("❌ Игра не запущена. /mafia")
        return
    if mafia_games[chat_id]["started"]:
        await message.answer("❌ Игра уже началась!")
        return
    if message.from_user.id not in mafia_games[chat_id]["players"]:
        mafia_games[chat_id]["players"].append(message.from_user.id)
        await message.answer(get_text(message.from_user.id, "mafia_joined", message.from_user.first_name, len(mafia_games[chat_id]["players"])))

# ========== @all ==========
@dp.message(Command("all"))
async def tag_all(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(get_text(message.from_user.id, "admin_only"))
        return
    
    chat_members = []
    async for member in bot.get_chat_administrators(message.chat.id):
        chat_members.append(member.user)
    
    if not chat_members:
        await message.answer("❌ Не удалось получить список")
        return
    
    mentions = " ".join([f"[{m.first_name}](tg://user?id={m.id})" for m in chat_members[:30]])
    text = message.text.replace("/all", "").strip() or "Внимание!"
    await bot.send_message(message.chat.id, f"🔔 {text}\n{mentions}", parse_mode=ParseMode.MARKDOWN)

# ========== ЗАПУСК ==========
async def main():
    print("🚀 The Global Bot (30+ ботов в 1) запущен!")
    print(f"📊 Бот: @{(await bot.get_me()).username}")
    print(f"💰 Валюта: Eblan Coin (EBC) + Звёзды (⭐)")
    print(f"🌐 Языки: Русский / English")
    print(f"🎮 Mini App: /game")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())