from typing import Any, Dict
from .enums import ReservedEnvVariableName


class Settings:
    """
    Simple class for working with settings from env.json
    
    All variables (reserved and custom) are available as attributes.
    Reserved variables have default values.
    """
    
    # Reserved variables with default values
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

    def __init__(self, **kwargs) -> None:
        """
        Initialize settings
        
        Args:
            **kwargs: Dictionary with settings from env.json
        """
        # Set all variables as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_reserved_variables(self) -> Dict[str, Any]:
        """Returns only reserved variables"""
        reserved = {}
        reserved_names = {v for v in ReservedEnvVariableName.__dict__.values() if isinstance(v, str)}
        
        for name in reserved_names:
            if hasattr(self, name):
                reserved[name] = getattr(self, name)
        return reserved
    
    def get_custom_variables(self) -> Dict[str, Any]:
        """Returns only custom variables"""
        reserved_names = {v for v in ReservedEnvVariableName.__dict__.values() if isinstance(v, str)}
        custom = {}
        
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key not in reserved_names:
                custom[key] = value
        return custom
    
    def to_dict(self) -> Dict[str, Any]:
        """Returns all settings as dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    def update(self, **kwargs) -> None:
        """Updates settings"""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Gets setting value by key"""
        return getattr(self, key, default)
    
    def __repr__(self) -> str:
        """String representation of object"""
        reserved = self.get_reserved_variables()
        custom = self.get_custom_variables()
        return f"Settings(reserved={len(reserved)}, custom={len(custom)})"
