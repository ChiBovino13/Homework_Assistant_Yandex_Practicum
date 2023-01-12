import requests
import telegram
import os
import logging
import time
import sys
import exceptions
from http import HTTPStatus
from settings import RETRY_PERIOD, ENDPOINT, HEADERS, HOMEWORK_VERDICTS

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('ID')

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение отправлено!')
    except Exception as e:
        logging.error(f'Cannot send message to chat. Error: {e}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise exceptions.RequestException(f'Ошибка эндпоинта {error}.')
    if response.status_code != HTTPStatus.OK:
        raise exceptions.StatusCodeServerAccessException(
            f'Сервер недоступен. Ошибка {response.status_code}.'
        )
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Приведите тип данных к формату dict.')
    if 'homeworks' not in response.keys():
        raise KeyError('В ответе API нет ключа homeworks')
    if 'current_date' not in response.keys():
        logging.error('В ответе API нет ключа current_date')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Приведите Homeworks к формату списка.')
    return response.get('homeworks')


def parse_status(homework):
    """Извлекает статус работы."""
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)
    homework_name = homework.get('homework_name')
    previous_status = ''
    if status is None:
        raise exceptions.HomeWorkStatusException(
            'У работы нет статуса.'
        )
    if verdict is None:
        raise exceptions.HomeWorkVerdictException(
            'У работы нет вердикта.'
        )
    if homework_name is None:
        raise exceptions.HomeWorkNameException(
            'Нет названия домашней работы.'
        )
    if status == previous_status:
        return f'Статус работы не изменился "{homework_name}". {verdict}'
    previous_status = status

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    empty_message = ''
    if not check_tokens():
        logging.critical(
            'Один или несколько токенов недоступны. Процесс завершен.'
        )
        sys.exit(1)
    timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            api_response = get_api_answer(timestamp)
            result = check_response(api_response)
            if len(result) > 0:
                logging.debug('Появился новый результат.')
            message = parse_status(result[0])
            if message != empty_message:
                send_message(bot, message)
                logging.debug('Сообщение {message} отправлено')
            else:
                logging.debug('Статус не изменился')
                empty_message = message
            if not api_response.get('current_date') is None:
                timestamp = api_response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.critical(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
