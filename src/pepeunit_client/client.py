import json
import base64
import os
import time
from typing import Optional, Dict, Any, List, Callable

from .settings import Settings
from .file_manager import FileManager
from .logger import Logger
from .schema_manager import SchemaManager
from .abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient
from .pepeunit_mqtt_client import PepeunitMqttClient
from .pepeunit_rest_client import PepeunitRestClient


class PepeunitClient:
    def __init__(
        self,
        env_file_path: str,
        schema_file_path: str,
        log_file_path: str,
        enable_mqtt: bool = False,
        enable_rest: bool = False,
        mqtt_client: Optional[AbstractPepeunitMqttClient] = None,
        rest_client: Optional[AbstractPepeunitRestClient] = None
    ):
        self.env_file_path = env_file_path
        self.schema_file_path = schema_file_path
        self.log_file_path = log_file_path
        self.enable_mqtt = enable_mqtt
        self.enable_rest = enable_rest
        
        self.settings = Settings(env_file_path)
        self.schema = SchemaManager(schema_file_path)

        self._mqtt_client = (mqtt_client if mqtt_client else self._get_default_mqtt_client()) if enable_mqtt else None
        self._rest_client = (rest_client if rest_client else self._get_default_rest_client()) if enable_rest else None
        
        self.logger = Logger(log_file_path, self._mqtt_client, self.schema)
        
        self._mqtt_input_handler: Optional[Callable] = None
        self._mqtt_output_handler: Optional[Callable] = None

        self._running = False
        self._last_state_send = 0
        
    def _get_default_mqtt_client(self) -> Optional[AbstractPepeunitMqttClient]:
        return PepeunitMqttClient(self.settings, self.schema, self.logger)
    
    def _get_default_rest_client(self) -> Optional[AbstractPepeunitRestClient]:
        return PepeunitRestClient(self.settings)
    
    @property
    def unit_uuid(self) -> str:
        token_parts = self.settings.PEPEUNIT_TOKEN.split('.')
        if len(token_parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        payload = token_parts[1]
        payload += '=' * (4 - len(payload) % 4)
        
        decoded_payload = base64.b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        return payload_data['uuid']
    
    def update_device_program(self, archive_path: str) -> None:
        extract_path = os.path.dirname(archive_path)
        FileManager.extract_tar_gz(archive_path, extract_path)
    
    def get_system_state(self) -> Dict[str, Any]:
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
    
    def set_input_message_handler(self, handler: Callable) -> None:
        self._mqtt_input_handler = handler
        if self._mqtt_client:
            def combined_handler(msg):
                self._base_mqtt_input_func(msg)
                if self._mqtt_input_handler:
                    self._mqtt_input_handler(msg)
            self._mqtt_client.set_input_message_handler(combined_handler)

    def _base_mqtt_input_func(self, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode()
        
        try:
            for topic_key in self.schema.input_base_topic:
                if topic in self.schema.input_base_topic[topic_key]:
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
            if 'log/pepeunit' in self.schema.output_base_topic:
                topic = self.schema.output_base_topic['log/pepeunit'][0]
                log_data = self.logger.get_full_log()
                if self._mqtt_client:
                    self._mqtt_client.publish(topic, json.dumps(log_data))
                self.logger.info("Log sync completed")
        except Exception as e:
            self.logger.error(f"Error during log sync: {str(e)}")

    def subscribe_all_schema_topics(self) -> None:
        topics = []
        
        for topic_list in self.schema_manager.input_base_topic.values():
            topics.extend(topic_list)
            
        for topic_list in self.schema_manager.input_topic.values():
            topics.extend(topic_list)
            
        self._mqtt_client.subscribe_topics(topics)

    def publish_to_topics(self, topic_key: str, message: str) -> None:
        topics = []
        
        if topic_key in self.schema_manager.output_topic:
            topics.extend(self.schema_manager.output_topic[topic_key])
        elif topic_key in self.schema_manager.output_base_topic:
            topics.extend(self.schema_manager.output_base_topic[topic_key])
            
        for topic in topics:
            self._mqtt_client.publish(topic, message)
    
    def _base_mqtt_output_handler(self) -> None:
        current_time = time.time()
        
        if 'state/pepeunit' in self.schema.output_base_topic:
            if current_time - self._last_state_send >= self.settings.STATE_SEND_INTERVAL:
                topic = self.schema.output_base_topic['state/pepeunit'][0]
                state_data = self.get_system_state()
                if self._mqtt_client:
                    self._mqtt_client.publish(topic, json.dumps(state_data))
                self._last_state_send = current_time
    
    def run_main_cycle(self, output_handler: Optional[Callable] = None) -> None:
        self._running = True
        if output_handler:
            self._mqtt_output_handler = output_handler
        
        try:
            while self._running:
                self._base_mqtt_output_handler()
                
                if self._mqtt_output_handler:
                    self._mqtt_output_handler()
                
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Error in main cycle: {str(e)}")
        finally:
            self._running = False
    
    def set_output_handler(self, output_handler: Callable) -> None:
        self._mqtt_output_handler = output_handler

    def stop_main_cycle(self) -> None:
        self._running = False
    
    
