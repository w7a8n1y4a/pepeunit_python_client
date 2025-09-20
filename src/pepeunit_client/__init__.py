"""
Pepeunit Python Client

A multi-platform library for working with Pepeunit Unit Storage.
Supports MQTT and REST clients with optional dependencies.
"""

from .pepeunit_client import PepeunitClient
from .enums import LogLevel, ReservedEnvVariableName
from .settings import Settings
from .file_manager import FileManager
from .interfaces import MQTTClientInterface, RESTClientInterface

__version__ = "0.9.0"
__all__ = [
    "PepeunitClient",
    "LogLevel", 
    "ReservedEnvVariableName",
    "Settings",
    "FileManager",
    "MQTTClientInterface",
    "RESTClientInterface",
]
