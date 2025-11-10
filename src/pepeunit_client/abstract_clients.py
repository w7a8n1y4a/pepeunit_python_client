from abc import ABC, abstractmethod
from typing import Optional, Callable, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import Settings
    from .schema_manager import SchemaManager
    from .logger import Logger


class AbstractPepeunitMqttClient(ABC):
    """
    Abstract base class for Pepeunit MQTT clients.
    
    Users can inherit from this class to create custom MQTT clients
    that integrate with the Pepeunit ecosystem.
    """
    
    def __init__(self, settings: 'Settings', schema_manager: 'SchemaManager', logger: 'Logger'):
        self.settings = settings
        self.schema_manager = schema_manager
        self.logger = logger
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to MQTT broker using settings configuration."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        pass
    
    @abstractmethod
    def subscribe_topics(self, topics: List[str]) -> None:
        """
        Subscribe to specific MQTT topics.
        
        Args:
            topics: List of topic strings to subscribe to
        """
        pass
    
    @abstractmethod
    def publish(self, topic: str, message: str) -> None:
        """
        Publish message to specific topic.
        
        Args:
            topic: MQTT topic to publish to
            message: Message content to publish
        """
        pass
    
    @abstractmethod
    def set_input_handler(self, handler: Callable) -> None:
        """
        Set user-defined input message handler.
        
        Args:
            handler: Function to handle incoming MQTT messages
        """
        pass


class AbstractPepeunitRestClient(ABC):
    """
    Abstract base class for Pepeunit REST clients.
    
    Users can inherit from this class to create custom REST clients
    that integrate with the Pepeunit API.
    """
    
    def __init__(self, settings: 'Settings'):
        self.settings = settings
    
    @abstractmethod
    def download_update(self, file_path: str) -> None:
        """
        Download firmware update archive.
        
        Args:
            unit_uuid: UUID of the unit to download update for
            file_path: Local path where to save the downloaded file
        """
        pass
    
    @abstractmethod
    def download_env(self, file_path: str) -> None:
        """
        Download env.json configuration.
        
        Args:
            unit_uuid: UUID of the unit to download config for
            file_path: Local path where to save the env.json file
        """
        pass
    
    @abstractmethod
    def download_schema(self, file_path: str) -> None:
        """
        Download schema.json configuration.
        
        Args:
            unit_uuid: UUID of the unit to download schema for
            file_path: Local path where to save the schema.json file
        """
        pass
    
    @abstractmethod
    def set_state_storage(self, state: Dict[str, Any]) -> None:
        """
        Store state data in Pepeunit Unit Storage.
        
        Args:
            unit_uuid: UUID of the unit
            state: State data to store
        """
        pass
    
    @abstractmethod
    def get_state_storage(self, unit_uuid: str) -> Dict[str, Any]:
        """
        Retrieve state data from Pepeunit Unit Storage.
        
        Args:
            unit_uuid: UUID of the unit
            
        Returns:
            Retrieved state data
        """
        pass
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Users can override this if they need custom authentication.
        
        Returns:
            Dictionary with authentication headers
        """
        return {
            'accept': 'application/json',
            'x-auth-token': self.settings.PEPEUNIT_TOKEN,
        }
    
    def _get_base_url(self) -> str:
        """
        Get base URL for Pepeunit API.
        
        Users can override this if they need custom URL construction.
        
        Returns:
            Base URL string
        """
        return f"{self.settings.HTTP_TYPE}://{self.settings.PEPEUNIT_URL}{self.settings.PEPEUNIT_APP_PREFIX}{self.settings.PEPEUNIT_API_ACTUAL_PREFIX}"
