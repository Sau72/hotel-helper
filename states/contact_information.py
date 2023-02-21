from telebot.handler_backends import State, StatesGroup


class UserInfoState(StatesGroup):
    city = State()
    city_confirm = State()
    check_in = State()
    check_out = State()
    min_price = State()
    max_price = State()
    distance = State()
    all_data = State()
    show_history = State()

    # выбор города
    # подтверждение города
    # дата заезда
    # дата выезда
    # минимальная цена
    # максимальная цена
    # максимальное удаление
    # все данные
    # история
