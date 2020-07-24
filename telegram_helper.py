from telegram.error import BadRequest

ADMIN_CHAT_ID = 123456789  # Your chat id
ADMIN_FIRST_NAME = "Your_telegram_first_name"
ADMIN_LAST_NAME = "Your_telegram_last_name"


def utf8len(s):
    return len(s.encode('utf-8'))


def is_admin_texting(update):
    if update.message.chat_id == ADMIN_CHAT_ID and \
                    update.message.from_user.first_name == "Deve" and \
                    update.message.from_user.last_name == "Scie":
        return True
    else:
        return False


def replay_to_user(bot, update, message):
    try:
        bot.send_message(chat_id=update.message.chat_id, text=message)
    except BadRequest as e:
        bot.send_message(chat_id=update.message.chat_id, text=e.message)


def send_message_to_admin(bot, message):
    try:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
    except BadRequest as e:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=e.message)
