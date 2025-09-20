"""
Pepeunit Python Client

Мультиплатформенная библиотека для работы с Pepeunit Unit Storage.
Поддерживает работу с конфигурационными файлами, MQTT, REST API и логированием.
"""

from .pepeunit_client import (
    PepeunitClient,
    LogLevel,
    MQTTClientInterface,
    RESTClientInterface,
    FileManager,
    Settings,
    ReservedEnvVariableName
)

__version__ = "0.9.0"
__author__ = "Ivan Serebrennikov"
__email__ = "admin@silberworks.com"

__all__ = [
    "PepeunitClient",
    "LogLevel", 
    "MQTTClientInterface",
    "RESTClientInterface",
    "FileManager",
    "Settings",
    "ReservedEnvVariableName"
]
