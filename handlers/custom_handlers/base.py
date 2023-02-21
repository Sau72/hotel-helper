from loader import bot
from states.contact_information import UserInfoState
from telebot.types import Message, InputMediaPhoto
from utils.api_hotels import get_locations
from keyboards.inline.inline_kb import city_markup, count_option_keyboard
from config_data.config import NUMBER_OF_HOTELS, logger
from utils.api_hotels import get_hotels, get_full_info
import telebot.apihelper
import urllib3.exceptions
from typing import Generator
from database.db_history import add_history_to_db, add_hotels_to_history_db


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def cmd_low(message: Message) -> None:
    """
    Стартовые команды запроса поиска '/lowprice', '/highprice', '/bestdeal'
    :param Message message: сообщение
    :return: None
    """
    logger.debug(f'Команда запроса на поиск: {message.text}')
    bot.set_state(message.from_user.id, UserInfoState.city, message.chat.id)
    bot.send_message(message.from_user.id, f"Введите город, в котором будем искать отель")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['cmd'] = message.text


@bot.message_handler(state=UserInfoState.city)
def get_city(message: Message) -> None:
    """
    Стейт ввода города с переходом на выбор, уточненного города
    :param Message message: сообщение
    :return: None
    """

    logger.debug(f'Запроса города для поиска: {message.text}')
    user_id = message.from_user.id
    chat_id = message.chat.id
    city = message.text

    cities = get_locations(message.text)

    if cities is None:
        logger.debug('Данные не получены. Повторите попытку позже.')
        bot.send_message(chat_id, 'Данные не получены. Повторите попытку позже.')
    elif cities:
        bot.set_state(user_id, UserInfoState.city_confirm, chat_id)
        with bot.retrieve_data(user_id, chat_id) as data:
            data['city'] = cities
            data['user_id'] = user_id
            data['chat_id'] = chat_id
        bot.send_message(chat_id, 'Уточните город: ', reply_markup=city_markup(cities))
    else:
        logger.debug(f'По запросу "{city}" ничего не найдено')
        bot.send_message(chat_id, f'По запросу "{city}" ничего не найдено.\n'
                                  f'Попробуйте еще раз.\n'
                                  f'Введите город для поиска')


def send_info(user_id, chat_id) -> None:
    """
    Вывод пользователю итоговой информации по вводным данным
    :param user_id: ID пользователя
    :param chat_id: ID чата
    :return: None
    """

    with bot.retrieve_data(user_id, chat_id) as data:
        num_days = (data['check_out'] - data['check_in']).days
        if 'num_hotels' not in data:
            data['num_hotels'] = NUMBER_OF_HOTELS
            data['num_foto'] = 0
            data['foto'] = False
        text = f"<b>Текущий город:</b> <i>{data['city']}</i>\n" \
               f"<b>Даты проживания:</b> <i>с {data['check_in'].strftime('%d.%m.%Y')} по " \
               f"{data['check_out'].strftime('%d.%m.%Y')}</i>\n" \
               f"<b>Количество суток:</b> <i>{num_days}</i>"
        if data['cmd'] == '/bestdeal':
            text += f"\n<b>Минимальная цена:</b> <i>{data['min_price']}$</i>\n" \
                    f"<b>Максимальная цена:</b> <i>{data['max_price']}$</i>\n" \
                    f"<b>Расстояние до:</b> <i>{data['max_distance']} км</i>\n"
            add_history_to_db(user_id, data['cmd'], data['city'], data['check_in'], data['check_out'],
                              num_days, data['min_price'], data['max_price'], data['max_distance'])
        else:
            add_history_to_db(user_id, data['cmd'], data['city'], data['check_in'], data['check_out'],
                              num_days, 0, 0, 0)

        logger.info(f"Вывод пользователю информации по поиску: {data['cmd']} {data['city']}")

        bot.send_message(user_id, text,
                         reply_markup=count_option_keyboard(data['num_hotels'], data['foto'], data['num_foto']),
                         parse_mode="HTML")


def get_hotel_info(user_id, chat_id) -> None:
    """
    Бозовый обработчик получения информации
    :param user_id: ID пользователя
    :param chat_id: ID чата
    :return: None
    """

    with bot.retrieve_data(user_id, chat_id) as data:
        command = data['cmd']
        num_foto = data['num_foto']
    logger.info(f"Получение отелей для города: {data['city']}")

    if command == '/lowprice':
        text = 'недорогих отелей'
        bot.send_message(chat_id, f'Получение списка {text}')
        result = get_hotels(data)
        hotels = result[:data['num_hotels']]
    elif command == '/highprice':
        text = 'дорогих отелей'
        bot.send_message(chat_id, f'Получение списка {text}')
        result = get_hotels(data)
        hotels = result[:-data['num_hotels'] - 1:-1]
    else:
        text = 'отелей ближе к центру'
        bot.send_message(chat_id, f'Получение списка {text}')
        result = get_hotels(data, data['min_price'], data['max_price'])
        result = check_distance(result, data['max_distance'])
        hotels = result[:data['num_hotels']]

    logger.info(f"Получение подробной информации об отелях")
    bot.send_message(chat_id, f'Уточнение данных {text}')
    hotels = get_full_info(hotels)

    for hotel in hotels:
        add_hotels_to_history_db(chat_id, hotel)

    logger.info(f"Отправка пользователю списка отелей")
    send_hotels(hotels, user_id, num_foto)


def send_hotels(hotels: list[dict], user_id: int, number_foto: int) -> None:
    """
    Отправка данных об отелях пользователю.
    :param hotels: список словарей с данными об отелях
    :param user_id: ID пользователя
    :param number_foto: количество выводимых фото, 0 - фото не выводятся
    :return: None
    """

    if len (hotels) == 0:
        bot.send_message(user_id, 'Отелей для данного запроса не найдено')
    for hotel in hotels:
        text = f"<b>{'★' * int(hotel.get('star', 0))} {hotel['name']}</b>\n" \
               f"<i>{hotel['address']}</i>\n" \
               f"{hotel['price_full']}\n" \
               f"{hotel['url']}"
        if number_foto > 0:
            foto = get_photo(hotel['foto'])

            for _ in range(3):
                # выполняются три попытки отправить медиагруппу с фото, каждый раз с новым набором фото
                foto_list = [InputMediaPhoto(next(foto)) for _ in range(number_foto - 1)]
                # к последнему фото добавляем текст с отелями
                foto_list.append(InputMediaPhoto(next(foto), caption=text, parse_mode='HTML'))
                try:
                    bot.send_media_group(user_id, foto_list)
                    break
                except [telebot.apihelper.ApiTelegramException, urllib3.exceptions.ReadTimeoutError] as msg:
                    print('Ошибка отправки медиагруппы. Отеля:', hotel['name'], msg)
                    logger.error(f"Ошибка отправки медиагруппы. Отеля:', hotel['name']")
            else:
                text = 'Фото получить не удалось.\n\n' + text
                bot.send_message(user_id, text,
                                 parse_mode='HTML',
                                 disable_web_page_preview=True,
                                 )
        else:
            bot.send_message(user_id, text,
                             parse_mode='HTML',
                             disable_web_page_preview=True,
                             )


def get_photo(foto: list[dict]) -> Generator:
    """
    Функция-генератор, генерирует url на фотографию
    :param foto: словарь с фотографиями
    :return: ссылки на фото отелей
    """

    for elem in foto:
        url = elem['image'].get('url')
        yield url


def check_distance(hotels: list[dict], max_distance: float) -> list[dict]:
    result = []
    for hotel in hotels:
        dist_km = round(float(hotel['distance']) * 1.60934, 2)
        if dist_km <= max_distance:
            result.extend([hotel])
    return result
