from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date


def city_markup(cities: dict) -> InlineKeyboardMarkup:
    """
    Инлайн клавиатуры вариантов подходящих локаций.
    :param cities: словарь {Наименование_локации: ID локации + ключ}.
    :return: клавиатура
    """
    keyboard = InlineKeyboardMarkup()
    for city in cities:
        keyboard.add(InlineKeyboardButton(text=city, callback_data=city + ';keycity'))
    return keyboard


def count_option_keyboard(num_hotel: int, foto: bool, num_foto: int) -> InlineKeyboardMarkup:
    """
    Инлайн клавиатуры с опциями для вывода информации
    :param num_hotel: количество отелей для вывода
    :param foto: нужно ли выводить фото
    :param num_foto: количество фото для вывода
    :return: клавиатуру
    """
    yes = f'Да {num_foto} шт.'
    keyboard = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton(f'Кол-во отелей: {num_hotel}', callback_data='num_hotels')
    button2 = InlineKeyboardButton(f'Фото: {yes if foto else "Нет"}',
                                   callback_data='need_foto')
    button3 = InlineKeyboardButton(f'Продолжить', callback_data='continue_num_hotels')

    keyboard.add(button1, button2, button3)
    return keyboard


def calendar_keyboard_create(min_data: date):
    """
       Инлайн клавиатуры с календарем, создание
       :param min_data: минимальная дата в календаре
       :return: result, key
    """
    result, key = DetailedTelegramCalendar(locale='ru', min_date=min_data).build()
    return result, key


def calendar_keyboard_process(min_data: date, call):
    """
       Инлайн клавиатуры с календарем, обновление
       :param min_data: минимальная дата в календаре
       :param call: Callquery
       :return: result, key, step
    """
    result, key, step = DetailedTelegramCalendar(locale='ru', min_date=min_data).process(call)
    return result, key, step


def history_keyboard(history_record_id: int) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру для действий с записью истории.

    :param history_record_id: id записи истории в базе данных
    :type history_record_id: int
    """

    keyboard = InlineKeyboardMarkup()

    delete = InlineKeyboardButton(text='Удалить запись', callback_data='DELETE|' + str(history_record_id))
    clear_history = InlineKeyboardButton(text='Очистить историю', callback_data='CLEAR')

    keyboard.add(delete, clear_history)
    return keyboard
