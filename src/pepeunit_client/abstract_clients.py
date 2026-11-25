from abc import ABC, abstractmethod
from typing import Optional, Callable, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import Settings
    from .io_topics import IOTopics
    from .logger import Logger


class AbstractPepeunitMqttClient(ABC):
    """
    Abstract base class for Pepeunit MQTT clients.
    
    Users can inherit from this class to create custom MQTT clients
    that integrate with the Pepeunit ecosystem.
    """
    
    def __init__(self, settings: 'Settings', logger: 'Logger'):
        self.settings = settings
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
    def set_subscriptions(self, topics: Dict[str, int]) -> None:
        """Apply the current topic-to-QoS mapping for all inputs."""
        pass

    @abstractmethod
    def publish(self, topic: str, message: Any, qos: int = 0) -> Any:
        """Publish the encoded payload using the specified QoS."""
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
        Download the device .env configuration.
        
        Args:
            file_path: Local path for the downloaded configuration
        """
        pass
    
    @abstractmethod
    def get_io_topics(self) -> "IOTopics":
        """Fetch and decode the unit's io_topics.yml."""
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
    
    @abstractmethod
    def get_input_by_output(self, topic: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Return the linked inputs in the response's unit_ios list."""
        pass

    @abstractmethod
    def get_units_by_ios(self, unit_io_uuids: List[str], limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Return units filtered by UnitIO UUIDs."""
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
            'x-auth-token': self.settings.PU_AUTH_TOKEN,
        }
    
    def _get_base_url(self) -> str:
        """
        Get base URL for Pepeunit API.
        
        Users can override this if they need custom URL construction.
        
        Returns:
            Base URL string
        """
        return f"{self.settings.PU_HTTP_TYPE}://{self.settings.PU_DOMAIN}{self.settings.PU_APP_PREFIX}{self.settings.PU_API_ACTUAL_PREFIX}"
