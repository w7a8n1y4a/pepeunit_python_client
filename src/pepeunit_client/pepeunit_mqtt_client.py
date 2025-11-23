from typing import Optional, Callable, List, TYPE_CHECKING, Any

from .abstract_clients import AbstractPepeunitMqttClient

# Import for mocking in tests
try:
    from paho.mqtt import client as mqtt_client_paho
    import uuid
except ImportError:
    mqtt_client_paho = None
    uuid = None

if TYPE_CHECKING:
    from .settings import Settings
    from .schema_manager import SchemaManager
    from .logger import Logger


class PepeunitMqttClient(AbstractPepeunitMqttClient):
    def __init__(self, settings: 'Settings', schema_manager: 'SchemaManager', logger: 'Logger'):
        super().__init__(settings, schema_manager, logger)
        self._client: Optional[Any] = None
        self._input_handler: Optional[Callable] = None
        
    def _get_client(self) -> Any:
        if mqtt_client_paho is None or uuid is None:
            raise ImportError("paho-mqtt is required for MQTT functionality")
            
        client = mqtt_client_paho.Client(mqtt_client_paho.CallbackAPIVersion.VERSION1, self.settings.unit_uuid)
        client.username_pw_set(self.settings.PU_AUTH_TOKEN, '')
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        
        return client
    
    def connect(self) -> None:
        if not self._client:
            self._client = self._get_client()
        
        self._client.connect(self.settings.PU_MQTT_HOST, self.settings.PU_MQTT_PORT)
        self._client.loop_start()
    
    def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self.logger.info(f"Disconnected from MQTT Broker", file_only=True)
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self.logger.info("Connected to MQTT Broker")
        else:
            self.logger.error(f"Error to connect to MQTT, return code {rc}", file_only=True)
    
    def _on_message(self, client, userdata, msg) -> None:

        msg.payload = msg.payload.decode()
        try:
            if self._input_handler:
                self._input_handler(msg)
                
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {str(e)}")
    
    def set_input_handler(self, handler: Callable) -> None:
        self._input_handler = handler
    
    def subscribe_topics(self, topics: List[str]) -> None:
        if self._client:
            for topic in topics:
                self._client.subscribe(topic)
            self.logger.info(f'Success subscribed to {len(topics)} topics')
    
    def publish(self, topic: str, message: str) -> None:
        if self._client:
            self._client.publish(topic, message)
    