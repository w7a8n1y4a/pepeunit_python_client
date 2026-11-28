from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

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
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
    
    @abstractmethod
    def set_subscriptions(self, topics: dict[str, int]) -> None:
        """Apply the current topic-to-QoS mapping for all inputs."""

    @abstractmethod
    def publish(self, topic: str, message: Any, qos: int = 0) -> Any:
        """Publish the encoded payload using the specified QoS."""

    @abstractmethod
    def set_input_handler(self, handler: Callable) -> None:
        """
        Set user-defined input message handler.
        
        Args:
            handler: Function to handle incoming MQTT messages
        """


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
            file_path: Local path where to save the downloaded file
        """
    
    @abstractmethod
    def download_env(self, file_path: str) -> None:
        """
        Download the device .env configuration.
        
        Args:
            file_path: Local path for the downloaded configuration
        """
    
    @abstractmethod
    def get_io_topics(self) -> "IOTopics":
        """Fetch and decode the unit's io_topics.yml."""

    @abstractmethod
    def set_state_storage(self, state: str) -> None:
        """Store a string in Pepeunit Unit Storage."""
    
    @abstractmethod
    def get_state_storage(self) -> str:
        """Retrieve the stored string from Pepeunit Unit Storage."""
    
    @abstractmethod
    def get_input_by_output(self, topic: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """Return the linked inputs in the response's unit_ios list."""

    @abstractmethod
    def get_units_by_ios(self, unit_io_uuids: list[str], limit: int = 100, offset: int = 0) -> dict[str, Any]:
        """Return units filtered by UnitIO UUIDs."""

    def _get_auth_headers(self) -> dict[str, str]:
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
