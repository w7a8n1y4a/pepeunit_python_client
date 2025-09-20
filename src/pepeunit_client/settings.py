from re import I
from typing import Any, Dict
from .enums import ReservedEnvVariableName


class Settings:
    """
    Простой класс для работы с настройками из env.json
    
    Все переменные (зарезервированные и пользовательские) доступны как атрибуты.
    Зарезервированные переменные имеют значения по умолчанию.
    """
    
    # Зарезервированные переменные с значениями по умолчанию
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

    def __init__(self, **kwargs):
        """
        Инициализация настроек
        
        Args:
            **kwargs: Словарь с настройками из env.json
        """
        # Устанавливаем все переменные как атрибуты
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_reserved_variables(self) -> Dict[str, Any]:
        """Возвращает только зарезервированные переменные"""
        reserved = {}
        reserved_names = {v for v in ReservedEnvVariableName.__dict__.values() if isinstance(v, str)}
        
        for name in reserved_names:
            if hasattr(self, name):
                reserved[name] = getattr(self, name)
        return reserved
    
    def get_custom_variables(self) -> Dict[str, Any]:
        """Возвращает только пользовательские переменные"""
        reserved_names = {v for v in ReservedEnvVariableName.__dict__.values() if isinstance(v, str)}
        custom = {}
        
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key not in reserved_names:
                custom[key] = value
        return custom
    
    def to_dict(self) -> Dict[str, Any]:
        """Возвращает все настройки в виде словаря"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    def update(self, **kwargs) -> None:
        """Обновляет настройки"""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение настройки по ключу"""
        return getattr(self, key, default)
    
    def __repr__(self) -> str:
        """Строковое представление объекта"""
        reserved = self.get_reserved_variables()
        custom = self.get_custom_variables()
        return f"Settings(reserved={len(reserved)}, custom={len(custom)})"
