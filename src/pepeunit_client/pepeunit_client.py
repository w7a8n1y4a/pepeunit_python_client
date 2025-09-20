
import json
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .enums import LogLevel
from .settings import Settings
from .file_manager import FileManager
from .interfaces import MQTTClientInterface, RESTClientInterface


class PepeunitClient:
    
    def __init__(
        self,
        env_path: str,
        schema_path: str,
        log_path: str,
        mqtt_client: Optional[MQTTClientInterface] = None,
        rest_client: Optional[RESTClientInterface] = None
    ) -> None:
        self.env_path = Path(env_path)
        self.schema_path = Path(schema_path)
        self.log_path = Path(log_path)
        self.mqtt_client = mqtt_client
        self.rest_client = rest_client
        
        self._env_data = FileManager.load_json_file(self.env_path)
        self._schema_data = FileManager.load_json_file(self.schema_path)
        self._log_data = FileManager.load_json_file(self.log_path)
        
        self.settings = Settings(**self._env_data) if isinstance(self._env_data, dict) else Settings()
    
    
    def _log(self, level: LogLevel, message: str) -> None:
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        }
        
        if isinstance(self._log_data, list):
            self._log_data.append(log_entry)
        else:
            self._log_data = [log_entry]
        
        FileManager.save_json_file(self.log_path, self._log_data)
        
        if self.mqtt_client and level.get_int_level() >= LogLevel.INFO.get_int_level():
            try:
                topic = self.get_topic_by_key('log/pepeunit')
                if topic:
                    self.mqtt_client.publish(topic, json.dumps(log_entry))
            except Exception as e:
                print(f"MQTT log send error: {e}")
    
    
    def update_env_from_file(self, file_path: str) -> None:
        try:
            new_env_data = FileManager.load_json_file(Path(file_path))
            self._env_data = new_env_data
            self.settings = Settings(**new_env_data) if isinstance(new_env_data, dict) else Settings()
            FileManager.save_json_file(self.env_path, self._env_data)
            self._log(LogLevel.INFO, f"env.json updated from file {file_path}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"env.json update error: {e}")
    
    def update_env(self, env_dict: Dict[str, Any]) -> None:
        try:
            self._env_data.update(env_dict)
            self.settings.update(**env_dict)
            FileManager.save_json_file(self.env_path, self._env_data)
            self._log(LogLevel.INFO, "env.json updated")
        except Exception as e:
            self._log(LogLevel.ERROR, f"env.json update error: {e}")
    
    def get_env_value(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)
    
    def get_env_data(self) -> Dict[str, Any]:
        return self.settings.to_dict()
    
    def get_reserved_settings(self) -> Dict[str, Any]:
        return self.settings.get_reserved_variables()
    
    def get_custom_settings(self) -> Dict[str, Any]:
        return self.settings.get_custom_variables()
    
    
    def update_schema_from_file(self, file_path: str) -> None:
        try:
            new_schema_data = FileManager.load_json_file(Path(file_path))
            self._schema_data = new_schema_data
            FileManager.save_json_file(self.schema_path, self._schema_data)
            self._log(LogLevel.INFO, f"schema.json updated from file {file_path}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"schema.json update error: {e}")
    
    def update_schema(self, schema_dict: Dict[str, Any]) -> None:
        try:
            self._schema_data.update(schema_dict)
            FileManager.save_json_file(self.schema_path, self._schema_data)
            self._log(LogLevel.INFO, "schema.json updated")
        except Exception as e:
            self._log(LogLevel.ERROR, f"schema.json update error: {e}")
    
    def get_schema_value(self, key: str, default: Any = None) -> Any:
        return self._schema_data.get(key, default)
    
    def get_schema_data(self) -> Dict[str, Any]:
        return self._schema_data.copy()
    
    
    def get_input_topics(self) -> List[str]:
        input_topics = []
        for topic_type in self._schema_data.keys():
            if 'input' in topic_type:
                for topic in self._schema_data[topic_type].keys():
                    if isinstance(self._schema_data[topic_type][topic], list):
                        input_topics.extend(self._schema_data[topic_type][topic])
                    else:
                        input_topics.append(self._schema_data[topic_type][topic])
        return input_topics
    
    def get_topic_by_key(self, key: str) -> Optional[str]:
        for topic_type in self._schema_data.keys():
            if topic_type in ['output_base_topic', 'input_base_topic']:
                if key in self._schema_data[topic_type]:
                    topics = self._schema_data[topic_type][key]
                    if isinstance(topics, list) and topics:
                        return topics[0]
                    elif isinstance(topics, str):
                        return topics
        return None
    
    def search_topic_in_schema(self, node_uuid: str) -> Optional[tuple[str, str]]:
        for topic_type in self._schema_data.keys():
            for topic_name in self._schema_data[topic_type].keys():
                topics = self._schema_data[topic_type][topic_name]
                if isinstance(topics, list):
                    for topic in topics:
                        if node_uuid in topic:
                            return topic_type, topic_name
                elif isinstance(topics, str) and node_uuid in topics:
                    return topic_type, topic_name
        return None
    
    
    
    
    def generate_device_state(self) -> Dict[str, Any]:
        try:
            import psutil  # type: ignore
            
            memory_info = psutil.virtual_memory()
            cpu_freq = psutil.cpu_freq()
            
            state = {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': cpu_freq.current if cpu_freq else 0,
                'commit_version': self.settings.COMMIT_VERSION or 'unknown',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
            
            return state
        except ImportError:
            return {
                'millis': round(time.time() * 1000),
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': self.settings.COMMIT_VERSION or 'unknown',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
        except Exception as e:
            self._log(LogLevel.ERROR, f"Device state generation error: {e}")
            return {
                'millis': round(time.time() * 1000),
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
    
    
    def save_log(self, level: LogLevel, message: str) -> None:
        self._log(level, message)
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        if isinstance(self._log_data, list):
            return self._log_data.copy()
        return []
    
    def clear_logs(self) -> None:
        self._log_data = []
        FileManager.save_json_file(self.log_path, self._log_data)
    
    
    def send_mqtt_message(self, topic: str, message: str) -> bool:
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT client not configured")
            return False
        
        try:
            self.mqtt_client.publish(topic, message)
            self._log(LogLevel.DEBUG, f"Message sent to topic {topic}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"MQTT message send error: {e}")
            return False
    
    def subscribe_to_topics(self, topics: List[str]) -> bool:
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT client not configured")
            return False
        
        try:
            self.mqtt_client.subscribe(topics)
            self._log(LogLevel.INFO, f"Subscribed to topics: {topics}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Topics subscription error: {e}")
            return False
    
    def send_log_via_mqtt(self, level: LogLevel, message: str, save_to_file: bool = True) -> bool:
        if not self.mqtt_client:
            if save_to_file:
                self.save_log(level, message)
            return False
        
        topic = self.get_topic_by_key('log/pepeunit')
        if not topic:
            if save_to_file:
                self.save_log(LogLevel.WARNING, "Log topic not found in schema")
            return False
        
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        }
        
        if save_to_file:
            if isinstance(self._log_data, list):
                self._log_data.append(log_entry)
            else:
                self._log_data = [log_entry]
            FileManager.save_json_file(self.log_path, self._log_data)
        
        return self.send_mqtt_message(topic, json.dumps(log_entry))
    
