import os
import sqlite3
import logging
from urllib.parse import urlencode

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEB_APP_URL = os.environ["WEB_APP_URL"].rstrip("/")
DB_PATH = os.environ.get("DB_PATH", "cr7coin_users.sqlite3")

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger("cr7coin")

LANGUAGES = [
    ("uz", "🇺🇿 O‘zbekcha"), ("en", "🇬🇧 English"), ("ru", "🇷🇺 Русский"),
    ("tr", "🇹🇷 Türkçe"), ("ar", "🇸🇦 العربية"), ("es", "🇪🇸 Español"),
    ("fr", "🇫🇷 Français"), ("de", "🇩🇪 Deutsch"), ("zh", "🇨🇳 中文"),
    ("hi", "🇮🇳 हिन्दी"), ("pt", "🇵🇹 Português"), ("it", "🇮🇹 Italiano"),
    ("kk", "🇰🇿 Қазақша"), ("ko", "🇰🇷 한국어"), ("ja", "🇯🇵 日本語"),
]

TEXT = {
"uz": {"choose":"🌍 Tilni tanlang:","welcome":"🎉 CR7 Coin’ga xush kelibsiz! Til sozlandi. O‘yinni ochish uchun quyidagi tugmani bosing.","open":"🚀 CR7 Coin’ni ochish","change":"🌐 Tilni o‘zgartirish"},
"en": {"choose":"🌍 Choose your language:","welcome":"🎉 Welcome to CR7 Coin! Your language is set. Tap below to open the game.","open":"🚀 Open CR7 Coin","change":"🌐 Change language"},
"ru": {"choose":"🌍 Выберите язык:","welcome":"🎉 Добро пожаловать в CR7 Coin! Язык сохранён. Нажмите кнопку ниже, чтобы открыть игру.","open":"🚀 Открыть CR7 Coin","change":"🌐 Изменить язык"},
"tr": {"choose":"🌍 Dilinizi seçin:","welcome":"🎉 CR7 Coin’e hoş geldiniz! Diliniz kaydedildi. Oyunu açmak için aşağıya dokunun.","open":"🚀 CR7 Coin’i aç","change":"🌐 Dili değiştir"},
"ar": {"choose":"🌍 اختر لغتك:","welcome":"🎉 أهلاً بك في CR7 Coin! تم حفظ لغتك. اضغط أدناه لفتح اللعبة.","open":"🚀 افتح CR7 Coin","change":"🌐 تغيير اللغة"},
"es": {"choose":"🌍 Elige tu idioma:","welcome":"🎉 ¡Bienvenido a CR7 Coin! Tu idioma se ha guardado. Pulsa abajo para abrir el juego.","open":"🚀 Abrir CR7 Coin","change":"🌐 Cambiar idioma"},
"fr": {"choose":"🌍 Choisissez votre langue :","welcome":"🎉 Bienvenue sur CR7 Coin ! Votre langue est enregistrée. Appuyez ci-dessous pour ouvrir le jeu.","open":"🚀 Ouvrir CR7 Coin","change":"🌐 Changer de langue"},
"de": {"choose":"🌍 Sprache auswählen:","welcome":"🎉 Willkommen bei CR7 Coin! Deine Sprache wurde gespeichert. Tippe unten, um das Spiel zu öffnen.","open":"🚀 CR7 Coin öffnen","change":"🌐 Sprache ändern"},
"zh": {"choose":"🌍 请选择语言：","welcome":"🎉 欢迎来到 CR7 Coin！语言已保存。点击下方按钮打开游戏。","open":"🚀 打开 CR7 Coin","change":"🌐 更改语言"},
"hi": {"choose":"🌍 अपनी भाषा चुनें:","welcome":"🎉 CR7 Coin में आपका स्वागत है! आपकी भाषा सेव हो गई है। गेम खोलने के लिए नीचे टैप करें।","open":"🚀 CR7 Coin खोलें","change":"🌐 भाषा बदलें"},
"pt": {"choose":"🌍 Escolha seu idioma:","welcome":"🎉 Bem-vindo ao CR7 Coin! Seu idioma foi salvo. Toque abaixo para abrir o jogo.","open":"🚀 Abrir CR7 Coin","change":"🌐 Alterar idioma"},
"it": {"choose":"🌍 Scegli la lingua:","welcome":"🎉 Benvenuto su CR7 Coin! La lingua è stata salvata. Tocca qui sotto per aprire il gioco.","open":"🚀 Apri CR7 Coin","change":"🌐 Cambia lingua"},
"kk": {"choose":"🌍 Тілді таңдаңыз:","welcome":"🎉 CR7 Coin жобасына қош келдіңіз! Тіліңіз сақталды. Ойынды ашу үшін төмендегі батырманы басыңыз.","open":"🚀 CR7 Coin ашу","change":"🌐 Тілді өзгерту"},
"ko": {"choose":"🌍 언어를 선택하세요:","welcome":"🎉 CR7 Coin에 오신 것을 환영합니다! 언어가 저장되었습니다. 아래 버튼을 눌러 게임을 여세요.","open":"🚀 CR7 Coin 열기","change":"🌐 언어 변경"},
"ja": {"choose":"🌍 言語を選択してください：","welcome":"🎉 CR7 Coinへようこそ！言語を保存しました。下のボタンからゲームを開いてください。","open":"🚀 CR7 Coinを開く","change":"🌐 言語を変更"},
}

def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, language TEXT NOT NULL
    )""")
    con.commit()
    return con

def save_language(user_id: int, language: str):
    with db() as con:
        con.execute(
            "INSERT INTO users(user_id, language) VALUES(?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET language=excluded.language",
            (user_id, language)
        )

def get_language(user_id: int):
    with db() as con:
        row = con.execute(
            "SELECT language FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
    return row[0] if row else None

def language_keyboard():
    rows = []
    row = []
    for code, label in LANGUAGES:
        row.append(InlineKeyboardButton(label, callback_data=f"lang:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current = get_language(user_id)
    if current:
        await send_welcome(update, current, edit=False)
    else:
        await update.effective_message.reply_text(
            "🌍 Welcome to CR7 Coin!\n\n" + TEXT["en"]["choose"],
            reply_markup=language_keyboard()
        )

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🌍 Choose your language / Tilni tanlang:",
        reply_markup=language_keyboard()
    )

async def send_welcome(update_or_query, language: str, edit: bool):
    msg = TEXT.get(language, TEXT["en"])
    url = WEB_APP_URL + "?" + urlencode({"lang": language})
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(msg["open"], web_app=WebAppInfo(url=url))
    ]])
    if edit:
        await update_or_query.edit_message_text(msg["welcome"], reply_markup=keyboard)
    else:
        await update_or_query.effective_message.reply_text(msg["welcome"], reply_markup=keyboard)

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    value = query.data.split(":", 1)[1]
    if value not in TEXT:
        return
    save_language(query.from_user.id, value)
    await send_welcome(query, value, edit=True)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CallbackQueryHandler(choose_language, pattern=r"^lang:"))
    log.info("CR7 Coin multilingual bot is running")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
