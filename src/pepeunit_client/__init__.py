"""
PepeunitClient - Мультиплатформенная библиотека для работы с Pepeunit Unit Storage

Основные компоненты:
- PepeunitClient: Основной клиент для работы с Pepeunit
- Settings: Класс для работы с настройками
- Schema: Класс для работы с MQTT топиками
- LogLevel: Уровни логирования
- Исключения: PepeunitClientError
"""

from .pepeunit_client import PepeunitClient
from .settings import Settings
from .schema import Schema
from .enums import LogLevel, ReservedEnvVariableName
from .exceptions import PepeunitClientError

__version__ = "0.9.0"
__author__ = "Ivan Serebrennikov"
__email__ = "admin@silberworks.com"

__all__ = [
    "PepeunitClient",
    "Settings", 
    "Schema",
    "LogLevel",
    "ReservedEnvVariableName",
    "PepeunitClientError"
]
