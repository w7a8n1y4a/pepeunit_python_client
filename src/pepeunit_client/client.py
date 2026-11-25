import json
import os
import tempfile
import time
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Callable

# Import for mocking in tests
try:
    import psutil
except ImportError:
    psutil = None

from .settings import Settings
from .file_manager import FileManager
from .logger import Logger
from .io_topics import IOTopics
from .abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient
from .pepeunit_mqtt_client import PepeunitMqttClient
from .pepeunit_rest_client import PepeunitRestClient
from .enums import BaseInputTopicType, BaseOutputTopicType, RestartMode


class PepeunitClient:
    def __init__(
        self,
        env_file_path: str,
        log_file_path: str,
        enable_mqtt: bool = False,
        enable_rest: bool = False,
        mqtt_client: Optional[AbstractPepeunitMqttClient] = None,
        rest_client: Optional[AbstractPepeunitRestClient] = None,
        cycle_speed: float = 0.1,
        restart_mode: RestartMode = RestartMode.RESTART_EXEC,
        ff_version_check_enable=True,
        ff_console_log_enable=True
    ):
        self.env_file_path = env_file_path
        self.log_file_path = log_file_path
        self.enable_mqtt = enable_mqtt
        self.enable_rest = enable_rest or enable_mqtt
        self.cycle_speed = cycle_speed
        self.restart_mode = restart_mode
        self.ff_version_check_enable = ff_version_check_enable
        self.ff_console_log_enable = ff_console_log_enable
        
        self.settings = Settings(env_file_path)
        self.io_topics = IOTopics()
        self.logger = Logger(log_file_path, self.settings, self.ff_console_log_enable)
        self.mqtt_client = (mqtt_client or self._get_default_mqtt_client()) if enable_mqtt else None
        self.rest_client = (rest_client or self._get_default_rest_client()) if self.enable_rest else None

        self.mqtt_input_handler: Optional[Callable] = None
        self.mqtt_output_handler: Optional[Callable] = None
        self.custom_update_handler: Optional[Callable] = None

        self._running = False
        self._last_state_send = 0
        if self.mqtt_client is not None:
            self.mqtt_client.set_input_handler(self._dispatch_mqtt_input)
            self.logger.publish_log = lambda message: self.publish_to_topics(BaseOutputTopicType.LOG.value, message)
        
    def _get_default_mqtt_client(self) -> Optional[AbstractPepeunitMqttClient]:
        return PepeunitMqttClient(self.settings, self.logger)
    
    def _get_default_rest_client(self) -> Optional[AbstractPepeunitRestClient]:
        return PepeunitRestClient(self.settings)
    
    def get_system_state(self) -> Dict[str, Any]:
        if psutil is not None:
            try:
                memory_info = psutil.virtual_memory()
                
                try:
                    cpu_freq = psutil.cpu_freq()
                    freq = cpu_freq.current * 1_000_000 if cpu_freq else 0
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
    
    def connect(self) -> None:
        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")
        self.refresh_io_topics()
        self.mqtt_client.connect()

    def set_mqtt_input_handler(self, handler: Callable) -> None:
        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")
        self.mqtt_input_handler = handler

    def _dispatch_mqtt_input(self, msg) -> None:
        self._base_mqtt_input_func(msg)
        if self.mqtt_input_handler:
            self.mqtt_input_handler(self, msg)

    def _base_mqtt_input_func(self, msg) -> None:
        name = self.io_topics.input_name(msg.topic)
        try:
            if name == BaseInputTopicType.ENV_UPDATE.value:
                self.download_env(self.env_file_path)
            elif name == BaseInputTopicType.SCHEMA_UPDATE.value:
                self.refresh_io_topics()
            elif name == BaseInputTopicType.UPDATE.value:
                self._handle_update(msg)
            elif name == BaseInputTopicType.LOG_SYNC.value:
                self._handle_log_sync()
            elif name == BaseInputTopicType.RESET.value:
                self._handle_reset()
        except Exception as error:
            self.logger.error(f"Error in standard MQTT input handler: {error}")

    def download_env(self, file_path: str) -> None:
        if not self.rest_client:
            raise RuntimeError("REST client is not available")
        self.rest_client.download_env(file_path)
        if Path(file_path).resolve() == Path(self.env_file_path).resolve():
            self.settings.load_from_file()
        self.logger.info("Updated environment settings")

    def refresh_io_topics(self) -> None:
        if not self.rest_client:
            raise RuntimeError("REST client is not available")
        topics = self.rest_client.get_io_topics()
        if self.mqtt_client:
            self.mqtt_client.set_subscriptions({io.topic: io.qos for io in topics.input.values()})
        self.io_topics = topics

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

        if self.ff_version_check_enable and self.settings.PU_COMMIT_VERSION == payload.get('PU_COMMIT_VERSION'):
            self.logger.info('No update needed: current version = target version')
            return
            
        if self.custom_update_handler:
            self.custom_update_handler(self, payload)
            return

        if "COMPILED_FIRMWARE_LINK" in payload:
            raise RuntimeError(
                "Compiled firmware updates require set_custom_update_handler()"
            )

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as archive:
            archive_path = archive.name
        try:
            self.rest_client.download_update(archive_path)
            self.update_device_program(archive_path)
        finally:
            Path(archive_path).unlink(missing_ok=True)
        self.logger.info("Firmware update completed")
    
    def update_device_program(self, archive_path: str) -> None:
        
        unit_directory = os.path.dirname(self.env_file_path) or os.getcwd()
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            FileManager.extract_tar_gz(archive_path, temp_extract_dir)
            self.logger.info(f"Extracted archive to {temp_extract_dir}")
            
            archive_env = Path(temp_extract_dir) / ".env"
            env_name = Path(self.env_file_path).name
            FileManager.read_env(str(archive_env))
            if env_name != archive_env.name:
                archive_env.replace(archive_env.with_name(env_name))
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
        elif self.restart_mode == RestartMode.ENV_TOPICS_ONLY:
            self.logger.info('Reloading environment and IO topics')
            self._reload_after_update()
        elif self.restart_mode == RestartMode.NO_RESTART:
            self.logger.info('Archive extracted, no restart or updates performed')
    
    def _reload_after_update(self) -> None:
        self.settings.load_from_file()
        self.refresh_io_topics()
        self._last_state_send = 0

    def _handle_reset(self) -> None:
        self.logger.info('Reset command received, restarting program')
        self._restart_program()

    def _restart_program(self) -> None:
        if self.restart_mode == RestartMode.RESTART_POPEN:
            self.stop_main_cycle()

            self.logger.info('Run new main cycle in other process')
            subprocess.Popen([sys.executable] + sys.argv)

            self.logger.info('I`ll Be Back - stop this process')
            sys.exit(0)

        self.stop_main_cycle()

        self.logger.info('I`ll Be Back - replacing current process')
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _handle_log_sync(self) -> None:
        entries = self.logger.get_full_log()
        if entries:
            self.publish_to_topics(BaseOutputTopicType.LOG.value, json.dumps(entries))

    def publish_to_topics(self, topic_key: str, message: Any) -> Any:
        if not self.mqtt_client:
            raise RuntimeError("MQTT client is not available")
        output = self.io_topics.output.get(topic_key)
        if output is not None:
            return self.mqtt_client.publish(output.topic, message, qos=output.qos)
        return None

    def _base_mqtt_output_handler(self) -> None:
        current_time = time.time()
        name = BaseOutputTopicType.STATE.value
        if self.mqtt_client and name in self.io_topics.output:
            if current_time - self._last_state_send >= self.settings.PU_STATE_SEND_INTERVAL:
                self.publish_to_topics(name, json.dumps(self.get_system_state()))
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
