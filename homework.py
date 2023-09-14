import logging
import os
import sys
import time
from http import HTTPStatus
from logging import FileHandler, StreamHandler

import requests
import telegram
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
file_handler = FileHandler(filename='app.log', mode='w', encoding='utf-8')
console_handler = StreamHandler(stream=sys.stdout)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """
    Проверяет доступность переменных окружения.
    которые необходимы для работы программы.знеуые
    """
    var_env = {
        'Токен Яндекс.Практикум': PRACTICUM_TOKEN,
        'Токен Телеграм-бота': TELEGRAM_TOKEN,
        'ID Телеграм-чата пользователя': TELEGRAM_CHAT_ID,
    }
    token_status = True
    for key, value in var_env.items():
        if not value:
            logger.critical(f'{key} отсутствует')
            token_status = False
    logger.debug('Проверка переменных окружения завершена')
    return token_status


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат.
    Определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра.
    Экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Успешная отправка сообщения в Telegram')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    Возвращает ответ API, приведя его из формата JSON к типам данных Python.
    """
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=payload
        )
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Статус запроса отличен от 200')
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на соответствие документации из урока API сервиса.
    В качестве параметра функция получает ответ API.
    Приведенный к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError(f'Ответ API не является словарем: {type(response)}')
    if 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ homeworks')
    home_works = response['homeworks']
    if not isinstance(home_works, list):
        raise TypeError(
            f'Ответ API homeworks не является списком: {type(home_works)}'
        )
    logger.debug('Данные, полученные в запросе к API проверены')
    return home_works


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка ДР.
    """
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name отсутсвует')
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Ключ status отсутствует')
    verdict = HOMEWORK_VERDICTS[homework_status]
    homework_name = homework['homework_name']
    logger.debug('Извлечение статуса работы из ответа API закончено')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)

    timestamp = 0
    last_message = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                current_message = parse_status(homework[0])
                if current_message != last_message:
                    send_message(bot, current_message)
                    last_message = current_message
            else:
                logger.debug('Статус работы не изменился.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_message:
                send_message(bot, message)
                last_message = message
        finally:
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s, %(levelname)s, %(funcName)s, %(message)s',
        handlers=[file_handler, console_handler],
        level=logging.DEBUG,
    )
    main()
