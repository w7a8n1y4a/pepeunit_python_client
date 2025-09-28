from typing import Any, Dict, Optional
from .file_manager import FileManager


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
    MINIMAL_LOG_LEVEL: str = 'Debug'

    def __init__(self, env_file_path: Optional[str] = None, **kwargs) -> None:
        self.env_file_path = env_file_path
        
        if env_file_path:
            self.load_from_file()
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def load_from_file(self) -> None:
        if not self.env_file_path or not FileManager.file_exists(self.env_file_path):
            return
        
        env_data = FileManager.read_json(self.env_file_path)
        for key, value in env_data.items():
            setattr(self, key, value)
    
    def reload(self) -> None:
        self.load_from_file()
    
    def update_from_file(self) -> None:
        """Метод для обновления настроек из файла (алиас для reload)."""
        self.reload()
    
    def get_env_values(self) -> Dict[str, Any]:
        if not self.env_file_path or not FileManager.file_exists(self.env_file_path):
            return {}
        return FileManager.read_json(self.env_file_path)
    
    def update_env_file(self, new_env_file_path: str) -> None:
        if not self.env_file_path:
            raise ValueError("env_file_path not set")
        
        FileManager.copy_file(new_env_file_path, self.env_file_path)
        self.load_from_file()
    
    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
