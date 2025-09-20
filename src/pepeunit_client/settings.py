from typing import Any, Dict
from .constants import ReservedEnvVariableName


class Settings:
    """
    Класс для типизированной работы с настройками из env.json
    
    Зарезервированные переменные доступны как атрибуты.
    Пользовательские переменные доступны через __getattr__.
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
        # Словарь для пользовательских переменных
        self._custom_variables = {}
        
        # Устанавливаем зарезервированные переменные
        reserved_names = {v for v in ReservedEnvVariableName.__dict__.values() if isinstance(v, str)}
        
        for key, value in kwargs.items():
            if key in reserved_names:
                setattr(self, key, value)
            else:
                # Пользовательские переменные сохраняем в отдельном словаре
                self._custom_variables[key] = value
    
    def __getattr__(self, name: str) -> Any:
        """Получает пользовательские переменные как атрибуты"""
        if name in self._custom_variables:
            return self._custom_variables[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Устанавливает атрибуты"""
        if name.startswith('_') or name in ReservedEnvVariableName.__dict__.values():
            # Зарезервированные переменные или служебные атрибуты
            super().__setattr__(name, value)
        else:
            # Пользовательские переменные
            if not hasattr(self, '_custom_variables'):
                super().__setattr__('_custom_variables', {})
            self._custom_variables[name] = value
    
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
        return self._custom_variables.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Возвращает все настройки в виде словаря"""
        result = self.get_reserved_variables()
        result.update(self._custom_variables)
        return result
    
    def update(self, **kwargs) -> None:
        """Обновляет настройки"""
        reserved_names = {v for v in ReservedEnvVariableName.__dict__.values() if isinstance(v, str)}
        
        for key, value in kwargs.items():
            if key in reserved_names:
                setattr(self, key, value)
            else:
                self._custom_variables[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение настройки по ключу"""
        try:
            return getattr(self, key)
        except AttributeError:
            return default
    
    def __repr__(self) -> str:
        """Строковое представление объекта"""
        reserved = self.get_reserved_variables()
        custom = self.get_custom_variables()
        return f"Settings(reserved={len(reserved)}, custom={len(custom)})"
