from telebot.types import Message
from config_data.config import logger, DEFAULT_COMMANDS
from loader import bot


# Эхо хендлер, куда летят текстовые сообщения без указанного состояния
@bot.message_handler(state=None)
def bot_echo(message: Message):
    logger.debug('Запрос справки')
    text = [f"/{command} - {desk}" for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, "\n".join(text))
