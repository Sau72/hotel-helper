import os
from dotenv import load_dotenv, find_dotenv
from loguru import logger
from peewee import SqliteDatabase

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("help", "Вывести справку"),
    ('lowprice', 'Узнать топ самых дешёвых отелей в городе'),
    ('highprice', 'Узнать топ самых дорогих отелей в городе'),
    ('bestdeal', 'Узнать топ отелей, наиболее подходящих по цене и расположению'),
    ('history', 'Узнать историю поиска')
)


NUMBER_OF_FOTO = 3      # количество выводимых фото (со скольки начинается)
NUMBER_OF_HOTELS = 5    # количество выводимых отелей по умолчанию

#логирование
# LEVEL_DEBUG = 'INFO'
LEVEL_DEBUG = 'DEBUG'

logger.add('error.log', format="{time} {level} {message}",  level='DEBUG', rotation="10 MB", compression="zip")

#БД peewee

db = SqliteDatabase('history.db')
