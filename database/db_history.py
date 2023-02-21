import datetime
from config_data.config import db, logger
import json
from database.db_base import Users, History


@logger.catch
def add_history_to_db(telegram_id: int,
                      command: str,
                      location: str,
                      check_in: str,
                      check_out: str,
                      num_days: int,
                      min_price: int,
                      max_price: int,
                      distance: float) -> None:
    """
    Создаём запись для истории поиска. Т.к. отели выдаются по одному, их подтягиваем позднее.

    :param telegram_id: id пользователя в телеграмме
    :type telegram_id: int
    :param command: команда пользователя
    :type command: str
    :param location: город, который ищет пользователь
    :type location: str
    :param check_in: дата заезда
    :type check_in: str
    :param check_out: дата выезда
    :type check_out: str
    :param num_days: кол-во дней в отеле
    :type num_days: int
    :param min_price: минимальная цена
    :type max_price: int
    :param max_price: максимальная цена
    :type max_price: int
    :param distance: максимальное расстояние до центра
    :type distance: float
    :return: None
    """

    with db:
        user, created = Users.get_or_create(telegram_id=telegram_id)

        history_row = History(
            search_date=datetime.datetime.now().date(),
            search_time=datetime.datetime.now().time(),
            user=user,
            command=command,
            location=location,
            checkin_date=check_in,
            checkout_date=check_out,
            num_days=num_days,
            min_price=min_price,
            max_price=max_price,
            distance=distance,
            hotels='{}'
        )
        history_row.save()


@logger.catch
def add_hotels_to_history_db(telegram_id: int, hotel: dict) -> None:
    """
    Добавляет отель в запись истории.

    :param telegram_id: telegram_id пользователя в телеграмме
    :type telegram_id: int
    :param hotel: словарь отеля с параметрами
    :type hotel: dict
    :return: None
    """

    with db:
        hotel_id = hotel.get('id')
        hotel_url = hotel.get('url')
        hotel_name = hotel.get('name')
        hotel_price_full = hotel.get('price_full')
        hotel_price = hotel.get('price')
        hotel_distance = hotel.get('distance')
        hotel_star = hotel.get('star')
        hotel_address = hotel.get('address')

        history_row = History.select().join(Users).where(Users.telegram_id == telegram_id)\
            .order_by(History.search_date.desc(), History.search_time.desc())\
            .get()

        hotels_dict = json.loads(history_row.hotels)
        hotels_dict[hotel_id] = [hotel_url, hotel_name, hotel_price_full, hotel_price, hotel_distance, hotel_star,
                                 hotel_address]
        hotels_json = json.dumps(hotels_dict)

        history_row.hotels = hotels_json
        history_row.save()


def history_row_to_message(record: History) -> str:
    """
    Обрабатывает строку в базе данных и возвращает сообщение для пользователя.

    :param record: одна запись истории - объект модели History
    :type record: History
    :return: Сообщение для пользователя
    :rtype: str
    """

    search_date = record.search_date.strftime("%d-%m-%Y")
    search_time = record.search_time.strftime("%H:%M")
    command = record.command
    location = record.location
    check_in = record.checkin_date
    check_out = record.checkout_date
    num_days = record.num_days
    min_price = record.min_price
    max_price = record.max_price
    distance = record.distance
    hotels = record.hotels

    text = f"{search_date} {search_time}\n<b>Команда:</b> <i>{command}</i>\n" \
           f"<b>Текущий город:</b> <i>{location}</i>\n" \
           f"<b>Даты проживания:</b> <i>с {check_in} по " \
           f"{check_out}</i>\n" \
           f"<b>Количество суток:</b> <i>{num_days}</i>\n"
    if command == '/bestdeal':
        text += f"<b>Минимальная цена:</b> <i>{min_price}$</i>\n" \
                f"<b>Максимальная цена:</b> <i>{max_price}$</i>\n" \
                f"<b>Расстояние до:</b> <i>{distance} км</i>\n"

    hotels_dict = json.loads(hotels)
    text += '\n<b>Найденные отели:</b>'
    for hotel in hotels_dict.items():
        hotel_address = hotel[1][6]  # address
        hotel_url = hotel[1][0]  # url
        hotel_name = hotel[1][1]  # name
        hotel_price_full = hotel[1][2]  # price_full
        hotel_distance = hotel[1][4]  # distance
        hotel_star = hotel[1][5]  # star

        text += f"\n<b>{'★' * int(hotel_star)} {hotel_name}</b>\n" \
                f"<i>{hotel_address}</i>\n" \
                f"Расстояние: {hotel_distance}км\n" \
                f"{hotel_price_full}\n" \
                f"{hotel_url}\n"
    return text
