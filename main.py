from loader import bot
import handlers  # noqa
from telebot.custom_filters import StateFilter
from utils.set_bot_commands import set_default_commands
from config_data.config import logger


if __name__ == "__main__":
    logger.info('Запуск бота...')
    bot.add_custom_filter(StateFilter(bot))
    logger.debug('Установка команд...')
    set_default_commands(bot)
    logger.info('Бот запущен...')
    bot.infinity_polling()
