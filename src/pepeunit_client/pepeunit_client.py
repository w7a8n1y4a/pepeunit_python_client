
import base64
import json
import logging
import sys
import time
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path

from .enums import LogLevel
from .exceptions import PepeunitClientError
from .settings import Settings
from .file_manager import FileManager
from .interfaces import MQTTClientInterface, RESTClientInterface
from .schema import Schema
from .mqtt_client import MQTTClient
from .rest_client import RESTClient


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик критических исключений"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


# Устанавливаем глобальный обработчик исключений
sys.excepthook = _global_exception_handler


class PepeunitClient:
    
    def __init__(
        self,
        env_path: str,
        schema_path: str,
        log_path: str,
        use_mqtt: bool = False,
        use_rest: bool = False,
        message_handler: Optional[Callable[[str, str], None]] = None,
        mqtt_client: Optional[MQTTClientInterface] = None,
        rest_client: Optional[RESTClientInterface] = None,
    ) -> None:
        self.env_path = Path(env_path)
        self.schema_path = Path(schema_path)
        self.log_path = Path(log_path)
        self.message_handler = message_handler

        self._env_data = FileManager.load_json_file(self.env_path)
        self._schema_data = FileManager.load_json_file(self.schema_path)
        self._log_data = FileManager.load_json_file(self.log_path)

        self.settings = Settings(**self._env_data) if isinstance(self._env_data, dict) else Settings()
        self.schema = Schema(self._schema_data)
        
        # Инициализация клиентов
        if mqtt_client:
            self.mqtt_client = mqtt_client
        elif use_mqtt:
            self.mqtt_client = MQTTClient(self.settings)
        else:
            self.mqtt_client = None
            
        if rest_client:
            self.rest_client = rest_client
        elif use_rest:
            self.rest_client = RESTClient(self.settings)
        else:
            self.rest_client = None
        
        # Настройка MQTT клиента
        if self.mqtt_client:
            if self.message_handler:
                # Создаем композитный обработчик: сначала наш, потом пользовательский
                composite_handler = self._create_composite_message_handler(self.message_handler)
                self.mqtt_client.set_message_handler(composite_handler)
            else:
                # Используем только встроенный обработчик
                self.mqtt_client.set_message_handler(self._handle_mqtt_message)
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Настройка автоматической отправки состояния
        self._setup_state_timer()
    
    def _create_composite_message_handler(self, user_handler: Callable[[str, str], None]) -> Callable[[str, str], None]:
        """Создает композитный обработчик сообщений"""
        def composite_handler(topic: str, payload: str) -> None:
            # Сначала обрабатываем встроенными обработчиками
            self._handle_mqtt_message(topic, payload)
            
            # Затем вызываем пользовательский обработчик
            try:
                user_handler(topic, payload)
            except Exception as e:
                self._log(LogLevel.ERROR, f"User message handler error: {e}")
        
        return composite_handler
    
    def set_message_handler(self, handler: Callable[[str, str], None]) -> None:
        """Установка пользовательского обработчика сообщений"""
        self.message_handler = handler
        if self.mqtt_client:
            if handler:
                composite_handler = self._create_composite_message_handler(handler)
                self.mqtt_client.set_message_handler(composite_handler)
            else:
                self.mqtt_client.set_message_handler(self._handle_mqtt_message)
    
    def connect_mqtt(self) -> bool:
        """Подключение MQTT клиента"""
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT client not configured")
            return False
        
        try:
            success = self.mqtt_client.connect()
            if success:
                self._log(LogLevel.INFO, "MQTT client connected")
                # Автоматическая подписка на input топики
                input_topics = self.schema.get_input_topics()
                if input_topics:
                    self.mqtt_client.subscribe(input_topics)
                    self._log(LogLevel.INFO, f"Subscribed to {len(input_topics)} input topics")
            else:
                error = self.mqtt_client.get_connection_error()
                self._log(LogLevel.ERROR, f"MQTT connection failed: {error}")
            return success
        except Exception as e:
            self._log(LogLevel.ERROR, f"MQTT connection error: {e}")
            return False
    
    def disconnect_mqtt(self) -> None:
        """Отключение MQTT клиента"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            self._log(LogLevel.INFO, "MQTT client disconnected")
    
    @property
    def unit_uuid(self) -> Optional[str]:
        """Получение unit_uuid из JWT токена"""
        try:
            token = self.settings.PEPEUNIT_TOKEN
            if not token:
                return None
            
            # JWT состоит из 3 частей, разделенных точками
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Декодируем центральную часть (payload)
            payload = parts[1]
            # Добавляем padding если нужно
            missing_padding = len(payload) % 4
            if missing_padding:
                payload += '=' * (4 - missing_padding)
            
            decoded_bytes = base64.b64decode(payload)
            payload_dict = json.loads(decoded_bytes.decode('utf-8'))
            
            return payload_dict.get('uuid')
        except Exception as e:
            self.logger.error(f"Error decoding unit_uuid from JWT: {e}")
            return None
    
    def _setup_state_timer(self) -> None:
        """Настройка автоматической отправки состояния по таймеру"""
        if not self.mqtt_client:
            return
        
        # Проверяем, есть ли топик для отправки состояния
        state_topic = self.schema.get_topic_by_key('state/pepeunit')
        if not state_topic:
            return
        
        # Запускаем таймер в отдельном потоке
        import threading
        
        def state_sender():
            while True:
                try:
                    state = self.generate_device_state()
                    state_topics = self.schema.output_base_topic.get('state/pepeunit', [])
                    if state_topics:
                        self.mqtt_client.publish(state_topics, json.dumps(state))
                        self._log(LogLevel.DEBUG, "Device state sent")
                except Exception as e:
                    self._log(LogLevel.ERROR, f"State sending error: {e}")
                
                time.sleep(self.settings.STATE_SEND_INTERVAL)
        
        state_thread = threading.Thread(target=state_sender, daemon=True)
        state_thread.start()
    
    def _log(self, level: LogLevel, message: str) -> None:
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        }
        
        if isinstance(self._log_data, list):
            self._log_data.append(log_entry)
        else:
            self._log_data = [log_entry]
        
        FileManager.save_json_file(self.log_path, self._log_data)
        
        if self.mqtt_client and level.get_int_level() >= LogLevel.INFO.get_int_level():
            try:
                topics = self.schema.output_base_topic.get('log/pepeunit', [])
                if topics:
                    self.mqtt_client.publish(topics, json.dumps(log_entry))
            except Exception as e:
                self.logger.error(f"MQTT log send error: {e}")
    
    def update_device_program(self, archive_path: str) -> bool:
        """Обновление программы устройства по пути до архива"""
        try:
            import tarfile
            import shutil
            from pathlib import Path
            
            archive_file = Path(archive_path)
            if not archive_file.exists():
                self._log(LogLevel.ERROR, f"Archive file not found: {archive_path}")
                return False
            
            # Создаем временную директорию для распаковки
            temp_dir = Path.cwd() / "temp_update"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
            # Распаковываем архив
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Копируем файлы в основную директорию
            for item in temp_dir.iterdir():
                dest_path = Path.cwd() / item.name
                if item.is_dir():
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(item, dest_path)
                else:
                    shutil.copy2(item, dest_path)
            
            # Удаляем временную директорию
            shutil.rmtree(temp_dir)
            
            self._log(LogLevel.INFO, f"Device program updated from {archive_path}")
            return True
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"Device program update error: {e}")
            return False
    
    
    def update_env_from_file(self, file_path: str) -> None:
        try:
            new_env_data = FileManager.load_json_file(Path(file_path))
            self._env_data = new_env_data
            self.settings = Settings(**new_env_data) if isinstance(new_env_data, dict) else Settings()
            FileManager.save_json_file(self.env_path, self._env_data)
            self._log(LogLevel.INFO, f"env.json updated from file {file_path}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"env.json update error: {e}")
    
    def update_env(self, env_dict: Dict[str, Any]) -> None:
        try:
            self._env_data.update(env_dict)
            self.settings.update(**env_dict)
            FileManager.save_json_file(self.env_path, self._env_data)
            self._log(LogLevel.INFO, "env.json updated")
        except Exception as e:
            self._log(LogLevel.ERROR, f"env.json update error: {e}")
    
    def get_env_data(self) -> Dict[str, Any]:
        return self._env_data
    
    def update_schema_from_file(self, file_path: str) -> None:
        try:
            new_schema_data = FileManager.load_json_file(Path(file_path))
            self._schema_data = new_schema_data
            self.schema.update(new_schema_data)
            FileManager.save_json_file(self.schema_path, self._schema_data)
            self._log(LogLevel.INFO, f"schema.json updated from file {file_path}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"schema.json update error: {e}")
    
    def update_schema(self, schema_dict: Dict[str, Any]) -> None:
        try:
            self._schema_data.update(schema_dict)
            self.schema.update(self._schema_data)
            FileManager.save_json_file(self.schema_path, self._schema_data)
            self._log(LogLevel.INFO, "schema.json updated")
        except Exception as e:
            self._log(LogLevel.ERROR, f"schema.json update error: {e}")
    
    def get_schema_value(self, key: str, default: Any = None) -> Any:
        return self._schema_data.get(key, default)
    
    def get_schema_data(self) -> Dict[str, Any]:
        return self._schema_data.copy()
    
    # REST функционал
    def download_update(self) -> Optional[str]:
        """Скачивание архива обновления через REST"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST client not configured for download_update")
            return None
        
        try:
            if not self.unit_uuid:
                self._log(LogLevel.ERROR, "unit_uuid not available for download_update")
                return None
            
            archive_path = self.rest_client.download_update(self.unit_uuid)
            self._log(LogLevel.INFO, f"Update archive downloaded to {archive_path}")
            return archive_path
        except Exception as e:
            self._log(LogLevel.ERROR, f"Download update error: {e}")
            return None
    
    def download_env(self) -> bool:
        """Скачивание env.json через REST"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST client not configured for download_env")
            return False
        
        try:
            if not self.unit_uuid:
                self._log(LogLevel.ERROR, "unit_uuid not available for download_env")
                return False
            
            env_data = self.rest_client.download_env(self.unit_uuid)
            self.update_env(env_data)
            self._log(LogLevel.INFO, "env.json downloaded and updated")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Download env error: {e}")
            return False
    
    def download_schema(self) -> bool:
        """Скачивание schema.json через REST"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST client not configured for download_schema")
            return False
        
        try:
            if not self.unit_uuid:
                self._log(LogLevel.ERROR, "unit_uuid not available for download_schema")
                return False
            
            schema_data = self.rest_client.download_schema(self.unit_uuid)
            self.update_schema(schema_data)
            self._log(LogLevel.INFO, "schema.json downloaded and updated")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Download schema error: {e}")
            return False
    
    def set_state_storage(self, state: str) -> bool:
        """Загрузка состояния в Unit Storage"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST client not configured for set_state_storage")
            return False
        
        try:
            if not self.unit_uuid:
                self._log(LogLevel.ERROR, "unit_uuid not available for set_state_storage")
                return False
            
            self.rest_client.set_state_storage(self.unit_uuid, state)
            self._log(LogLevel.INFO, "State uploaded to Unit Storage")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Set state storage error: {e}")
            return False
    
    def get_state_storage(self) -> Optional[str]:
        """Получение состояния из Unit Storage"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST client not configured for get_state_storage")
            return None
        
        try:
            if not self.unit_uuid:
                self._log(LogLevel.ERROR, "unit_uuid not available for get_state_storage")
                return None
            
            state = self.rest_client.get_state_storage(self.unit_uuid)
            self._log(LogLevel.INFO, "State retrieved from Unit Storage")
            return state
        except Exception as e:
            self._log(LogLevel.ERROR, f"Get state storage error: {e}")
            return None
    
    def perform_update(self) -> bool:
        """Полный цикл обновления: MQTT получает команду → REST скачивает → базовый класс обновляется"""
        if not self.mqtt_client or not self.rest_client:
            self._log(LogLevel.WARNING, "Both MQTT and REST clients required for perform_update")
            return False
        
        try:
            # Скачиваем архив обновления
            archive_path = self.download_update()
            if not archive_path:
                self._log(LogLevel.ERROR, "Failed to download update archive")
                return False
            
            # Обновляем программу устройства
            success = self.update_device_program(archive_path)
            if success:
                self._log(LogLevel.INFO, "Full update cycle completed successfully")
            else:
                self._log(LogLevel.ERROR, "Failed to update device program")
            
            return success
        except Exception as e:
            self._log(LogLevel.ERROR, f"Perform update error: {e}")
            return False
    
    def _handle_mqtt_message(self, topic: str, payload: str) -> None:
        """Обработчик MQTT сообщений для специальных топиков"""
        try:
            # Парсим топик для определения типа сообщения
            topic_parts = topic.split('/')
            
            # Обрабатываем разные форматы топиков
            if len(topic_parts) >= 5:
                # Структурированный топик: domain/input_base_topic/unit_uuid/topic_name/...
                topic_type = topic_parts[1]
                topic_name = topic_parts[3]
                
                if topic_type == 'input_base_topic':
                    self._handle_special_topic(topic_name, payload)
            elif len(topic_parts) >= 3:
                # Простой топик: domain/topic_name/...
                topic_name = topic_parts[1]
                self._handle_special_topic(topic_name, payload)
            
        except Exception as e:
            self._log(LogLevel.ERROR, f"MQTT message handler error: {e}")
    
    def _handle_special_topic(self, topic_name: str, payload: str) -> None:
        """Обработка специальных топиков"""
        if topic_name == 'update' and self.rest_client:
            self._handle_update_message(payload)
        elif topic_name == 'env_update' and self.rest_client:
            self._handle_env_update_message()
        elif topic_name == 'schema_update' and self.rest_client:
            self._handle_schema_update_message()
        elif topic_name == 'log_sync':
            self._handle_log_sync_message()
    
    def _handle_update_message(self, payload: str) -> None:
        """Обработка сообщения обновления"""
        try:
            update_data = json.loads(payload)
            new_version = update_data.get('NEW_COMMIT_VERSION')
            
            if new_version and new_version != self.settings.COMMIT_VERSION:
                self._log(LogLevel.INFO, f"Update requested to version {new_version}")
                self.perform_update()
            else:
                self._log(LogLevel.INFO, "Update message received but no version change needed")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Update message handling error: {e}")
    
    def _handle_env_update_message(self) -> None:
        """Обработка сообщения обновления env.json"""
        try:
            self._log(LogLevel.INFO, "Environment update requested")
            self.download_env()
        except Exception as e:
            self._log(LogLevel.ERROR, f"Environment update handling error: {e}")
    
    def _handle_schema_update_message(self) -> None:
        """Обработка сообщения обновления schema.json"""
        try:
            self._log(LogLevel.INFO, "Schema update requested")
            if self.download_schema():
                # Переподписываемся на новые топики
                if self.mqtt_client:
                    input_topics = self.schema.get_input_topics()
                    self.mqtt_client.subscribe(input_topics)
        except Exception as e:
            self._log(LogLevel.ERROR, f"Schema update handling error: {e}")
    
    def _handle_log_sync_message(self) -> None:
        """Обработка сообщения синхронизации логов"""
        try:
            self._log(LogLevel.INFO, "Log sync requested")
            if self.mqtt_client:
                topics = self.schema.output_base_topic.get('log/pepeunit', [])
                if topics:
                    logs = self.get_all_logs()
                    self.mqtt_client.publish(topics, json.dumps(logs))
        except Exception as e:
            self._log(LogLevel.ERROR, f"Log sync handling error: {e}")
    
    def get_input_topics(self) -> List[str]:
        """Получение всех input топиков для подписки"""
        return self.schema.get_input_topics()
    
    def get_topic_by_key(self, key: str) -> Optional[str]:
        """Получение топика по ключу"""
        return self.schema.get_topic_by_key(key)
    
    def search_topic_in_schema(self, node_uuid: str) -> Optional[tuple[str, str]]:
        """Поиск топика по node_uuid в схеме"""
        return self.schema.search_topic_in_schema(node_uuid)
    
    
    
    
    def generate_device_state(self) -> Dict[str, Any]:
        try:
            import psutil  # type: ignore
            
            memory_info = psutil.virtual_memory()
            cpu_freq = psutil.cpu_freq()
            
            state = {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': cpu_freq.current if cpu_freq else 0,
                'commit_version': self.settings.COMMIT_VERSION or 'unknown',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
            
            return state
        except ImportError:
            return {
                'millis': round(time.time() * 1000),
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': self.settings.COMMIT_VERSION or 'unknown',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
        except Exception as e:
            self._log(LogLevel.ERROR, f"Device state generation error: {e}")
            return {
                'millis': round(time.time() * 1000),
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
    
    
    def save_log(self, level: LogLevel, message: str) -> None:
        self._log(level, message)
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        if isinstance(self._log_data, list):
            return self._log_data.copy()
        return []
    
    def clear_logs(self) -> None:
        self._log_data = []
        FileManager.save_json_file(self.log_path, self._log_data)
    
    
    def send_mqtt_message(self, topic_key: str, message: str) -> bool:
        """Отправка сообщения в топик по ключу"""
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT client not configured")
            return False
        
        try:
            # Получаем топики по ключу из схемы
            topics = []
            if topic_key in self.schema.output_topic:
                topics = self.schema.output_topic[topic_key]
            elif topic_key in self.schema.output_base_topic:
                topics = self.schema.output_base_topic[topic_key]
            
            if not topics:
                self._log(LogLevel.WARNING, f"Topic key {topic_key} not found in schema")
                return False
            
            # Отправляем на все топики в списке
            success = self.mqtt_client.publish(topics, message)
            
            if success:
                self._log(LogLevel.DEBUG, f"Message sent to {len(topics)} topics for key {topic_key}")
            else:
                self._log(LogLevel.ERROR, f"Failed to send message to topics for key {topic_key}")
            
            return success
        except Exception as e:
            self._log(LogLevel.ERROR, f"MQTT message send error: {e}")
            return False
    
    def subscribe_to_topics(self, topic_key: str) -> bool:
        """Подписка на топики по ключу"""
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT client not configured")
            return False
        
        try:
            # Получаем топики по ключу из схемы
            topics = []
            if topic_key in self.schema.input_topic:
                topics = self.schema.input_topic[topic_key]
            elif topic_key in self.schema.input_base_topic:
                topics = self.schema.input_base_topic[topic_key]
            
            if not topics:
                self._log(LogLevel.WARNING, f"Topic key {topic_key} not found in schema")
                return False
            
            # Подписываемся на все топики в списке
            success = self.mqtt_client.subscribe(topics)
            
            if success:
                self._log(LogLevel.INFO, f"Subscribed to {len(topics)} topics for key {topic_key}")
            else:
                self._log(LogLevel.ERROR, f"Failed to subscribe to topics for key {topic_key}")
            
            return success
        except Exception as e:
            self._log(LogLevel.ERROR, f"Topics subscription error: {e}")
            return False
    
    def send_log_via_mqtt(self, level: LogLevel, message: str, save_to_file: bool = True) -> bool:
        if not self.mqtt_client:
            if save_to_file:
                self.save_log(level, message)
            return False
        
        topics = self.schema.output_base_topic.get('log/pepeunit', [])
        if not topics:
            if save_to_file:
                self.save_log(LogLevel.WARNING, "Log topic not found in schema")
            return False
        
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        }
        
        if save_to_file:
            if isinstance(self._log_data, list):
                self._log_data.append(log_entry)
            else:
                self._log_data = [log_entry]
            FileManager.save_json_file(self.log_path, self._log_data)
        
        return self.mqtt_client.publish(topics, json.dumps(log_entry))
    
