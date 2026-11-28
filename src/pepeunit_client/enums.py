from enum import Enum, StrEnum


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
    IO_TOPICS_UPDATE = "io_topics_update"
    LOG_SYNC = "log_sync"
    RESET = "reset"


class BackendTopicCommand(Enum):
    UPDATE = "Update"
    ENV_UPDATE = "EnvUpdate"
    IO_TOPICS_UPDATE = "IOTopicsUpdate"
    LOG_SYNC = "LogSync"
    RESET = "Reset"


class BackendTopicCommandKey(StrEnum):
    COMMAND = "command"
    COMMIT_VERSION = "pu_commit_version"
    COMPILED_FIRMWARE_LINK = "compiled_firmware_link"


class BaseOutputTopicType(Enum):
    LOG = "log"
    STATE = "state"


class RestartMode(Enum):
    RESTART_EXEC = 'restart_exec'
    ENV_TOPICS_ONLY = 'env_topics_only'
    NO_RESTART = 'no_restart'
