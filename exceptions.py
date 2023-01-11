import requests

class StatusCodeServerAccessException(Exception):
    """Ошибка доступа сервера."""
    pass

class EmptyStatusException(Exception):
    """Отсутствует запрашиваемый ключ."""
    pass

class RequestException(Exception):
    """Ошибка эндпоинта."""
    pass

class HomeWorkNameException(Exception):
    """Нет имени домашней работы"""
    pass

class HomeWorkStatusException(Exception):
    """Ошибка ключа status."""
    pass

class HomeWorkVerdictException(Exception):
    """Ошибка ключа verdict."""
    pass
