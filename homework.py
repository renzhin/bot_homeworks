import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 10
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
    ...


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат.
    Определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра.
    Экземпляр класса Bot и строку с текстом сообщения.
    """
    ...


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    Возвращает ответ API, приведя его из формата JSON к типам данных Python.
    """
    print(timestamp)
    payload = {'from_date': timestamp - RETRY_PERIOD * 6000000}
    response = requests.get(
        ENDPOINT, headers=HEADERS, params=payload
    )
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на соответствие документации из урока API сервиса.
    В качестве параметра функция получает ответ API.
    Приведенный к типам данных Python.
    """
    return response


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка ДР.
    """
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    status = ''
    # ...

    while True:
        try:
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            homework = response['homeworks'][0]['status']
            if homework != status:
                print(homework)
                bot.send_message(TELEGRAM_CHAT_ID, homework)
                status = homework

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
