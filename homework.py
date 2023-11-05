import logging
import os
import sys
import time
from http import HTTPStatus
from json.decoder import JSONDecodeError

import requests
from dotenv import load_dotenv
import telegram
from telegram import Bot

from exceptions import (
    ExceptionGetAPIError,
    ExceptionSendMessageError,
    ExceptionStatusError
)

import exceptions

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

logger = logging.getLogger(__name__)
fileHandler = logging.FileHandler('logs.log', encoding='utf-8')
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)
streamHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logger.info('Проверка доступности переменных окружения.')
    return all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logger.debug('Начало отправки сообщения в Telegram чат')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        raise ExceptionSendMessageError(
            f'Cбой при отправке сообщения "{message}" в Telegram. '
            f'Error: {error}')
    else:
        logger.debug(f'В Telegram отправлено сообщение "{message}"')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = int(time.time())
    params = {'from_date': timestamp}
    requests_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    try:
        logger.info(f'Запрос к эндпоинту "{ENDPOINT}" API-сервиса c '
                    f'параметрами {requests_params}')
        response = requests.get(**requests_params)
        if response.status_code != HTTPStatus.OK:
            message = (f'Сбой в работе программы: Эндпоинт {ENDPOINT} c '
                       f'параметрами {requests_params} недоступен. status_code'
                       f': {response.status_code}, reason: {response.reason}, '
                       f'text: {response.text}')
            raise ExceptionStatusError(message)
    except requests.exceptions.RequestException:
        raise exceptions.WrongResponseError(
            'Ошибка сервера {response.status_code.phrase}'
        )
    except Exception as error:
        raise ExceptionGetAPIError(
            f'Cбой при запросе к энпоинту "{ENDPOINT}" API-сервиса с '
            f'параметрами {requests_params}.'
            f'Error: {error}')
    try:
        response = response.json()
    except JSONDecodeError as error:
        raise exceptions.NotJSONError(
            f'Невозможно привести данные к типам Python. Ошибка: {error}'
        )
    return response


def check_response(response):
    """Проверяет ответ API на соответствие."""
    logger.info('Проверка ответа API на корректность')
    if not isinstance(response, dict):
        message = (f'Ответ API получен в виде {type(response)}, '
                   'а должен быть словарь')
        raise TypeError(message)
    required_keys = ['current_date', 'homeworks']
    missing_keys = [key for key in required_keys if key not in response]
    if missing_keys:
        error_message = 'Отсутствуют ключи: {}'.format(', '.join(missing_keys))
        raise KeyError(error_message)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        message = (f'API вернул {type(homeworks)} под ключом homeworks, '
                   'а должен быть список')
        raise TypeError(message)
    return homeworks


def parse_status(homework):
    """Информация конкретной домашней работы и статус этой работы."""
    logger.info('Извлечение из конкретной домашней работы статуса этой работы')
    if 'homework_name' not in homework:
        message = 'В словаре homework не найден ключ homework_name'
        raise KeyError(message)
    homework_name = homework.get('homework_name')
    if 'status' not in homework:
        message = 'В словаре homework не найден ключ status'
        raise KeyError(message)
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        message = (
            f'В словаре HOMEWORK_STATUSES не найден ключ {homework_status}')
        raise KeyError(message)
    verdict = HOMEWORK_VERDICTS.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = ('Доступны не все переменные окружения, которые '
                   'необходимы для работы программы: '
                   'PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID')
        logger.critical(message)
        sys.exit(message)

    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if 'homeworks' not in response:
                raise exceptions.WrongJSONError(
                    'Ответ не содержит списка работ.'
                )
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('В ответе API отсутсвуют новые статусы')
            timestamp = int(time.time())
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
