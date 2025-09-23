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
    def set_input_message_handler(self, handler: Callable) -> None:
        """
        Set user-defined input message handler.
        
        Args:
            handler: Function to handle incoming MQTT messages
        """
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
    def subscribe_all_schema_topics(self) -> None:
        """Subscribe to all topics defined in schema (input_base_topic and input_topic)."""
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
    def publish_to_topics(self, topic_key: str, message: str) -> None:
        """
        Publish message to all topics associated with topic_key from schema.
        
        Args:
            topic_key: Key from schema (e.g., 'output/pepeunit')
            message: Message content to publish
        """
        pass
    
    @abstractmethod
    def run_main_cycle(self, output_handler: Optional[Callable] = None) -> None:
        """
        Run the main application cycle.
        
        This method should:
        - Call base_mqtt_output_func() for system state publishing
        - Call user-provided output_handler if provided
        - Run in a loop until stop_main_cycle() is called
        - Handle exceptions and log them appropriately
        
        Args:
            output_handler: Optional user-defined function for custom output logic
        """
        pass
    
    @abstractmethod
    def stop_main_cycle(self) -> None:
        """Stop the main application cycle."""
        pass
    
    def _base_mqtt_input_func(self, msg) -> None:
        """
        Base input handler for Pepeunit system messages.
        
        This method should handle:
        - update/pepeunit: Trigger update process
        - env_update/pepeunit: Download and apply new env.json
        - schema_update/pepeunit: Download and apply new schema.json
        - log_sync/pepeunit: Publish full log to output topic
        
        Users can override this if they need custom base functionality.
        """
        pass
    
    def _base_mqtt_output_func(self) -> None:
        """
        Base output handler for Pepeunit system messages.
        
        This method should handle:
        - state/pepeunit: Publish system state at configured intervals
        - log/pepeunit: Publish log messages if enabled
        
        Users can override this if they need custom base functionality.
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
    def download_update(self, unit_uuid: str, file_path: str) -> None:
        """
        Download firmware update archive.
        
        Args:
            unit_uuid: UUID of the unit to download update for
            file_path: Local path where to save the downloaded file
        """
        pass
    
    @abstractmethod
    def download_env(self, unit_uuid: str, file_path: str) -> None:
        """
        Download env.json configuration.
        
        Args:
            unit_uuid: UUID of the unit to download config for
            file_path: Local path where to save the env.json file
        """
        pass
    
    @abstractmethod
    def download_schema(self, unit_uuid: str, file_path: str) -> None:
        """
        Download schema.json configuration.
        
        Args:
            unit_uuid: UUID of the unit to download schema for
            file_path: Local path where to save the schema.json file
        """
        pass
    
    @abstractmethod
    def set_state_storage(self, unit_uuid: str, state: Dict[str, Any]) -> None:
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
