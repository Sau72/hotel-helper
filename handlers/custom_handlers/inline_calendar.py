from loader import bot
from states.contact_information import UserInfoState
from datetime import date, timedelta
from telegram_bot_calendar import DetailedTelegramCalendar
from handlers.custom_handlers.base import send_info
from keyboards.inline.inline_kb import calendar_keyboard_create, calendar_keyboard_process
from handlers.custom_handlers.bestdeal import get_bestdeal_data
from config_data.config import logger


def check_in(chat_id) -> None:
    """
    Вывод пользователю календаря с заданием даты заезды
    :param chat_id: ID чата
    :return: None
    """

    bot.send_message(chat_id,
                     f"Дата заезда:",
                     reply_markup=calendar_keyboard_create(date.today()))


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=UserInfoState.check_in)
def cal(c) -> None:
    """
    Стейт обработка календаря заезда
    :param c: Callquery
    :return: None
    """
    user_id = c.message.chat.id
    chat_id = c.message.chat.id

    calendar_keyboard_process(date.today(), c.data)

    result, key, step = calendar_keyboard_process(date.today(), c.data)
    if not result and key:
        bot.edit_message_text(f"Дата заезда:",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        with bot.retrieve_data(user_id, chat_id) as data:
            data['check_in'] = result

        bot.edit_message_text(f"Дата заезда: {result}",
                              c.message.chat.id,
                              c.message.message_id)
        bot.set_state(user_id, UserInfoState.check_out, chat_id)
        logger.debug(f'Дата заезда: {result}')

        bot.send_message(chat_id, f"Дата выезда:", reply_markup=calendar_keyboard_create(data['check_in']))


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(), state=UserInfoState.check_out)
def cal(c):
    """
       Стейт обработка календаря выезда
       :param c: Callquery
       :return: None
       """
    user_id = c.message.chat.id
    chat_id = c.message.chat.id
    with bot.retrieve_data(user_id, chat_id) as data:
        check_in = data['check_in']
        check_in += timedelta(days=1)

    result, key, step = calendar_keyboard_process(check_in, c.data)

    if not result and key:
        bot.edit_message_text(f"Дата выезда:",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        with bot.retrieve_data(user_id, chat_id) as data:
            data['check_out'] = result

        bot.edit_message_text(f"Дата выезда: {result}",
                              c.message.chat.id,
                              c.message.message_id)
        logger.debug(f'Дата выезда: {result}')

        if data['cmd'] == '/bestdeal':
            get_bestdeal_data(user_id, chat_id)
        else:
            send_info(user_id, chat_id)
