"""
Основные фикстуры для тестирования pepeunit_client
"""
import json
import os
import tempfile
import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock, patch

from pepeunit_client.settings import Settings
from pepeunit_client.schema_manager import SchemaManager
from pepeunit_client.logger import Logger
from pepeunit_client.file_manager import FileManager
from pepeunit_client.abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient


@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_env_data() -> Dict[str, Any]:
    """Тестовые данные для env.json"""
    return {
        "DELAY_PUB_MSG": 1,
        "PEPEUNIT_URL": "devunit.pepeunit.com",
        "HTTP_TYPE": "https",
        "PEPEUNIT_APP_PREFIX": "/pepeunit",
        "PEPEUNIT_API_ACTUAL_PREFIX": "/api/v1",
        "MQTT_URL": "devemqx.pepemoss.com",
        "MQTT_PORT": 1884,
        "PEPEUNIT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiMzc0ZDQxZTQtMTUzYi00ZDNlLWFiYTAtYTA4ODM3NGVjZDJkIiwidHlwZSI6IlVuaXQifQ.rSc4H18Jfuk_-gh4NCFWKTAyj5ckHz2ZmlwXoGjtr2I",
        "SYNC_ENCRYPT_KEY": "PoTHLHYFIwke9W8aM3TefA==",
        "SECRET_KEY": "ZxtLN+kN5Sif+lr5rpFJMQ==",
        "PING_INTERVAL": 30,
        "STATE_SEND_INTERVAL": 2,
        "COMMIT_VERSION": "d4218da85305798c783a51dd25944bfa0b40903b"
    }


@pytest.fixture
def sample_schema_data() -> Dict[str, Any]:
    """Тестовые данные для schema.json"""
    return {
        "input_base_topic": {
            "update/pepeunit": [
                "devunit.pepeunit.com/input_base_topic/374d41e4-153b-4d3e-aba0-a088374ecd2d/update/pepeunit"
            ],
            "env_update/pepeunit": [
                "devunit.pepeunit.com/input_base_topic/374d41e4-153b-4d3e-aba0-a088374ecd2d/env_update/pepeunit"
            ],
            "schema_update/pepeunit": [
                "devunit.pepeunit.com/input_base_topic/374d41e4-153b-4d3e-aba0-a088374ecd2d/schema_update/pepeunit"
            ],
            "log_sync/pepeunit": [
                "devunit.pepeunit.com/input_base_topic/374d41e4-153b-4d3e-aba0-a088374ecd2d/log_sync/pepeunit"
            ]
        },
        "output_base_topic": {
            "state/pepeunit": [
                "devunit.pepeunit.com/output_base_topic/374d41e4-153b-4d3e-aba0-a088374ecd2d/state/pepeunit"
            ],
            "log/pepeunit": [
                "devunit.pepeunit.com/output_base_topic/374d41e4-153b-4d3e-aba0-a088374ecd2d/log/pepeunit"
            ]
        },
        "input_topic": {
            "input/pepeunit": [
                "devunit.pepeunit.com/751ea411-8068-42df-9c65-987f122f670e/pepeunit"
            ]
        },
        "output_topic": {
            "output/pepeunit": [
                "devunit.pepeunit.com/8e912700-5fba-40fc-9f45-be0ccb6a63fd/pepeunit"
            ]
        }
    }


@pytest.fixture
def env_file(temp_dir, sample_env_data) -> str:
    """Создает временный файл env.json"""
    env_path = os.path.join(temp_dir, "env.json")
    with open(env_path, 'w') as f:
        json.dump(sample_env_data, f)
    return env_path


@pytest.fixture
def schema_file(temp_dir, sample_schema_data) -> str:
    """Создает временный файл schema.json"""
    schema_path = os.path.join(temp_dir, "schema.json")
    with open(schema_path, 'w') as f:
        json.dump(sample_schema_data, f)
    return schema_path


@pytest.fixture
def log_file(temp_dir) -> str:
    """Создает путь для временного файла log.json"""
    return os.path.join(temp_dir, "log.json")


@pytest.fixture
def mock_settings(env_file, sample_env_data) -> Settings:
    """Мок объект Settings с тестовыми данными"""
    settings = Settings(env_file)
    return settings


@pytest.fixture
def mock_schema_manager(schema_file) -> SchemaManager:
    """Мок объект SchemaManager с тестовыми данными"""
    return SchemaManager(schema_file)


@pytest.fixture
def mock_logger(log_file, mock_settings, mock_schema_manager) -> Logger:
    """Мок объект Logger"""
    return Logger(log_file, None, mock_schema_manager, mock_settings)


@pytest.fixture
def mock_mqtt_client():
    """Мок MQTT клиента"""
    mock_client = Mock(spec=AbstractPepeunitMqttClient)
    mock_client.connect = Mock()
    mock_client.disconnect = Mock()
    mock_client.subscribe_topics = Mock()
    mock_client.publish = Mock()
    mock_client.set_input_handler = Mock()
    return mock_client


@pytest.fixture
def mock_rest_client():
    """Мок REST клиента"""
    mock_client = Mock(spec=AbstractPepeunitRestClient)
    mock_client.download_update = Mock()
    mock_client.download_env = Mock()
    mock_client.download_schema = Mock()
    mock_client.set_state_storage = Mock()
    mock_client.get_state_storage = Mock(return_value={"test": "data"})
    return mock_client


@pytest.fixture
def mock_paho_mqtt():
    """Мок paho-mqtt клиента"""
    with patch('pepeunit_client.pepeunit_mqtt_client.mqtt_client_paho') as mock_mqtt_module:
        mock_client = MagicMock()
        mock_mqtt_module.Client.return_value = mock_client
        mock_mqtt_module.CallbackAPIVersion.VERSION1 = "VERSION1"
        yield mock_client


@pytest.fixture
def mock_httpx():
    """Мок httpx клиента"""
    with patch('pepeunit_client.pepeunit_rest_client.httpx') as mock_httpx_module:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"test content"
        mock_response.json.return_value = {"test": "data"}
        
        mock_httpx_module.get.return_value = mock_response
        mock_httpx_module.put.return_value = mock_response
        
        yield mock_httpx_module


@pytest.fixture
def mock_psutil():
    """Мок psutil для системной информации"""
    with patch('pepeunit_client.client.psutil') as mock_psutil:
        mock_memory = MagicMock()
        mock_memory.available = 8000000000
        mock_memory.total = 16000000000
        
        mock_cpu_freq = MagicMock()
        mock_cpu_freq.current = 2400.0
        
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_freq.return_value = mock_cpu_freq
        
        yield mock_psutil


@pytest.fixture
def mock_datetime():
    """Мок datetime для контроля времени в тестах"""
    with patch('pepeunit_client.logger.datetime') as mock_dt:
        mock_dt.datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T00:00:00.000000"
        yield mock_dt


@pytest.fixture
def mock_time():
    """Мок time для контроля времени в тестах"""
    with patch('time.time') as mock_time_func:
        mock_time_func.return_value = 1672531200.0  # 2023-01-01 00:00:00 UTC
        yield mock_time_func


@pytest.fixture
def sample_log_entries():
    """Примеры записей лога для тестирования"""
    return [
        {
            "level": "Info",
            "text": "Test info message",
            "create_datetime": "2023-01-01T00:00:00.000000"
        },
        {
            "level": "Error", 
            "text": "Test error message",
            "create_datetime": "2023-01-01T00:01:00.000000"
        }
    ]


@pytest.fixture
def mock_jwt_token():
    """Мок JWT токена для тестирования"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoidGVzdC11dWlkLTEyMzQiLCJpYXQiOjE2NzI1MzEyMDB9.test_signature"


class MockMessage:
    """Мок MQTT сообщения"""
    def __init__(self, topic: str, payload: str):
        self.topic = topic
        self.payload = payload.encode()


@pytest.fixture
def mock_mqtt_message():
    """Фабрика для создания мок MQTT сообщений"""
    def _create_message(topic: str, payload: str) -> MockMessage:
        return MockMessage(topic, payload)
    return _create_message


@pytest.fixture(autouse=True)
def mock_subprocess():
    """Автоматический мок subprocess для предотвращения реальных системных вызовов"""
    with patch('subprocess.Popen') as mock_popen:
        yield mock_popen


@pytest.fixture(autouse=True) 
def mock_sys_exit():
    """Автоматический мок sys.exit для предотвращения выхода из тестов"""
    with patch('sys.exit') as mock_exit:
        yield mock_exit
