# bot.py
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ------- Настройки -------
TOKEN = "8323692500:AAEu2WOcgMPkIeuNLTIavsGqbXX7myFw4C0"  # <- вставь токен
DB_FILE = "users.txt"

# ------- Утилиты для работы с базой -------
def ensure_db():
    if not os.path.exists(DB_FILE):
        # создать пустой файл
        with open(DB_FILE, "w", encoding="utf-8") as f:
            pass

def search_user(username: str):
    ensure_db()
    username = username.lower().strip()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                u, reason = line.strip().split("|", 1)
                if u.lower().strip() == username:
                    return reason.strip()
    return None

def add_user(username: str, reason: str):
    ensure_db()
    # Записываем в формате: username | причина
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"{username} | {reason}\n")

# ------- Обработчики -------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить", callback_data="check")],
        [InlineKeyboardButton("➕ Добавить в базу", callback_data="add")]
    ]
    await update.message.reply_text(
        "👋 Привет! Я *TeleCheker_Bot*.\nВыбери действие:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "check":
            context.user_data["mode"] = "check"
            await query.message.reply_text("🔎 Введите username для проверки (пример: @username или username):")
        elif query.data == "add":
            context.user_data["mode"] = "add_user"
            await query.message.reply_text("📝 Введите username, которого хотите добавить в базу:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    # Режим проверки
    if mode == "check":
        username = text
        # нормализуем: убираем @ в начале
        if username.startswith("@"):
            username = username[1:]
        result = search_user(username)
        if result:
            await update.message.reply_text(f"⚠ Пользователь *{username}* найден в базе.\nПричина: {result}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"✅ Пользователь *{username}* не найден в базе.", parse_mode="Markdown")
        context.user_data["mode"] = None

    # Начинаем добавление: получили username
    elif mode == "add_user":
        username = text
        if username.startswith("@"):
            username = username[1:]
        context.user_data["new_username"] = username
        context.user_data["mode"] = "add_reason"
        await update.message.reply_text("✏ Теперь введите причину добавления (коротко):")

    # Получили причину — добавляем в базу
    elif mode == "add_reason":
        username = context.user_data.get("new_username")
        reason = text
        if not username:
            await update.message.reply_text("Ошибка: не указан username. Начните заново через /start.")
            context.user_data["mode"] = None
            return
        add_user(username, reason)
        await update.message.reply_text(f"✔ Пользователь *{username}* добавлен в базу.\nПричина: {reason}", parse_mode="Markdown")
        context.user_data["mode"] = None
        context.user_data.pop("new_username", None)

    else:
        await update.message.reply_text("Нажмите /start чтобы открыть меню.")

# ------- Основной запуск (синхронно, чтобы не конфликтовать с Pydroid3) -------
def main():
    ensure_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("TeleCheker_Bot запущен. Ожидание сообщений...")
    # Важно: в Pydroid3 чаще всего лучше запускать app.run_polling() синхронно
    app.run_polling()

if __name__ == "__main__":
    main()