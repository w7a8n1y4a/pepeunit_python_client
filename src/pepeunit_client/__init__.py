"""
Pepeunit Python Client

Мультиплатформенная библиотека для работы с Pepeunit Unit Storage.
Поддерживает работу с конфигурационными файлами, MQTT, REST API и логированием.
"""

from .pepeunit_client import PepeunitClient
from .constants import LogLevel, ReservedEnvVariableName
from .settings import Settings
from .file_manager import FileManager
from .interfaces import MQTTClientInterface, RESTClientInterface
from .mqtt_client import PepeunitMQTTClient
from .rest_client import PepeunitRESTClient

__version__ = "0.9.0"
__author__ = "Ivan Serebrennikov"
__email__ = "admin@silberworks.com"

__all__ = [
    "PepeunitClient",
    "LogLevel", 
    "ReservedEnvVariableName",
    "Settings",
    "FileManager",
    "MQTTClientInterface",
    "RESTClientInterface",
    "PepeunitMQTTClient",
    "PepeunitRESTClient"
]
