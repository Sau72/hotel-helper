from config_data.config import db, logger
from peewee import *



class Users(Model):
    """
    Модель пользователя.
    """

    telegram_id = IntegerField(unique=True)

    class Meta:
        database = db
        db_table = 'users'


class History(Model):
    """
    Модель истории поиска.
    """

    user = ForeignKeyField(Users, on_delete='cascade')
    search_date = DateField()
    search_time = TimeField()
    command = CharField(max_length=10)
    location = CharField()
    checkin_date = CharField()
    checkout_date = CharField()
    num_days = IntegerField(null=True)
    min_price = IntegerField(null=True)
    max_price = IntegerField(null=True)
    distance = FloatField(null=True)
    hotels = CharField()

    class Meta:
        database = db
        db_table = 'history'


with db:
    tables = [Users, History]
    if not all(table.table_exists() for table in tables):
        db.create_tables(tables)
        logger.debug('Таблицы в БД созданы успешно')
    else:
        logger.debug('Таблицы в БД уже существуют')
