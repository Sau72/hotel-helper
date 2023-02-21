from loader import bot
from config_data.config import db, logger
from database.db_base import History, Users
from telebot.types import Message, CallbackQuery
from states.contact_information import UserInfoState
from database.db_history import history_row_to_message
from keyboards.inline.inline_kb import history_keyboard


@bot.message_handler(commands=['history'])
def show_history(message: Message) -> None:
    """
    Показ истории поиска.

    :param message: Объект сообщения.
    :type message: Message
    :return: None
    """

    logger.debug(f'Команда запроса на поиск: {message.text}')
    telegram_id = message.chat.id
    bot.set_state(message.from_user.id, UserInfoState.show_history, message.chat.id)

    with db:
        user_history = History.select().join(Users).where(Users.telegram_id == telegram_id)

        if len(user_history) > 0:
            for record in user_history:
                message_text = history_row_to_message(record)

                bot.send_message(message.chat.id, message_text,
                                 reply_markup=history_keyboard(record.id),
                                 parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, 'К сожалению, в истории нет ни одной записи\n'
                                              'Начать поиск можно с помощью команд /lowprice, /highprice и /bestdeal\n'
                                              'Выполненный поиск будет автоматически добавлен в историю')


@bot.callback_query_handler(func=lambda call: call.data.startswith('DELETE'), state=UserInfoState.show_history)
def delete_record(callback: CallbackQuery) -> None:
    """
    Удаление записи из истории.

    :param callback: Объект CallBackQuery
    :type: CallbackQuery
    :return: None
    """

    logger.debug(f'Удаление записи из истории')
    record_id = callback.data.split('|')[1]

    with db:
        record = History.select().where(History.id == record_id).get()
        record.delete_instance()

    bot.answer_callback_query(callback.id)
    bot.delete_message(callback.message.chat.id, callback.message.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('CLEAR'), state=UserInfoState.show_history)
def delete_record(callback: CallbackQuery) -> None:
    """
    Очистка истории.

    :param callback: Объект CallBackQuery
    :type: CallbackQuery
    :return: None
    """

    logger.debug(f'Полная очистка истории')
    telegram_id = callback.message.chat.id

    with db:
        user_history = History.select().join(Users).where(Users.id == telegram_id)
        for record in user_history:
            record.delete_instance()

    bot.answer_callback_query(callback.id)
    bot.send_message(telegram_id, 'История очищена')
