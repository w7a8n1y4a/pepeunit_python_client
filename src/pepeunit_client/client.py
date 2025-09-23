import json
import base64
import os
from typing import Optional, Dict, Any, List, Callable

from .settings import Settings
from .file_manager import FileManager
from .logger import Logger
from .schema_manager import SchemaManager
from .abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient
from .pepeunit_mqtt_client import PepeunitMqttClient
from .pepeunit_rest_client import PepeunitRestClient


class PepeunitClient:
    def __init__(
        self,
        env_file_path: str,
        schema_file_path: str,
        log_file_path: str,
        enable_mqtt: bool = False,
        enable_rest: bool = False,
        mqtt_client: Optional[AbstractPepeunitMqttClient] = None,
        rest_client: Optional[AbstractPepeunitRestClient] = None
    ):
        self.env_file_path = env_file_path
        self.schema_file_path = schema_file_path
        self.log_file_path = log_file_path
        self.enable_mqtt = enable_mqtt
        self.enable_rest = enable_rest
        
        self.settings = Settings(env_file_path)
        self.schema = SchemaManager(schema_file_path)

        self._mqtt_client = (mqtt_client if mqtt_client else self._get_default_mqtt_client()) if enable_mqtt else None
        self._rest_client = (rest_client if rest_client else self._get_default_rest_client()) if enable_rest else None
        
        self.logger = Logger(log_file_path, self._mqtt_client, self.schema)
        
        self._mqtt_input_handler: Optional[Callable] = None
        self._running = False
    
    
    def _get_default_mqtt_client(self) -> Optional[AbstractPepeunitMqttClient]:
        return PepeunitMqttClient(self.settings, self.schema, self.logger)
    
    def _get_default_rest_client(self) -> Optional[AbstractPepeunitRestClient]:
        return PepeunitRestClient(self.settings)
    
    @property
    def unit_uuid(self) -> str:
        token_parts = self.settings.PEPEUNIT_TOKEN.split('.')
        if len(token_parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        payload = token_parts[1]
        payload += '=' * (4 - len(payload) % 4)
        
        decoded_payload = base64.b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        return payload_data['uuid']
    
    def update_device_program(self, archive_path: str) -> None:
        extract_path = os.path.dirname(archive_path)
        FileManager.extract_tar_gz(archive_path, extract_path)
    
    def get_system_state(self) -> Dict[str, Any]:
        try:
            import psutil
            import time
            
            memory_info = psutil.virtual_memory()
            return {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'commit_version': self.settings.COMMIT_VERSION,
            }
        except ImportError:
            import time
            return {
                'millis': round(time.time() * 1000),
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': self.settings.COMMIT_VERSION,
            }
    
    
