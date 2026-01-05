import json
from typing import Optional, TYPE_CHECKING
import datetime

from .enums import LogLevel, BaseOutputTopicType
from .file_manager import FileManager

if TYPE_CHECKING:
    from .schema_manager import SchemaManager
    from .settings import Settings
    from .abstract_clients import AbstractPepeunitMqttClient


class Logger:
    def __init__(
        self,
        log_file_path: str,
        mqtt_client: Optional['AbstractPepeunitMqttClient'] = None, 
        schema_manager: Optional['SchemaManager'] = None,
        settings: Optional['Settings'] = None,
        ff_console_log_enable: bool = True
    ):
        self.log_file_path = log_file_path
        self.mqtt_client = mqtt_client
        self.schema_manager = schema_manager
        self.settings = settings
        self.ff_console_log_enable = ff_console_log_enable
    
    def _string_to_log_level(self, level_str: str) -> LogLevel:
        level_mapping = {
            'Debug': LogLevel.DEBUG,
            'Info': LogLevel.INFO,
            'Warning': LogLevel.WARNING,
            'Error': LogLevel.ERROR,
            'Critical': LogLevel.CRITICAL,
        }
        return level_mapping.get(level_str, LogLevel.DEBUG)
    
    def _should_log(self, level: LogLevel) -> bool:
        if not self.settings:
            return True
        
        minimal_level = self._string_to_log_level(self.settings.PU_MIN_LOG_LEVEL)
        return level.get_int_level() >= minimal_level.get_int_level()
    
    def _log(self, level: LogLevel, message: str, file_only: bool = False) -> None:
        if not self._should_log(level):
            return
            
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': self._get_current_datetime()
        }
        
        if self.ff_console_log_enable:
            print(log_entry)
        
        FileManager.append_ndjson_with_limit(self.log_file_path, log_entry, self.settings.PU_MAX_LOG_LENGTH)
        
        if not file_only and self.mqtt_client and BaseOutputTopicType.LOG_PEPEUNIT.value in self.schema_manager.output_base_topic:
            topic = self.schema_manager.output_base_topic[BaseOutputTopicType.LOG_PEPEUNIT.value][0]
            try:
                self.mqtt_client.publish(topic, json.dumps(log_entry))
            except Exception:
                pass
    
    def _get_current_datetime(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    def debug(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.DEBUG, message, file_only)
    
    def info(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.INFO, message, file_only)
    
    def warning(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.WARNING, message, file_only)
    
    def error(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.ERROR, message, file_only)
    
    def critical(self, message: str, file_only: bool = False) -> None:
        self._log(LogLevel.CRITICAL, message, file_only)
    
    def get_full_log(self) -> list:
        if not FileManager.file_exists(self.log_file_path):
            return []
        
        return list(FileManager.iter_ndjson(self.log_file_path))
    
    def iter_log(self):
        if not FileManager.file_exists(self.log_file_path):
            return
        
        for item in FileManager.iter_ndjson(self.log_file_path):
            yield item
    
    def reset_log(self) -> None:
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            pass
