"""
Pepeunit Python Client

A multi-platform library for working with Pepeunit Unit Storage.
Supports MQTT and REST clients with optional dependencies.
"""

from .pepeunit_client import PepeunitClient, PepeunitClientError
from .enums import LogLevel, ReservedEnvVariableName
from .settings import Settings
from .file_manager import FileManager
from .interfaces import MQTTClientInterface, RESTClientInterface
from .mqtt_client import MQTTClient
from .rest_client import RESTClient
from .schema import Schema

__version__ = "0.10.0"
__all__ = [
    "PepeunitClient",
    "PepeunitClientError",
    "LogLevel", 
    "ReservedEnvVariableName",
    "Settings",
    "FileManager",
    "MQTTClientInterface",
    "RESTClientInterface",
    "MQTTClient",
    "RESTClient",
    "Schema",
]
