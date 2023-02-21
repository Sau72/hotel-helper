from telebot.types import Message
from config_data.config import logger
from loader import bot


@bot.message_handler(commands=["start"])
def bot_start(message: Message):
    logger.debug('Команда /start')
    bot.send_message(message.from_user.id, f'Привет, {message.from_user.first_name}!')
    bot.send_message(message.from_user.id, f'Вызов справки /help')
    bot.send_message(message.from_user.id, 'Здесь можно получить лучшие предложения об отелях с сайта Hotels.com')
