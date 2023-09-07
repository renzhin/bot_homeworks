import logging
import os
import sys
import time
from http import HTTPStatus
from logging import Formatter, StreamHandler

import requests
import telegram
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(Formatter(fmt='%(asctime)s, %(levelname)s, %(message)s'))
logger.addHandler(handler)


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
    которые необходимы для работы программы.
    """
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logger.critical('Отсутствует одна или несколько переменных окружения')
        sys.exit(1)


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
    except Exception:
        logger.error('Ошибка отправки сообщения в Telegram')


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    Возвращает ответ API, приведя его из формата JSON к типам данных Python.
    """
    print(timestamp)
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=payload
        )
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
    if response.status_code != HTTPStatus.OK:
        raise logger.error('Статус запроса отличен от 200')
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на соответствие документации из урока API сервиса.
    В качестве параметра функция получает ответ API.
    Приведенный к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')

    if not response.get('homeworks'):
        raise KeyError('В ответе API отсутствует ключ homeworks')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Ответ API homeworks не является списком')


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка ДР.
    """
    try:
        homework['status'] in HOMEWORK_VERDICTS
        verdict = HOMEWORK_VERDICTS[homework['status']]
        homework_name = homework['homework_name']
    except Exception:
        logger.error('Статус отсутствует в словаре HOMEWORK_VERDICTS')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    status = ''
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            message = parse_status(response['homeworks'][0])
            verdict = response['homeworks'][0]['status']
            if verdict != status:
                print(verdict)
                send_message(bot, message)
                status = verdict

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
