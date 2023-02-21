from telebot.types import Message
from config_data.config import DEFAULT_COMMANDS, logger
from loader import bot


@bot.message_handler(commands=["help"])
def bot_help(message: Message):
    logger.debug('Запрос справки')
    text = [f"/{command} - {desk}" for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, "\n".join(text))
