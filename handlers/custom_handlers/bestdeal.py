from loader import bot
from states.contact_information import UserInfoState
from telebot.types import Message
from handlers.custom_handlers.base import send_info
from config_data.config import logger


def get_bestdeal_data(user_id, chat_id) -> None:
    bot.send_message(user_id, f'Минимальная цена отеля за ночь, в $: ')
    bot.set_state(user_id, UserInfoState.min_price, chat_id)


@bot.message_handler(state=UserInfoState.min_price)
def get_min_price(message: Message) -> None:
    """
    Стейт ввода минимальной цены в поиске отелей
    :param Message message: сообщение
    :return: None
    """

    price_min = message.text
    if price_min.isdigit():
        price_min = int(price_min)
        if price_min == 0:
            price_min = 1   # при 0 ошибка при запросе API

        logger.debug(f"Минимальная цена: {price_min}")
        bot.set_state(message.from_user.id, UserInfoState.max_price, message.chat.id)
        bot.send_message(message.from_user.id, f"Максимальная цена отеля за ночь, в $: ")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['min_price'] = price_min
    else:
        bot.reply_to(message=message, text='Вы ввели не число. Повторите ввод минимальной цены:')
        logger.debug(f"Ввод минимальной цены. Вы ввели не число.")


@bot.message_handler(state=UserInfoState.max_price)
def get_max_price(message: Message) -> None:
    """
    Стейт ввода максимальной цены в поиске отелей
    :param Message message: сообщение
    :return: None
    """

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        price_min = data['min_price']
    price_max = message.text
    if price_max.isdigit():
        price_max = int(price_max)
        if price_max < price_min:
            bot.reply_to(message=message, text=f'Максимальная цена должна быть больше минимальной'
                                               f' цены за отель - {price_min} $')
        else:
            logger.debug(f"Максимальная цена: {price_max}")
            bot.set_state(message.from_user.id, UserInfoState.distance, message.chat.id)
            bot.send_message(message.from_user.id, f"Максимальное расстояние до отелей (км): ")
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['max_price'] = price_max
    else:
        bot.reply_to(message=message, text='Вы ввели не число. Повторите ввод максимальной цены:')
        logger.debug(f"Ввод максимальной цены. Вы ввели не число.")


@bot.message_handler(state=UserInfoState.distance)
def get_distance(message: Message) -> None:
    """
    Стейт ввода максимального расстояния до отелей
    :param Message message: сообщение
    :return: None
    """
    user_id = message.chat.id
    chat_id = message.chat.id
    distance = message.text
    if distance.isdigit():
        bot.set_state(message.from_user.id, UserInfoState.all_data, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['max_distance'] = float(distance)
        logger.debug(f"Расстояние до отеля: {distance}")
        send_info(user_id, chat_id)
    else:
        bot.reply_to(message=message, text='Вы ввели не число. Повторите ввод максимального расстояния:')
        logger.debug(f"Ввод расстояния до отеля. Вы ввели не число.")
