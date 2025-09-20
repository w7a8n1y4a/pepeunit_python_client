from enum import Enum


class ReservedEnvVariableName:
    """Constants for reserved environment variables"""
    PEPEUNIT_URL = 'PEPEUNIT_URL'
    HTTP_TYPE = 'HTTP_TYPE'
    PEPEUNIT_APP_PREFIX = 'PEPEUNIT_APP_PREFIX'
    PEPEUNIT_API_ACTUAL_PREFIX = 'PEPEUNIT_API_ACTUAL_PREFIX'
    MQTT_URL = 'MQTT_URL'
    MQTT_PORT = 'MQTT_PORT'
    PEPEUNIT_TOKEN = 'PEPEUNIT_TOKEN'
    SYNC_ENCRYPT_KEY = 'SYNC_ENCRYPT_KEY'
    SECRET_KEY = 'SECRET_KEY'
    COMMIT_VERSION = 'COMMIT_VERSION'
    PING_INTERVAL = 'PING_INTERVAL'
    STATE_SEND_INTERVAL = 'STATE_SEND_INTERVAL'


class LogLevel(Enum):
    """Log levels"""
    DEBUG = 'Debug'
    INFO = 'Info'
    WARNING = 'Warning'
    ERROR = 'Error'
    CRITICAL = 'Critical'

    def get_int_level(self) -> int:
        """Returns numeric log level"""
        level_mapping = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_mapping[self]
