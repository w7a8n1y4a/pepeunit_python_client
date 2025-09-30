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


class SearchTopicType(Enum):
    UNIT_NODE_UUID = 'unit_node_uuid'
    FULL_NAME = 'full_name'


class SearchScope(Enum):
    ALL = 'all'
    INPUT = 'input'
    OUTPUT = 'output'


class DestinationTopicType(Enum):
    INPUT_BASE_TOPIC = 'input_base_topic'
    OUTPUT_BASE_TOPIC = 'output_base_topic'
    INPUT_TOPIC = 'input_topic'
    OUTPUT_TOPIC = 'output_topic'


class BaseInputTopicType(Enum):
    UPDATE_PEPEUNIT = 'update/pepeunit'
    ENV_UPDATE_PEPEUNIT = 'env_update/pepeunit'
    SCHEMA_UPDATE_PEPEUNIT = 'schema_update/pepeunit'
    LOG_SYNC_PEPEUNIT = 'log_sync/pepeunit'


class BaseOutputTopicType(Enum):
    LOG_PEPEUNIT = 'log/pepeunit'
    STATE_PEPEUNIT = 'state/pepeunit'


class RestartMode(Enum):
    RESTART_POPEN = 'restart_popen'
    RESTART_EXEC = 'restart_exec'
    ENV_SCHEMA_ONLY = 'env_schema_only'
    NO_RESTART = 'no_restart'
