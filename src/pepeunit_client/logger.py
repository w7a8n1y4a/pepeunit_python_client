import json
from typing import Optional, Dict, Any, TYPE_CHECKING

from .enums import LogLevel
from .protocols import MQTTClientProtocol
from .file_manager import FileManager

if TYPE_CHECKING:
    from .schema_manager import SchemaManager


class Logger:
    def __init__(self, log_file_path: str, mqtt_client: Optional[MQTTClientProtocol] = None, 
                 schema_manager: Optional['SchemaManager'] = None):
        self.log_file_path = log_file_path
        self.mqtt_client = mqtt_client
        self.schema_manager = schema_manager
    
    def _log(self, level: LogLevel, message: str) -> None:
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': self._get_current_datetime()
        }
        
        self._write_to_file(log_entry)
        
        if self.mqtt_client and self.schema_manager:
            self._send_mqtt(log_entry)
    
    def _write_to_file(self, log_entry: Dict[str, Any]) -> None:
        FileManager.append_to_json_list(self.log_file_path, log_entry)
    
    def _send_mqtt(self, log_entry: Dict[str, Any]) -> None:
        try:
            if 'log/pepeunit' in self.schema_manager.output_base_topic:
                topic = self.schema_manager.output_base_topic['log/pepeunit'][0]
                self.mqtt_client.publish(topic, json.dumps(log_entry))
        except Exception:
            pass
    
    def _get_current_datetime(self) -> str:
        import datetime
        return datetime.datetime.utcnow().isoformat()
    
    def debug(self, message: str) -> None:
        self._log(LogLevel.DEBUG, message)
    
    def info(self, message: str) -> None:
        self._log(LogLevel.INFO, message)
    
    def warning(self, message: str) -> None:
        self._log(LogLevel.WARNING, message)
    
    def error(self, message: str) -> None:
        self._log(LogLevel.ERROR, message)
    
    def critical(self, message: str) -> None:
        self._log(LogLevel.CRITICAL, message)
    
    def get_full_log(self) -> list:
        if not FileManager.file_exists(self.log_file_path):
            return []
        
        return FileManager.read_json(self.log_file_path)
