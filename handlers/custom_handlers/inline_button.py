from loader import bot
from telebot.types import CallbackQuery
from states.contact_information import UserInfoState
from handlers.custom_handlers.inline_calendar import check_in
from keyboards.inline.inline_kb import count_option_keyboard
from config_data.config import NUMBER_OF_FOTO, logger
from handlers.custom_handlers.base import get_hotel_info

"""
Обработчики инлайн кнопок
"""


@bot.callback_query_handler(func=lambda call: call.data.endswith('keycity'))
def get_city(call: CallbackQuery) -> None:
    """
    Кнопка получения подтверждения города
    """

    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        cities = data['city']
        data['city'] = call.data.split(';')[0]
        data['city_id'] = cities.get(call.data.split(';')[0])

    bot.set_state(call.from_user.id, UserInfoState.check_in, call.message.chat.id)
    logger.debug(f"Уточненный город: {data['city']}")
    check_in(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == 'need_foto')
def change_show_foto(call: CallbackQuery) -> None:
    """
    Кнопка Установка режима вывода фото, либо 0, либо NUMBER_OF_FOTO, NUMBER_OF_FOTO + 2,
    NUMBER_OF_FOTO + 4 из файла конфигурации
    """
    bot.answer_callback_query(call.id)
    with bot.retrieve_data(call.from_user.id) as data:
        foto = data['foto']
        num_foto = data['num_foto']
        if not foto:
            foto = True
            num_foto = NUMBER_OF_FOTO
        else:
            num_foto += 2
            if num_foto == NUMBER_OF_FOTO + 6:
                foto = False
                num_foto = 0

        num = data['num_hotels']
        data['num_foto'] = num_foto
        data['foto'] = foto
    logger.debug(f"Выбрано: выводить фото - {foto}, кол-во фото - {num_foto}")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                  reply_markup=count_option_keyboard(num, foto, num_foto))


@bot.callback_query_handler(func=lambda call: call.data == 'num_hotels')
def change_number_hotels(call: CallbackQuery) -> None:
    """
    Кнопка Смена количества выводимых отелей от 5 до 15 с шагом 5.
    """
    bot.answer_callback_query(call.id)
    with bot.retrieve_data(call.from_user.id) as data:
        foto = data['foto']
        num = data['num_hotels']
        num_foto = data['num_foto']
        if num < 15:
            num += 5
        else:
            num = 5
        data['num_hotels'] = num
    logger.debug(f"Выбрано: выводить отелей - {num}")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                  reply_markup=count_option_keyboard(num, foto, num_foto))


@bot.callback_query_handler(func=lambda call: call.data == 'continue_num_hotels')
def receive_hotels(call: CallbackQuery) -> None:
    """
    Кнопка Получение списка отелей.
    """
    get_hotel_info(call.from_user.id, call.message.chat.id)
