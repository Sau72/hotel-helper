import requests
from config_data.config import RAPID_API_KEY, logger
from typing import Optional, Dict, Literal, List
from datetime import datetime


def get_locations(city: str) -> Optional[Dict[str, str]]:
    """
    Функция получения от API Hotels всех городов, подходящих по названию.
    :param city: город для поиска
    :return: словарь(ключ - город: значение - gaiaId города)
    """

    querystring = {"q": city, "locale": "ru_RU"}
    resp = request_to_api_hotel(querystring, 'loc')
    if not resp:
        return None
    locations_dict = {}
    for region in resp['sr']:
        if region['type'] == 'CITY':
            city_name = region['regionNames'].get('fullName')
            city_id = region['gaiaId']
            locations_dict[city_name] = city_id
    return locations_dict


@logger.catch
def get_hotels(data: dict, min_price: int = 0, max_price: int = 0) -> List[dict]:
    """
    Получает словарь с ID города, формируется список отелей в городе,
    Данные запрашиваются при необходимости несколько раз,
    чтобы получить полный список отелей. (блоки по 200 позиций)
    :param data: текущие данные пользователя.
    :param min_price: минимальная цена в поиске
    :param max_price: максимальная цена в поиске
    :return: список, элемент списка - словарь с данными об отелях
    """

    def get_price(price: dict) -> str:   # парсинг цены в отеле
        try:
            cost = price['lead']['amount']
        except (TypeError, KeyError):
            return 'Стоимость: нет данных.'
        return f'За сутки {cost}$. Всего {cost * days:.2f}$ за {days} {end}'

    def parse(hotel: dict) -> dict:     # парсинг данных об отеле
        item = {
            'id': hotel['id'],
            'url': f'https://www.hotels.com/h{hotel["id"]}.Hotel-Information',
            'name': f"{hotel.get('name', '-')}",
            'price_full': get_price(hotel.get('price')),
            'price': f"{hotel['price']['lead'].get('amount')}",
            'distance': float(hotel['destinationInfo']['distanceFromDestination'].get('value'))
        }
        return item

    def date_to_dict(date_string: datetime) -> dict:
        """
        Переводим время в словарь
        :param str date_string: время
        :return: dict
        """
        return {
            'day': int(date_string.day),
            'month': int(date_string.month),
            'year': int(date_string.year)
        }

    #  начало функции
    days = (data['check_out'] - data['check_in']).days
    if days == 1:
        end = 'ночь'
    elif days < 5:
        end = 'ночи'
    else:
        end = 'ночей'

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": data['city_id']},
        "checkInDate": date_to_dict(data['check_in']),
        "checkOutDate": date_to_dict(data['check_out']),
        "rooms": [{"adults": 1}],
        "resultsStartingIndex": 0,
        "resultsSize": 200,
        "sort": "PRICE_LOW_TO_HIGH"
    }

    if min_price > 0:
        payload['filters'] = {"price": {"max": max_price, "min": min_price}}

    cur_len = 200  # считываем блоки отелей, пока properties не станет меньше 200 позиций
    hotel_start = 0
    result = []
    while cur_len == 200:
        response = request_to_api_hotel(payload, 'hotel')
        if not response:
            break
        response = response['data']['propertySearch']['properties']  # оставляем список отелей
        cur_len = len(response)
        logger.debug(f'Считано позиций отелей: {len(result) + cur_len}')
        result.extend([(parse(hotel) if hotel['price']['lead'].get('amount') != 0 else None) for hotel in response])
        hotel_start += 200
        payload.update({"resultsStartingIndex": hotel_start})
    pos = 0     #оставляем только те отели, у которых есть цена
    for hotels in result:
        if hotels is None:
            result = result[:pos]
            break
        pos += 1
    return result


@logger.catch
def get_full_info(hotels: list[dict]) -> list[dict]:
    """
    Уточнение данных по отелю
    :param hotels: словарь с данными об отелях
    :return: словарь с данными об отелях + ссылки на фото и кол-во звезд
    """
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": 0
    }

    for hotel in hotels:
        payload.update({"propertyId": hotel['id']})
        resp = request_to_api_hotel(payload, 'prop')
        if not resp:
            return None
        try:
            hotel['star'] = int(resp['data']['propertyInfo']['summary']['overview']['propertyRating'].get('rating'))
        except AttributeError:
            hotel['star'] = 0
        hotel['address'] = resp['data']['propertyInfo']['summary']['location']['address'].get('addressLine')
        hotel['foto'] = resp['data']['propertyInfo']['propertyGallery'].get('images')
    return hotels


@logger.catch
def request_to_api_hotel(querystring: dict, mode: Literal['loc', 'hotel', 'prop']) -> Optional[dict]:
    """
    Запроса к API Hotels
    v3 для запроса городов,
    v2 для запроса свойств
    :param querystring: строка запроса
    :param mode: тип запрашиваемых данных:
            'hotel' - список отелей
            'loc' - список городов
            'prop' - информация об отеле
    :return: json извлеченный из ответа (dict), если за 3 попытки не получено ответа, то None
    """
    if mode == 'loc':
        url = 'https://hotels4.p.rapidapi.com/locations/v3/search'
        headers = {'X-RapidAPI-Key': RAPID_API_KEY, 'X-RapidAPI-Host': 'hotels4.p.rapidapi.com'}

    elif mode == 'hotel':
        url = 'https://hotels4.p.rapidapi.com/properties/v2/list'
        headers = {"content-type": "application/json", "X-RapidAPI-Key": RAPID_API_KEY,
                   "X-RapidAPI-Host": "hotels4.p.rapidapi.com"}
    else:
        url = 'https://hotels4.p.rapidapi.com/properties/v2/detail'
        headers = {"content-type": "application/json", "X-RapidAPI-Key": RAPID_API_KEY,
                   "X-RapidAPI-Host": "hotels4.p.rapidapi.com"}

    for i in range(3):
        try:
            logger.debug(f'Запрос {mode}, попытка {i + 1}')
            if mode == 'loc':
                response = requests.request("GET", url, headers=headers, params=querystring, timeout=10)
            else:
                response = requests.request("POST", url, headers=headers, json=querystring, timeout=10)

            if response.status_code == 200:
                logger.debug('Ответ получен.')
                response.encoding = 'utf-8'
                response = response.json()
                return response
            else:
                return None
        except requests.exceptions.RequestException as er:
            logger.error('Ошибка запроса: ', er)
    return None
