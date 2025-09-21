from typing import Any, Dict
from .enums import ReservedEnvVariableName


class Settings:
    
    PEPEUNIT_URL: str = ''
    PEPEUNIT_APP_PREFIX: str = ''
    PEPEUNIT_API_ACTUAL_PREFIX: str = ''
    HTTP_TYPE: str = 'https'
    MQTT_URL: str = ''
    MQTT_PORT: int = 1883
    PEPEUNIT_TOKEN: str = ''
    SYNC_ENCRYPT_KEY: str = ''
    SECRET_KEY: str = ''
    COMMIT_VERSION: str = ''
    PING_INTERVAL: int = 30
    STATE_SEND_INTERVAL: int = 300

    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
