import base64
import datetime
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .settings import Settings
from .schema import Schema
from .file_manager import PepeunitFileManager
from .interfaces import MQTTClientInterface, RESTClientInterface
from .mqtt_client import MQTTClient, DummyMQTTClient
from .rest_client import RESTClient, DummyRESTClient
from .exceptions import PepeunitClientError
from .enums import LogLevel


class PepeunitClient:
    
    def __init__(
        self,
        env_path: str,
        schema_path: str,
        log_path: str,
        mqtt_enabled: bool = False,
        rest_enabled: bool = False,
        mqtt_client: Optional[MQTTClientInterface] = None,
        rest_client: Optional[RESTClientInterface] = None,
        message_handler: Optional[Callable] = None
    ):
        self.mqtt_enabled = mqtt_enabled
        self.rest_enabled = rest_enabled
        
        logging.basicConfig(level=logging.CRITICAL)
        self.logger = logging.getLogger(__name__)
        
        self.file_manager = PepeunitFileManager(env_path, schema_path, log_path)
        
        self._load_settings()
        self._load_schema()
        
        self.mqtt_client = mqtt_client or self._create_mqtt_client()
        self.rest_client = rest_client or self._create_rest_client()
        
        self.message_handler = message_handler
        if self.message_handler and self.mqtt_client:
            self.mqtt_client.set_message_handler(self._internal_message_handler)
        
        self._state_timer: Optional[threading.Timer] = None
        self._is_running = False
    
    def _load_settings(self) -> None:
        try:
            env_data = self.file_manager.get_env_values()
            self.settings = Settings(**env_data)
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error loading settings: {e}")
            self.settings = Settings()
    
    def _load_schema(self) -> None:
        try:
            schema_data = self.file_manager.get_schema_values()
            self.schema = Schema(schema_data)
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error loading schema: {e}")
            self.schema = Schema({})
    
    def _create_mqtt_client(self) -> MQTTClientInterface:
        if not self.mqtt_enabled:
            return DummyMQTTClient()
        
        try:
            return MQTTClient(
                host=self.settings.MQTT_URL,
                port=self.settings.MQTT_PORT,
                username=self.settings.PEPEUNIT_TOKEN,
                password=""
            )
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error creating MQTT client: {e}")
            return DummyMQTTClient()
    
    def _create_rest_client(self) -> RESTClientInterface:
        if not self.rest_enabled:
            return DummyRESTClient()
        
        try:
            return RESTClient(timeout=30)
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error creating REST client: {e}")
            return DummyRESTClient()
    
    @property
    def unit_uuid(self) -> str:
        try:
            if not self.settings.PEPEUNIT_TOKEN:
                return ""
            
            
            parts = self.settings.PEPEUNIT_TOKEN.split('.')
            if len(parts) != 3:
                return ""
            
            payload = parts[1]
            
            payload += '=' * (4 - len(payload) % 4)
            
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            
            return payload_data.get('uuid', '')
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error extracting unit_uuid from token: {e}")
            return ""
    
    def refresh_settings(self) -> None:
        
        try:
            self._load_settings()
            if self.mqtt_enabled:
                self.mqtt_client = self._create_mqtt_client()
                if self.message_handler:
                    self.mqtt_client.set_message_handler(self._internal_message_handler)
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error refreshing settings: {e}")
    
    def get_subscription_topics(self) -> List[str]:
        
        return self.schema.get_input_topics()
    
    def update_device_program(self, archive_path: str) -> None:
        
        try:
            self.file_manager.update_device_program(archive_path)
            self.refresh_settings()
            self.log(LogLevel.INFO, f"Device program updated from {archive_path}")
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error updating device program: {e}")
            raise
    
    def get_system_state(self) -> Dict[str, Any]:
        
        try:
            state = {
                'millis': round(time.time() * 1000),
                'commit_version': self.settings.COMMIT_VERSION,
            }
            
            if PSUTIL_AVAILABLE:
                memory_info = psutil.virtual_memory()
                cpu_freq = psutil.cpu_freq()
                
                state.update({
                    'mem_free': memory_info.available,
                    'mem_alloc': memory_info.total - memory_info.available,
                    'freq': cpu_freq.current if cpu_freq else 0,
                })
            else:
                state.update({
                    'mem_free': 0,
                    'mem_alloc': 0,
                    'freq': 0,
                })
            
            return state
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error getting system state: {e}")
            return {
                'millis': round(time.time() * 1000),
                'commit_version': self.settings.COMMIT_VERSION,
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
            }
    
    def log(self, level: LogLevel, message: str) -> None:
        
        try:
            log_entry = {
                'level': level.value,
                'text': message,
                'create_datetime': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            
            self.file_manager.append_log_entry(log_entry)
            
            if (self.mqtt_enabled and 
                hasattr(self.mqtt_client, 'is_connected') and 
                self.mqtt_client.is_connected):
                
                log_topic = self.schema.get_topic_by_key('log/pepeunit')
                if log_topic:
                    try:
                        self.mqtt_client.publish(log_topic, json.dumps(log_entry))
                    except Exception:
                        pass  # Не логируем ошибки отправки лога
                        
        except Exception as e:
            self.logger.critical(f"Critical logging error: {e}")
    
    def get_full_log(self) -> List[Dict[str, Any]]:
        
        return self.file_manager.get_full_log()
    
    
    def update_env_file(self, new_env_path: str) -> None:
        
        try:
            self.file_manager.update_env_file(new_env_path)
            self.refresh_settings()
            self.log(LogLevel.INFO, f"Environment file updated from {new_env_path}")
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error updating env file: {e}")
            raise
    
    def get_env_values(self) -> Dict[str, Any]:
        
        return self.file_manager.get_env_values()
    
    def update_schema_file(self, new_schema_path: str) -> None:
        
        try:
            self.file_manager.update_schema_file(new_schema_path)
            self._load_schema()
            self.log(LogLevel.INFO, f"Schema file updated from {new_schema_path}")
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error updating schema file: {e}")
            raise
    
    def get_schema_values(self) -> Dict[str, Any]:
        
        return self.file_manager.get_schema_values()
    
    def update_log_file(self, new_log_path: str) -> None:
        
        try:
            self.file_manager.update_log_file(new_log_path)
            self.log(LogLevel.INFO, f"Log file updated from {new_log_path}")
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error updating log file: {e}")
            raise
    
    
    def connect_mqtt(self) -> None:
        
        if not self.mqtt_enabled:
            raise PepeunitClientError("MQTT is not enabled")
        
        try:
            self.mqtt_client.connect()
            self.mqtt_client.start_loop()
            
            topics = self.get_subscription_topics()
            if topics:
                self.mqtt_client.subscribe(topics)
            
            self.log(LogLevel.INFO, "Connected to MQTT broker")
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error connecting to MQTT: {e}")
            raise
    
    def disconnect_mqtt(self) -> None:
        
        if self.mqtt_client:
            try:
                self.mqtt_client.stop_loop()
                self.mqtt_client.disconnect()
                self.log(LogLevel.INFO, "Disconnected from MQTT broker")
            except Exception as e:
                self.log(LogLevel.ERROR, f"Error disconnecting from MQTT: {e}")
    
    def publish_to_topic(self, topic_key: str, message: str) -> None:
        
        if not self.mqtt_enabled:
            raise PepeunitClientError("MQTT is not enabled")
        
        try:
            topics = self.schema.output_topic.get(topic_key, [])
            if not topics:
                raise PepeunitClientError(f"Topic key '{topic_key}' not found in output_topic")
            
            for topic in topics:
                success = self.mqtt_client.publish(topic, message)
                if not success:
                    self.log(LogLevel.ERROR, f"Failed to publish to topic {topic}")
                    
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error publishing to topic {topic_key}: {e}")
            raise
    
    def subscribe_to_topics(self, topic_key: str) -> None:
        
        if not self.mqtt_enabled:
            raise PepeunitClientError("MQTT is not enabled")
        
        try:
            topics = self.schema.input_topic.get(topic_key, [])
            if not topics:
                raise PepeunitClientError(f"Topic key '{topic_key}' not found in input_topic")
            
            self.mqtt_client.subscribe(topics)
            self.log(LogLevel.INFO, f"Subscribed to topics for key '{topic_key}'")
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error subscribing to topics {topic_key}: {e}")
            raise
    
    def start_state_publishing(self) -> None:
        
        if not self.mqtt_enabled:
            return
        
        state_topic = self.schema.get_topic_by_key('state/pepeunit')
        if state_topic and self.settings.STATE_SEND_INTERVAL > 0:
            self._schedule_state_publishing()
    
    def _schedule_state_publishing(self) -> None:
        
        if not self._is_running:
            return
            
        try:
            state = self.get_system_state()
            state_topic = self.schema.get_topic_by_key('state/pepeunit')
            
            if state_topic:
                self.mqtt_client.publish(state_topic, json.dumps(state))
            
            self._state_timer = threading.Timer(
                self.settings.STATE_SEND_INTERVAL,
                self._schedule_state_publishing
            )
            self._state_timer.start()
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error in state publishing: {e}")
    
    
    def download_update(self) -> str:
        
        if not self.rest_enabled:
            raise PepeunitClientError("REST is not enabled")
        
        try:
            url = self._build_api_url(f"/units/firmware/tgz/{self.unit_uuid}")
            headers = self._get_auth_headers()
            
            temp_path = f"/tmp/update_{self.unit_uuid}.tar.gz"
            self.rest_client.download_file(url, temp_path, headers)
            
            self.log(LogLevel.INFO, f"Update downloaded to {temp_path}")
            return temp_path
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error downloading update: {e}")
            raise
    
    def download_env(self) -> str:
        
        if not self.rest_enabled:
            raise PepeunitClientError("REST is not enabled")
        
        try:
            url = self._build_api_url(f"/units/env/{self.unit_uuid}")
            headers = self._get_auth_headers()
            
            response = self.rest_client.get(url, headers)
            
            temp_path = f"/tmp/env_{self.unit_uuid}.json"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=4, ensure_ascii=False)
            
            self.log(LogLevel.INFO, f"Environment downloaded to {temp_path}")
            return temp_path
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error downloading env: {e}")
            raise
    
    def download_schema(self) -> str:
        
        if not self.rest_enabled:
            raise PepeunitClientError("REST is not enabled")
        
        try:
            url = self._build_api_url(f"/units/get_current_schema/{self.unit_uuid}")
            headers = self._get_auth_headers()
            
            response = self.rest_client.get(url, headers)
            
            temp_path = f"/tmp/schema_{self.unit_uuid}.json"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=4, ensure_ascii=False)
            
            self.log(LogLevel.INFO, f"Schema downloaded to {temp_path}")
            return temp_path
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error downloading schema: {e}")
            raise
    
    def set_state_storage(self, uuid: str, state: Dict[str, Any]) -> None:
        
        if not self.rest_enabled:
            raise PepeunitClientError("REST is not enabled")
        
        try:
            url = self._build_api_url(f"/unit/{uuid}")
            headers = self._get_auth_headers()
            
            self.rest_client.put(url, state, headers)
            self.log(LogLevel.INFO, f"State uploaded to storage for unit {uuid}")
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error setting state storage: {e}")
            raise
    
    def get_state_storage(self, uuid: str) -> Dict[str, Any]:
        
        if not self.rest_enabled:
            raise PepeunitClientError("REST is not enabled")
        
        try:
            url = self._build_api_url(f"/unit/{uuid}")
            headers = self._get_auth_headers()
            
            response = self.rest_client.get(url, headers)
            self.log(LogLevel.INFO, f"State retrieved from storage for unit {uuid}")
            return response
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error getting state storage: {e}")
            raise
    
    
    def perform_update(self) -> None:
        
        if not (self.mqtt_enabled and self.rest_enabled):
            raise PepeunitClientError("Both MQTT and REST must be enabled for perform_update")
        
        try:
            archive_path = self.download_update()
            
            self.update_device_program(archive_path)
            
            os.remove(archive_path)
            
            self.log(LogLevel.INFO, "Update completed successfully")
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error performing update: {e}")
            raise
    
    
    def _build_api_url(self, endpoint: str) -> str:
        
        return (f"{self.settings.HTTP_TYPE}://{self.settings.PEPEUNIT_URL}"
                f"{self.settings.PEPEUNIT_APP_PREFIX}"
                f"{self.settings.PEPEUNIT_API_ACTUAL_PREFIX}{endpoint}")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        
        return {
            'accept': 'application/json',
            'x-auth-token': self.settings.PEPEUNIT_TOKEN,
        }
    
    def _internal_message_handler(self, client, userdata, msg) -> None:
        
        try:
            self._handle_system_messages(client, userdata, msg)
            
            if self.message_handler:
                self.message_handler(client, userdata, msg)
                
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error in message handler: {e}")
    
    def _handle_system_messages(self, client, userdata, msg) -> None:
        
        try:
            topic_parts = msg.topic.split('/')
            
            if len(topic_parts) >= 3:
                result = self.schema.search_topic_in_schema(self.unit_uuid)
                if result:
                    topic_type, topic_name = result
                    
                    if topic_type == 'input_base_topic':
                        self._handle_base_topic_message(topic_name, msg)
                        
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error handling system message: {e}")
    
    def _handle_base_topic_message(self, topic_name: str, msg) -> None:
        
        try:
            if topic_name == 'update/pepeunit' and self.rest_enabled:
                self.perform_update()
                
            elif topic_name == 'env_update/pepeunit' and self.rest_enabled:
                env_path = self.download_env()
                self.update_env_file(env_path)
                os.remove(env_path)
                
            elif topic_name == 'schema_update/pepeunit' and self.rest_enabled:
                schema_path = self.download_schema()
                self.update_schema_file(schema_path)
                os.remove(schema_path)
                
            elif topic_name == 'log_sync/pepeunit':
                log_topic = self.schema.get_topic_by_key('log/pepeunit')
                if log_topic:
                    full_log = self.get_full_log()
                    self.mqtt_client.publish(log_topic, json.dumps(full_log, indent=4))
                    
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error handling base topic message {topic_name}: {e}")
    
    
    def start(self) -> None:
        
        try:
            self._is_running = True
            
            if self.mqtt_enabled:
                self.connect_mqtt()
                self.start_state_publishing()
            
            self.log(LogLevel.INFO, "PepeunitClient started")
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error starting client: {e}")
            raise
    
    def stop(self) -> None:
        
        try:
            self._is_running = False
            
            if self._state_timer:
                self._state_timer.cancel()
            
            if self.mqtt_enabled:
                self.disconnect_mqtt()
            
            self.log(LogLevel.INFO, "PepeunitClient stopped")
            
        except Exception as e:
            self.log(LogLevel.ERROR, f"Error stopping client: {e}")
    
    def __enter__(self):
        
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        
        self.stop()