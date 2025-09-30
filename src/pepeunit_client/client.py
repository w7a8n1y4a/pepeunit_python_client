import json
import base64
import os
import tempfile
import time
from typing import Optional, Dict, Any, List, Callable

from .settings import Settings
from .file_manager import FileManager
from .logger import Logger
from .schema_manager import SchemaManager
from .abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient
from .pepeunit_mqtt_client import PepeunitMqttClient
from .pepeunit_rest_client import PepeunitRestClient
from .enums import BaseInputTopicType, BaseOutputTopicType


class PepeunitClient:
    def __init__(
        self,
        env_file_path: str,
        schema_file_path: str,
        log_file_path: str,
        enable_mqtt: bool = False,
        enable_rest: bool = False,
        mqtt_client: Optional[AbstractPepeunitMqttClient] = None,
        rest_client: Optional[AbstractPepeunitRestClient] = None,
        cycle_speed: float = 0.1
    ):
        self.env_file_path = env_file_path
        self.schema_file_path = schema_file_path
        self.log_file_path = log_file_path
        self.enable_mqtt = enable_mqtt
        self.enable_rest = enable_rest
        self.cycle_speed = cycle_speed
        
        self.settings = Settings(env_file_path)
        self.schema = SchemaManager(schema_file_path)
        
        self.logger = Logger(log_file_path, None, self.schema, self.settings)

        self.mqtt_client = (mqtt_client if mqtt_client else self._get_default_mqtt_client()) if enable_mqtt else None
        self.rest_client = (rest_client if rest_client else self._get_default_rest_client()) if enable_rest else None
        
        if self.mqtt_client:
            self.logger.mqtt_client = self.mqtt_client
        
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
    
    def set_cycle_speed(self, speed: float) -> None:
        if speed <= 0:
            raise ValueError("Cycle speed must be greater than 0")
        self.cycle_speed = speed
    
    def update_device_program(self, archive_path: str) -> None:
        import tempfile
        import sys
        import subprocess
        
        unit_directory = os.path.dirname(self.env_file_path) or os.getcwd()
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            FileManager.extract_tar_gz(archive_path, temp_extract_dir)
            
            FileManager.copy_directory_contents(temp_extract_dir, unit_directory)
        
        self.logger.info('Stop main cycle')
        self.stop_main_cycle()
        
        self.logger.info('I`ll Be Back')

        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    
    def get_system_state(self) -> Dict[str, Any]:
        try:
            import psutil
            
            memory_info = psutil.virtual_memory()
            
            try:
                cpu_freq = psutil.cpu_freq()
                freq = cpu_freq.current if cpu_freq else 0
            except (AttributeError, OSError):
                freq = 0
            
            return {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': freq,
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
    
    def set_mqtt_input_handler(self, handler: Callable) -> None:
        self._mqtt_input_handler = handler
        if self.mqtt_client:
            def combined_handler(msg):
                self._base_mqtt_input_func(msg)
                if self._mqtt_input_handler:
                    self._mqtt_input_handler(self, msg)
            self.mqtt_client.set_input_handler(combined_handler)

    def _base_mqtt_input_func(self, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode()
        
        try:
            for topic_key in self.schema.input_base_topic:
                if topic in self.schema.input_base_topic[topic_key]:
                    if topic_key == BaseInputTopicType.UPDATE_PEPEUNIT.value:
                        self._handle_update(payload)
                    elif topic_key == BaseInputTopicType.ENV_UPDATE_PEPEUNIT.value:
                        self._handle_env_update()
                    elif topic_key == BaseInputTopicType.SCHEMA_UPDATE_PEPEUNIT.value:
                        self._handle_schema_update()
                    elif topic_key == BaseInputTopicType.LOG_SYNC_PEPEUNIT.value:
                        self._handle_log_sync()
                    break
        except Exception as e:
            self.logger.error(f"Error in base MQTT input handler: {str(e)}")
    
    def download_update(self, archive_path: str) -> None:
        if not self.enable_rest or not self.rest_client:
            raise RuntimeError("REST client is not enabled or available")
        
        self.rest_client.download_update(self.unit_uuid, archive_path)
        self.logger.info(f"Update archive downloaded to {archive_path}")
    
    def download_env(self, file_path: str) -> None:
        if not self.enable_rest or not self.rest_client:
            raise RuntimeError("REST client is not enabled or available")
        
        self.rest_client.download_env(self.unit_uuid, file_path)
        self.settings.load_from_file()
        self.logger.info(f"Environment file downloaded and updated from {file_path}")
    
    def download_schema(self, file_path: str) -> None:
        if not self.enable_rest or not self.rest_client:
            raise RuntimeError("REST client is not enabled or available")
        
        self.rest_client.download_schema(self.unit_uuid, file_path)
        self.schema.update_from_file()
        self.logger.info(f"Schema file downloaded and updated from {file_path}")
    
    def set_state_storage(self, state: Dict[str, Any]) -> None:
        if not self.enable_rest or not self.rest_client:
            raise RuntimeError("REST client is not enabled or available")
        
        self.rest_client.set_state_storage(self.unit_uuid, state)
        self.logger.info("State uploaded to Pepeunit Unit Storage")
    
    def get_state_storage(self) -> Dict[str, Any]:
        if not self.enable_rest or not self.rest_client:
            raise RuntimeError("REST client is not enabled or available")
        
        state = self.rest_client.get_state_storage(self.unit_uuid)
        self.logger.info("State retrieved from Pepeunit Unit Storage")
        return state
    
    def perform_update(self) -> None:
        if not (self.enable_mqtt and self.enable_rest):
            raise RuntimeError("Both MQTT and REST clients must be enabled for perform_update")
        
        try:
            temp_dir = tempfile.gettempdir()
            archive_path = os.path.join(temp_dir, f"update_{self.unit_uuid}.tar.gz")
            
            self.download_update(archive_path)
            self.update_device_program(archive_path)
            os.remove(archive_path)
            self.logger.info("Full update cycle completed successfully")
        except Exception as e:
            self.logger.error(f"Update failed: {str(e)}")
            raise
        
    def _handle_update(self, payload: str) -> None:
        self.logger.info("Update request received via MQTT")
        if self.enable_rest and self.rest_client:
            try:
                self.perform_update()
            except Exception as e:
                self.logger.error(f"Failed to perform update: {str(e)}")
        else:
            self.logger.warning("REST client not available for update")
    
    def _handle_env_update(self) -> None:
        self.logger.info("Env update request received via MQTT")
        if self.enable_rest and self.rest_client:
            try:
                self.download_env(self.env_file_path)
            except Exception as e:
                self.logger.error(f"Failed to update env: {str(e)}")
        else:
            self.logger.warning("REST client not available for env update")
    
    def _handle_schema_update(self) -> None:
        self.logger.info("Schema update request received via MQTT")
        if self.enable_rest and self.rest_client:
            try:
                self.download_schema(self.schema_file_path)
                if self.enable_mqtt and self.mqtt_client:
                    self.subscribe_all_schema_topics()
            except Exception as e:
                self.logger.error(f"Failed to update schema: {str(e)}")
        else:
            self.logger.warning("REST client not available for schema update")
    
    def _handle_log_sync(self) -> None:
        try:
            if BaseOutputTopicType.LOG_PEPEUNIT.value in self.schema.output_base_topic:
                topic = self.schema.output_base_topic[BaseOutputTopicType.LOG_PEPEUNIT.value][0]
                log_data = self.logger.get_full_log()
                if self.mqtt_client:
                    self.mqtt_client.publish(topic, json.dumps(log_data))
                self.logger.info("Log sync completed")
        except Exception as e:
            self.logger.error(f"Error during log sync: {str(e)}")

    def subscribe_all_schema_topics(self) -> None:
        if not self.enable_mqtt or not self.mqtt_client:
            raise RuntimeError("MQTT client is not enabled or available")
            
        topics = []
        
        for topic_list in self.schema.input_base_topic.values():
            topics.extend(topic_list)
            
        for topic_list in self.schema.input_topic.values():
            topics.extend(topic_list)
            
        self.mqtt_client.subscribe_topics(topics)

    def publish_to_topics(self, topic_key: str, message: str) -> None:
        if not self.enable_mqtt or not self.mqtt_client:
            raise RuntimeError("MQTT client is not enabled or available")
            
        topics = []
        
        if topic_key in self.schema.output_topic:
            topics.extend(self.schema.output_topic[topic_key])
        elif topic_key in self.schema.output_base_topic:
            topics.extend(self.schema.output_base_topic[topic_key])
            
        for topic in topics:
            self.mqtt_client.publish(topic, message)
    
    def _base_mqtt_output_handler(self) -> None:
        current_time = time.time()
        
        if BaseOutputTopicType.STATE_PEPEUNIT.value in self.schema.output_base_topic:
            if current_time - self._last_state_send >= self.settings.STATE_SEND_INTERVAL:
                topic = self.schema.output_base_topic[BaseOutputTopicType.STATE_PEPEUNIT.value][0]
                state_data = self.get_system_state()
                if self.mqtt_client:
                    self.mqtt_client.publish(topic, json.dumps(state_data))

                    self._last_state_send = current_time
    
    def run_main_cycle(self, output_handler: Optional[Callable] = None) -> None:
        self._running = True
        if output_handler:
            self._mqtt_output_handler = output_handler
        
        try:
            while self._running:
                self._base_mqtt_output_handler()
                
                if self._mqtt_output_handler:
                    self._mqtt_output_handler(self)
                
                time.sleep(self.cycle_speed)
                
        except Exception as e:
            self.logger.error(f"Error in main cycle: {str(e)}")
        finally:
            self._running = False
    
    def set_output_handler(self, output_handler: Callable) -> None:
        self._mqtt_output_handler = output_handler

    def stop_main_cycle(self) -> None:
        self._running = False
    
    
