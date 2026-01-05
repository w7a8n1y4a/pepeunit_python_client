import json
import os
import tempfile
import time
import sys
import subprocess
from typing import Optional, Dict, Any, Callable

# Import for mocking in tests
try:
    import psutil
except ImportError:
    psutil = None

from .settings import Settings
from .file_manager import FileManager
from .logger import Logger
from .schema_manager import SchemaManager
from .abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient
from .pepeunit_mqtt_client import PepeunitMqttClient
from .pepeunit_rest_client import PepeunitRestClient
from .enums import BaseInputTopicType, BaseOutputTopicType, RestartMode


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
        cycle_speed: float = 0.1,
        restart_mode: RestartMode = RestartMode.RESTART_EXEC,
        ff_version_check_enable=True
    ):
        self.env_file_path = env_file_path
        self.schema_file_path = schema_file_path
        self.log_file_path = log_file_path
        self.enable_mqtt = enable_mqtt
        self.enable_rest = enable_rest
        self.cycle_speed = cycle_speed
        self.restart_mode = restart_mode
        self.ff_version_check_enable = ff_version_check_enable
        
        self.settings = Settings(env_file_path)
        self.schema = SchemaManager(schema_file_path)
        self.logger = Logger(log_file_path, None, self.schema, self.settings)

        self.mqtt_client = (mqtt_client if mqtt_client else self._get_default_mqtt_client()) if enable_mqtt else None
        self.rest_client = (rest_client if rest_client else self._get_default_rest_client()) if enable_rest else None
        
        if self.mqtt_client:
            self.logger.mqtt_client = self.mqtt_client
        
        self.mqtt_input_handler: Optional[Callable] = None
        self.mqtt_output_handler: Optional[Callable] = None
        self.custom_update_handler: Optional[Callable] = None

        self._running = False
        self._last_state_send = 0
        
    def _get_default_mqtt_client(self) -> Optional[AbstractPepeunitMqttClient]:
        return PepeunitMqttClient(self.settings, self.schema, self.logger)
    
    def _get_default_rest_client(self) -> Optional[AbstractPepeunitRestClient]:
        return PepeunitRestClient(self.settings)
    
    def get_system_state(self) -> Dict[str, Any]:
        if psutil is not None:
            try:
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
                    'pu_commit_version': self.settings.PU_COMMIT_VERSION,
                }
            except Exception:
                pass
        
        return {
            'millis': round(time.time() * 1000),
            'mem_free': 0,
            'mem_alloc': 0,
            'freq': 0,
            'pu_commit_version': self.settings.PU_COMMIT_VERSION,
        }
    
    def set_mqtt_input_handler(self, handler: Callable) -> None:

        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")

        self.mqtt_input_handler = handler

        def combined_handler(msg):
            self._base_mqtt_input_func(msg)
            if self.mqtt_input_handler:
                self.mqtt_input_handler(self, msg)

        self.mqtt_client.set_input_handler(combined_handler)

    def _base_mqtt_input_func(self, msg) -> None:
        try:
            for topic_key in self.schema.input_base_topic:
                if msg.topic in self.schema.input_base_topic[topic_key]:
                    self.logger.info(f'Get base MQTT command: {topic_key}')

                    if topic_key == BaseInputTopicType.ENV_UPDATE_PEPEUNIT.value:
                        self.download_env(self.env_file_path)
                    elif topic_key == BaseInputTopicType.SCHEMA_UPDATE_PEPEUNIT.value:
                        self.download_schema(self.schema_file_path)
                    elif topic_key == BaseInputTopicType.UPDATE_PEPEUNIT.value:
                        self._handle_update(msg)
                    elif topic_key == BaseInputTopicType.LOG_SYNC_PEPEUNIT.value:
                        self._handle_log_sync()
                    break
        except Exception as e:
            self.logger.error(f"Error in base MQTT input handler: {str(e)}")
    
    def download_env(self, file_path: str) -> None:
        if not self.rest_client:
            raise RuntimeError("REST client is not available")

        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")

        self.rest_client.download_env(file_path)
        self.settings.load_from_file()
        self.logger.info('Success update env')
    
    def download_schema(self, file_path: str) -> None:
        if not self.rest_client:
            raise RuntimeError("REST client is not available")

        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")

        self.rest_client.download_schema(file_path)
        self.schema.update_from_file()
        self.subscribe_all_schema_topics()
        self.logger.info('Success update schema')

    def set_state_storage(self, state: str) -> None:
        if not self.rest_client:
            raise RuntimeError("REST client is not available")
        
        self.rest_client.set_state_storage(state)
    
    def get_state_storage(self) -> str:
        if not self.rest_client:
            raise RuntimeError("REST client is not available")
        
        return self.rest_client.get_state_storage()

    def _handle_update(self, msg) -> None:

        payload = json.loads(msg.payload) if msg.payload else {}

        if not self.rest_client:
            raise RuntimeError("REST client is not available")

        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")

        if self.ff_version_check_enable and self.settings.PU_COMMIT_VERSION == payload.get('PU_COMMIT_VERSION'):
            self.logger.info('No update needed: current version = target version')
            return
            
        if self.custom_update_handler:
            self.custom_update_handler(self, payload)
        else:
            temp_dir = tempfile.gettempdir()
            archive_path = os.path.join(temp_dir, f"update_{self.settings.unit_uuid}.tar.gz")
            
            self.rest_client.download_update(archive_path)
            self.logger.info('Success download update archive', file_only=True)

            self.update_device_program(archive_path)
            self.logger.info('Success extract archive', file_only=True)
            
            self.logger.info("Full update cycle completed successfully")
    
    def update_device_program(self, archive_path: str) -> None:
        
        unit_directory = os.path.dirname(self.env_file_path) or os.getcwd()
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            FileManager.extract_tar_gz(archive_path, temp_extract_dir)
            self.logger.info(f"Extracted archive to {temp_extract_dir}")
            
            FileManager.copy_directory_contents(temp_extract_dir, unit_directory)
            self.logger.info(f"Copied directory contents from {temp_extract_dir} to {unit_directory}")
        
        os.remove(archive_path)
        self.logger.info(f"Archive removed {archive_path}")
        
        if self.restart_mode == RestartMode.RESTART_POPEN:
            self.stop_main_cycle()
            
            self.logger.info('Run new main cycle in other process')
            subprocess.Popen([sys.executable] + sys.argv)

            self.logger.info('I`ll Be Back - stop this process')
            sys.exit(0)
        elif self.restart_mode == RestartMode.RESTART_EXEC:
            self.stop_main_cycle()
            
            self.logger.info('I`ll Be Back - replacing current process')
            os.execv(sys.executable, [sys.executable] + sys.argv)
        elif self.restart_mode == RestartMode.ENV_SCHEMA_ONLY:
            self.logger.info('Updating env and schema only, without restart')
            self._update_env_schema_only()
        elif self.restart_mode == RestartMode.NO_RESTART:
            self.logger.info('Archive extracted, no restart or updates performed')
    
    def _update_env_schema_only(self) -> None:
        self.settings.load_from_file()
        self.schema.update_from_file()
        
        if self.enable_mqtt and self.mqtt_client:
            self.subscribe_all_schema_topics()
        
        self.logger.info('Environment and schema updated successfully')

    def _handle_log_sync(self) -> None:
        topic = self.schema.output_base_topic[BaseOutputTopicType.LOG_PEPEUNIT.value][0]
        log_data = self.logger.get_full_log()
        if self.mqtt_client:
            self.mqtt_client.publish(topic, json.dumps(log_data))
        self.logger.info("Log sync completed")

    def subscribe_all_schema_topics(self) -> None:
        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")
            
        topics = []
        
        for topic_list in self.schema.input_base_topic.values():
            topics.extend(topic_list)
            
        for topic_list in self.schema.input_topic.values():
            topics.extend(topic_list)

        self.logger.info(f'Need a subscription for {len(topic_list)} topics')
            
        self.mqtt_client.subscribe_topics(topics)

    def publish_to_topics(self, topic_key: str, message: str) -> None:
        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")
            
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
            if current_time - self._last_state_send >= self.settings.PU_STATE_SEND_INTERVAL:
                topic = self.schema.output_base_topic[BaseOutputTopicType.STATE_PEPEUNIT.value][0]
                state_data = self.get_system_state()
                if self.mqtt_client:
                    self.mqtt_client.publish(topic, json.dumps(state_data))

                    self._last_state_send = current_time
    
    def run_main_cycle(self) -> None:
        self._running = True
        try:
            while self._running:
                self._base_mqtt_output_handler()
                
                if self.mqtt_output_handler:
                    self.mqtt_output_handler(self)
                
                time.sleep(self.cycle_speed)
                
        except Exception as e:
            self.logger.error(f"Error in main cycle: {str(e)}")
        finally:
            self._running = False
    
    def set_output_handler(self, output_handler: Callable) -> None:
        self.mqtt_output_handler = output_handler

    def set_custom_update_handler(self, custom_update_handler: Callable) -> None:
        self.custom_update_handler = custom_update_handler

    def stop_main_cycle(self) -> None:
        self.logger.info(f'Main cycle stopped')
        self._running = False
