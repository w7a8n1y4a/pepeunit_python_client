import json
import base64

from typing import Optional
from .file_manager import FileManager


class Settings:
    
    PU_DOMAIN: str = ''
    PU_HTTP_TYPE: str = 'https'
    PU_APP_PREFIX: str = ''
    PU_API_ACTUAL_PREFIX: str = ''
    PU_MQTT_HOST: str = ''
    PU_MQTT_PORT: int = 1883
    PU_MQTT_PING_INTERVAL: int = 20
    PU_MQTT_KEEPALIVE: int = 60
    PU_AUTH_TOKEN: str = ''
    PU_SECRET_KEY: str = ''
    PU_ENCRYPT_KEY: str = ''
    PU_STATE_SEND_INTERVAL: int = 300
    PU_MIN_LOG_LEVEL: str = 'Debug'
    PU_MAX_LOG_LENGTH: int = 64
    PU_COMMIT_VERSION: str = ''

    def __init__(self, env_file_path: Optional[str] = None, **kwargs) -> None:
        self.env_file_path = env_file_path
        self._env_keys = set()
        self._settings_overrides = kwargs
        
        if env_file_path:
            self.load_from_file()
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def unit_uuid(self) -> str:
        token_parts = self.PU_AUTH_TOKEN.split('.')
        if len(token_parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        payload = token_parts[1]
        payload += '=' * (-len(payload) % 4)
        
        decoded_payload = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        return payload_data['uuid']
    
    def load_from_file(self) -> None:
        if not self.env_file_path or not FileManager.file_exists(self.env_file_path):
            return
        
        env_data = FileManager.read_env(self.env_file_path)
        for key in self._env_keys - env_data.keys():
            if key in self._settings_overrides:
                setattr(self, key, self._settings_overrides[key])
            else:
                self.__dict__.pop(key, None)
        self._env_keys = set(env_data)
        for key, value in env_data.items():
            setattr(self, key, value)
