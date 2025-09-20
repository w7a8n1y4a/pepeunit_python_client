
import json
import os
import shutil
import time
import uuid
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = 'Debug'
    INFO = 'Info'
    WARNING = 'Warning'
    ERROR = 'Error'
    CRITICAL = 'Critical'

    def get_int_level(self) -> int:
        """Возвращает числовой уровень логирования"""
        level_mapping = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        return level_mapping[self]


class MQTTClientInterface(ABC):
    """Интерфейс для MQTT клиента"""
    
    @abstractmethod
    def publish(self, topic: str, payload: str) -> None:
        """Отправить сообщение в топик"""
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        """Подписаться на топики"""
        pass


class RESTClientInterface(ABC):
    """Интерфейс для REST клиента"""
    
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Выполнить GET запрос"""
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Выполнить POST запрос"""
        pass


class PepeunitClient:
    """
    Основной клиент для работы с Pepeunit Unit Storage
    
    Поддерживает работу с:
    - env.json - конфигурационные настройки
    - schema.json - схема топиков
    - log.json - логирование
    - MQTT клиент (опционально)
    - REST клиент (опционально)
    """
    
    def __init__(
        self,
        env_path: str,
        schema_path: str,
        log_path: str,
        mqtt_client: Optional[MQTTClientInterface] = None,
        rest_client: Optional[RESTClientInterface] = None
    ):
        """
        Инициализация клиента
        
        Args:
            env_path: Путь до файла env.json
            schema_path: Путь до файла schema.json
            log_path: Путь до файла log.json
            mqtt_client: Опциональный MQTT клиент
            rest_client: Опциональный REST клиент
        """
        self.env_path = Path(env_path)
        self.schema_path = Path(schema_path)
        self.log_path = Path(log_path)
        self.mqtt_client = mqtt_client
        self.rest_client = rest_client
        
        # Загружаем данные при инициализации
        self._env_data = self._load_json_file(self.env_path)
        self._schema_data = self._load_json_file(self.schema_path)
        self._log_data = self._load_json_file(self.log_path)
    
    def _load_json_file(self, file_path: Path) -> Union[Dict[str, Any], List[Any]]:
        """Загружает JSON файл"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {} if file_path.suffix == '.json' else []
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка загрузки файла {file_path}: {e}")
            return {} if file_path.suffix == '.json' else []
    
    def _save_json_file(self, file_path: Path, data: Union[Dict[str, Any], List[Any]]) -> None:
        """Сохраняет данные в JSON файл"""
        try:
            # Создаем директорию если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка сохранения файла {file_path}: {e}")
    
    def _log(self, level: LogLevel, message: str) -> None:
        """Внутреннее логирование"""
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        }
        
        # Добавляем в память
        if isinstance(self._log_data, list):
            self._log_data.append(log_entry)
        else:
            self._log_data = [log_entry]
        
        # Сохраняем в файл
        self._save_json_file(self.log_path, self._log_data)
        
        # Отправляем через MQTT если доступен
        if self.mqtt_client and level.get_int_level() >= LogLevel.INFO.get_int_level():
            try:
                topic = self.get_topic_by_key('log/pepeunit')
                if topic:
                    self.mqtt_client.publish(topic, json.dumps(log_entry))
            except Exception as e:
                print(f"Ошибка отправки лога через MQTT: {e}")
    
    # ==================== Функции работы с env.json ====================
    
    def update_env_from_file(self, file_path: str) -> None:
        """Обновляет env.json из файла по пути"""
        try:
            new_env_data = self._load_json_file(Path(file_path))
            self._env_data = new_env_data
            self._save_json_file(self.env_path, self._env_data)
            self._log(LogLevel.INFO, f"env.json обновлен из файла {file_path}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления env.json: {e}")
    
    def update_env(self, env_dict: Dict[str, Any]) -> None:
        """Обновляет env.json из словаря"""
        try:
            self._env_data.update(env_dict)
            self._save_json_file(self.env_path, self._env_data)
            self._log(LogLevel.INFO, "env.json обновлен")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления env.json: {e}")
    
    def get_env_value(self, key: str, default: Any = None) -> Any:
        """Получает значение из env.json по ключу"""
        return self._env_data.get(key, default)
    
    def get_env_data(self) -> Dict[str, Any]:
        """Получает все данные из env.json"""
        return self._env_data.copy()
    
    # ==================== Функции работы с schema.json ====================
    
    def update_schema_from_file(self, file_path: str) -> None:
        """Обновляет schema.json из файла по пути"""
        try:
            new_schema_data = self._load_json_file(Path(file_path))
            self._schema_data = new_schema_data
            self._save_json_file(self.schema_path, self._schema_data)
            self._log(LogLevel.INFO, f"schema.json обновлен из файла {file_path}")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления schema.json: {e}")
    
    def update_schema(self, schema_dict: Dict[str, Any]) -> None:
        """Обновляет schema.json из словаря"""
        try:
            self._schema_data.update(schema_dict)
            self._save_json_file(self.schema_path, self._schema_data)
            self._log(LogLevel.INFO, "schema.json обновлен")
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления schema.json: {e}")
    
    def get_schema_value(self, key: str, default: Any = None) -> Any:
        """Получает значение из schema.json по ключу"""
        return self._schema_data.get(key, default)
    
    def get_schema_data(self) -> Dict[str, Any]:
        """Получает все данные из schema.json"""
        return self._schema_data.copy()
    
    # ==================== Функции работы с топиками ====================
    
    def get_input_topics(self) -> List[str]:
        """Получает список всех входных топиков для подписки"""
        input_topics = []
        for topic_type in self._schema_data.keys():
            if 'input' in topic_type:
                for topic in self._schema_data[topic_type].keys():
                    if isinstance(self._schema_data[topic_type][topic], list):
                        input_topics.extend(self._schema_data[topic_type][topic])
                    else:
                        input_topics.append(self._schema_data[topic_type][topic])
        return input_topics
    
    def get_topic_by_key(self, key: str) -> Optional[str]:
        """Получает топик по ключу из schema"""
        for topic_type in self._schema_data.keys():
            if topic_type in ['output_base_topic', 'input_base_topic']:
                if key in self._schema_data[topic_type]:
                    topics = self._schema_data[topic_type][key]
                    if isinstance(topics, list) and topics:
                        return topics[0]
                    elif isinstance(topics, str):
                        return topics
        return None
    
    def search_topic_in_schema(self, node_uuid: str) -> Optional[tuple[str, str]]:
        """Ищет топик в схеме по node_uuid"""
        for topic_type in self._schema_data.keys():
            for topic_name in self._schema_data[topic_type].keys():
                topics = self._schema_data[topic_type][topic_name]
                if isinstance(topics, list):
                    for topic in topics:
                        if node_uuid in topic:
                            return topic_type, topic_name
                elif isinstance(topics, str) and node_uuid in topics:
                    return topic_type, topic_name
        return None
    
    # ==================== Функции обновления прошивки ====================
    
    def update_firmware(self, archive_path: str) -> bool:
        """Обновляет прошивку устройства по пути до архива"""
        try:
            # Определяем формат архива
            archive_format = self._get_archive_format(archive_path)
            
            # Создаем временную директорию для распаковки
            temp_dir = Path(archive_path).parent / "temp_update"
            temp_dir.mkdir(exist_ok=True)
            
            # Распаковываем архив
            self._extract_archive(archive_path, str(temp_dir), archive_format)
            
            # Копируем файлы (здесь должна быть логика копирования в нужное место)
            # Для примера просто логируем
            self._log(LogLevel.INFO, f"Прошивка обновлена из архива {archive_path}")
            
            # Очищаем временную директорию
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления прошивки: {e}")
            return False
    
    def _get_archive_format(self, file_path: str) -> str:
        """Определяет формат архива по расширению"""
        ext = Path(file_path).suffix.lower()
        format_mapping = {
            '.zip': 'zip',
            '.tar.gz': 'tgz',
            '.tgz': 'tgz',
            '.tar': 'tar',
            '.gz': 'gztar'
        }
        return format_mapping.get(ext, 'zip')
    
    def _extract_archive(self, file_path: str, extract_path: str, archive_format: str) -> None:
        """Распаковывает архив"""
        if archive_format == 'tgz':
            # Специальная обработка для tgz с zlib
            with open(file_path, 'rb') as f:
                producer = zlib.decompressobj(wbits=9)
                tar_data = producer.decompress(f.read()) + producer.flush()
                tar_filepath = f'{os.path.dirname(file_path)}/update.tar'
                with open(tar_filepath, 'wb') as tar_file:
                    tar_file.write(tar_data)
                shutil.unpack_archive(tar_filepath, extract_path, 'tar')
                os.remove(tar_filepath)
        else:
            shutil.unpack_archive(file_path, extract_path, archive_format)
    
    # ==================== Функции генерации состояния ====================
    
    def generate_device_state(self) -> Dict[str, Any]:
        """Генерирует состояние устройства"""
        try:
            import psutil  # type: ignore
            
            memory_info = psutil.virtual_memory()
            cpu_freq = psutil.cpu_freq()
            
            state = {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': cpu_freq.current if cpu_freq else 0,
                'commit_version': self.get_env_value('COMMIT_VERSION', 'unknown'),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
            
            return state
        except ImportError:
            # Fallback если psutil недоступен
            return {
                'millis': round(time.time() * 1000),
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': self.get_env_value('COMMIT_VERSION', 'unknown'),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка генерации состояния устройства: {e}")
            return {
                'millis': round(time.time() * 1000),
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
            }
    
    # ==================== Функции работы с логами ====================
    
    def save_log(self, level: LogLevel, message: str) -> None:
        """Сохраняет лог в log.json"""
        self._log(level, message)
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Получает все логи"""
        if isinstance(self._log_data, list):
            return self._log_data.copy()
        return []
    
    def clear_logs(self) -> None:
        """Очищает все логи"""
        self._log_data = []
        self._save_json_file(self.log_path, self._log_data)
        self._log(LogLevel.INFO, "Логи очищены")
    
    # ==================== MQTT функции (если клиент передан) ====================
    
    def send_mqtt_message(self, topic: str, message: str) -> bool:
        """Отправляет сообщение через MQTT"""
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT клиент не настроен")
            return False
        
        try:
            self.mqtt_client.publish(topic, message)
            self._log(LogLevel.DEBUG, f"Сообщение отправлено в топик {topic}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка отправки MQTT сообщения: {e}")
            return False
    
    def subscribe_to_topics(self, topics: List[str]) -> bool:
        """Подписывается на топики через MQTT"""
        if not self.mqtt_client:
            self._log(LogLevel.WARNING, "MQTT клиент не настроен")
            return False
        
        try:
            self.mqtt_client.subscribe(topics)
            self._log(LogLevel.INFO, f"Подписка на топики: {topics}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка подписки на топики: {e}")
            return False
    
    def send_log_via_mqtt(self, level: LogLevel, message: str, save_to_file: bool = True) -> bool:
        """Отправляет лог через MQTT с опциональным сохранением в файл"""
        if not self.mqtt_client:
            if save_to_file:
                self.save_log(level, message)
            return False
        
        topic = self.get_topic_by_key('log/pepeunit')
        if not topic:
            if save_to_file:
                self.save_log(LogLevel.WARNING, "Топик для логов не найден в схеме")
            return False
        
        log_entry = {
            'level': level.value,
            'text': message,
            'create_datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
        }
        
        # Сохраняем в файл если нужно
        if save_to_file:
            if isinstance(self._log_data, list):
                self._log_data.append(log_entry)
            else:
                self._log_data = [log_entry]
            self._save_json_file(self.log_path, self._log_data)
        
        return self.send_mqtt_message(topic, json.dumps(log_entry))
    
    # ==================== REST функции (если клиент передан) ====================
    
    def download_and_update_firmware(self, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Скачивает и обновляет прошивку в одну функцию"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST клиент не настроен")
            return False
        
        try:
            # Скачиваем файл
            response = self.rest_client.get(url, headers)
            # Здесь должна быть логика сохранения файла
            # Для примера просто логируем
            self._log(LogLevel.INFO, f"Прошивка скачана с {url}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка скачивания прошивки: {e}")
            return False
    
    def download_and_update_env(self, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Скачивает и обновляет env.json в одну функцию"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST клиент не настроен")
            return False
        
        try:
            response = self.rest_client.get(url, headers)
            self.update_env(response)
            self._log(LogLevel.INFO, f"env.json обновлен с {url}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления env.json: {e}")
            return False
    
    def download_and_update_schema(self, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
        """Скачивает и обновляет schema.json в одну функцию"""
        if not self.rest_client:
            self._log(LogLevel.WARNING, "REST клиент не настроен")
            return False
        
        try:
            response = self.rest_client.get(url, headers)
            self.update_schema(response)
            self._log(LogLevel.INFO, f"schema.json обновлен с {url}")
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"Ошибка обновления schema.json: {e}")
            return False
