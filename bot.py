from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

TOKEN = "8412405743:AAH4zAhdMr8iGWv2xPpcW8BQCVFNXkFEsz0"
ADMIN_ID = 7593179610   # <-- ТВОЙ ID

# хранит данные диалогов: {user_id: {"username": "...", "text": "..."}}
dialogs = {}


# ----------------------------------------------------------
# Пользователь пишет → сохраняем диалог → отправляем админу кнопку
# ----------------------------------------------------------
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message
    uid = msg.from_user.id

    # админ НЕ проходит сюда
    if uid == ADMIN_ID:
        return

    username = msg.from_user.username or "без никнейма"

    dialogs[uid] = {
        "username": username,
        "text": msg.text,
    }

    button = InlineKeyboardButton(
        text="▶ Ответить",
        callback_data=f"reply_{uid}"
    )
    keyboard = InlineKeyboardMarkup([[button]])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Новый диалог от @{username} ({uid}):\n{msg.text}",
        reply_markup=keyboard,
    )


# ----------------------------------------------------------
# Админ нажал кнопку «Ответить»
# ----------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    uid = int(query.data.split("_")[1])

    # сохраняем активный диалог В user_data админа
    context.user_data["active_dialog"] = uid

    await query.message.edit_text(
        f"Вы выбрали диалог с @{dialogs[uid]['username']} ({uid}).\n"
        f"Введите ответ:"
    )


# ----------------------------------------------------------
# Админ пишет ответ → отправляем пользователю
# ----------------------------------------------------------
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    # проверка — пишет ли админ
    if msg.from_user.id != ADMIN_ID:
        return

    active_dialog = context.user_data.get("active_dialog")

    if active_dialog is None:
        await msg.reply_text("Нет выбранного диалога. Нажмите кнопку «Ответить».")
        return

    # отправляем сообщение пользователю
    await context.bot.send_message(
        chat_id=active_dialog,
        text=msg.text,
    )

    await msg.reply_text("✅ Ответ отправлен.")

    # сбрасываем выбор
    context.user_data["active_dialog"] = None


# ----------------------------------------------------------
# Запуск бота
# ----------------------------------------------------------
app = ApplicationBuilder().token(TOKEN).build()

# сообщения пользователей (кроме админа)
app.add_handler(MessageHandler(filters.TEXT & ~filters.User(ADMIN_ID), user_message))

# ответы админа
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_reply))

# кнопки
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot started...")
app.run_polling()
