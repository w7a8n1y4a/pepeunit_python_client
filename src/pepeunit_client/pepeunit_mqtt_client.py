import json
import time
from typing import Optional, Callable, List, Dict, Any, TYPE_CHECKING

from .protocols import MQTTClientProtocol
from .abstract_clients import AbstractPepeunitMqttClient

if TYPE_CHECKING:
    from .settings import Settings
    from .schema_manager import SchemaManager
    from .logger import Logger


class PepeunitMqttClient(AbstractPepeunitMqttClient):
    def __init__(self, settings: 'Settings', schema_manager: 'SchemaManager', logger: 'Logger'):
        super().__init__(settings, schema_manager, logger)
        self._client: Optional[MQTTClientProtocol] = None
        self._running = False
        self._input_handler: Optional[Callable] = None
        self._output_handler: Optional[Callable] = None
        self._last_state_send = 0
        
    def _get_paho_client(self) -> MQTTClientProtocol:
        try:
            from paho.mqtt import client as mqtt_client
            import uuid
            
            client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, str(uuid.uuid4()))
            client.username_pw_set(self.settings.PEPEUNIT_TOKEN, '')
            client.on_connect = self._on_connect
            client.on_message = self._on_message
            
            return client
        except ImportError:
            raise ImportError("paho-mqtt is required for MQTT functionality")
    
    def connect(self) -> None:
        if not self._client:
            self._client = self._get_paho_client()
        
        self._client.connect(self.settings.MQTT_URL, self.settings.MQTT_PORT)
        self._client.loop_start()
    
    def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self.logger.info("Connected to MQTT Broker!")
        else:
            self.logger.critical(f"Failed to connect to MQTT, return code {rc}")
    
    def _on_message(self, client, userdata, msg) -> None:
        try:
            self._base_mqtt_input_func(msg)
            
            if self._input_handler:
                self._input_handler(msg)
                
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {str(e)}")
    
    def _base_mqtt_input_func(self, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode()
        
        try:
            for topic_key in self.schema_manager.input_base_topic:
                if topic in self.schema_manager.input_base_topic[topic_key]:
                    if topic_key == 'update/pepeunit':
                        self._handle_update(payload)
                    elif topic_key == 'env_update/pepeunit':
                        self._handle_env_update()
                    elif topic_key == 'schema_update/pepeunit':
                        self._handle_schema_update()
                    elif topic_key == 'log_sync/pepeunit':
                        self._handle_log_sync()
                    break
        except Exception as e:
            self.logger.error(f"Error in base MQTT input handler: {str(e)}")
    
    def _handle_update(self, payload: str) -> None:
        self.logger.info("Update request received via MQTT")
    
    def _handle_env_update(self) -> None:
        self.logger.info("Env update request received via MQTT")
    
    def _handle_schema_update(self) -> None:
        self.logger.info("Schema update request received via MQTT")
    
    def _handle_log_sync(self) -> None:
        try:
            if 'log/pepeunit' in self.schema_manager.output_base_topic:
                topic = self.schema_manager.output_base_topic['log/pepeunit'][0]
                log_data = self.logger.get_full_log()
                self.publish(topic, json.dumps(log_data))
                self.logger.info("Log sync completed")
        except Exception as e:
            self.logger.error(f"Error during log sync: {str(e)}")
    
    def set_input_message_handler(self, handler: Callable) -> None:
        self._input_handler = handler
    
    def subscribe_topics(self, topics: List[str]) -> None:
        if self._client:
            for topic in topics:
                self._client.subscribe(topic)
    
    def subscribe_all_schema_topics(self) -> None:
        topics = []
        
        for topic_list in self.schema_manager.input_base_topic.values():
            topics.extend(topic_list)
            
        for topic_list in self.schema_manager.input_topic.values():
            topics.extend(topic_list)
            
        self.subscribe_topics(topics)
    
    def publish(self, topic: str, message: str) -> None:
        if self._client:
            self._client.publish(topic, message)
    
    def publish_to_topics(self, topic_key: str, message: str) -> None:
        topics = []
        
        if topic_key in self.schema_manager.output_topic:
            topics.extend(self.schema_manager.output_topic[topic_key])
        elif topic_key in self.schema_manager.output_base_topic:
            topics.extend(self.schema_manager.output_base_topic[topic_key])
            
        for topic in topics:
            self.publish(topic, message)
    
    def _base_mqtt_output_func(self) -> None:
        current_time = time.time()
        
        if 'state/pepeunit' in self.schema_manager.output_base_topic:
            if current_time - self._last_state_send >= self.settings.STATE_SEND_INTERVAL:
                topic = self.schema_manager.output_base_topic['state/pepeunit'][0]
                state_data = self._get_system_state()
                self.publish(topic, json.dumps(state_data))
                self._last_state_send = current_time
    
    def _get_system_state(self) -> Dict[str, Any]:
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            return {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'commit_version': self.settings.COMMIT_VERSION,
            }
        except ImportError:
            return {
                'millis': round(time.time() * 1000),
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': self.settings.COMMIT_VERSION,
            }
    
    def run_main_cycle(self, output_handler: Optional[Callable] = None) -> None:
        self._running = True
        self._output_handler = output_handler
        
        try:
            while self._running:
                self._base_mqtt_output_func()
                
                if self._output_handler:
                    self._output_handler()
                
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error in main cycle: {str(e)}")
        finally:
            self._running = False
    
    def stop_main_cycle(self) -> None:
        self._running = False
