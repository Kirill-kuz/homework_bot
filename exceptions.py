class ExceptionSendMessageError(Exception):
    """Класс исключения при ошибке отправки сообщения."""

    pass


class ExceptionGetAPIError(Exception):
    """Класс исключения при ошибке запроса к API."""

    pass


class ExceptionStatusError(Exception):
    """Класс исключения при не корректном статусе ответа."""

    pass


class WrongResponseError(Exception):
    """Класс исключения при ошибке ответа сервера."""

    pass


class NotJSONError(Exception):
    """Класс исключения при ошибке JSONE."""

    pass
