from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS
from loader import bot
from states.contact_information import UserInfoState


@bot.message_handler(commands=["helloworld"])
def bot_hello(message: Message) -> None:
    """
    Обработка команды /helloworld, вывод приветствия
    :param Message message: сообщение
    :return: None
    """

    bot.set_state(message.from_user.id, UserInfoState.city, message.chat.id)
    text = f"Здравствуйте, {message.from_user.full_name}"
    bot.send_message(message.from_user.id, text)
