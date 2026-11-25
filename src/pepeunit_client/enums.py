from enum import Enum


class LogLevel(Enum):
    DEBUG = 'Debug'
    INFO = 'Info'
    WARNING = 'Warning'
    ERROR = 'Error'
    CRITICAL = 'Critical'

    def get_int_level(self) -> int:
        level_mapping = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_mapping[self]


class BaseInputTopicType(Enum):
    UPDATE = "update"
    ENV_UPDATE = "env_update"
    SCHEMA_UPDATE = "schema_update"
    LOG_SYNC = "log_sync"
    RESET = "reset"


class BaseOutputTopicType(Enum):
    LOG = "log"
    STATE = "state"


class RestartMode(Enum):
    RESTART_POPEN = 'restart_popen'
    RESTART_EXEC = 'restart_exec'
    ENV_TOPICS_ONLY = 'env_topics_only'
    NO_RESTART = 'no_restart'
