class Error(Exception):
    """Базовый класс для исключений."""


class ExceptionSendMessageError(Error):
    """Класс исключения при ошибке отправки сообщения."""

    def __init__(self, message):
        self.message = message


class ExceptionGetAPIError(Exception):
    """Класс исключения при ошибке запроса к API."""

    def __init__(self, message):
        self.message = message


class ExceptionStatusError(Exception):
    """Класс исключения при не корректном статусе ответа."""

    def __init__(self, message):
        self.message = message
