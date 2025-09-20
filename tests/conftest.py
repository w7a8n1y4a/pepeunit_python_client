"""
Test configuration and fixtures for PepeunitClient integration tests.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

from pepeunit_client import PepeunitClient, LogLevel


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def env_data() -> Dict[str, Any]:
    """Sample environment data for testing."""
    return {
        "PEPEUNIT_URL": "https://test.example.com",
        "HTTP_TYPE": "https",
        "PEPEUNIT_APP_PREFIX": "/app",
        "PEPEUNIT_API_ACTUAL_PREFIX": "/api/v1",
        "MQTT_URL": "test.mqtt.example.com",
        "MQTT_PORT": 1883,
        "PEPEUNIT_TOKEN": "test_token_123",
        "SYNC_ENCRYPT_KEY": "test_encrypt_key",
        "SECRET_KEY": "test_secret_key",
        "COMMIT_VERSION": "test_commit_123",
        "PING_INTERVAL": 30,
        "STATE_SEND_INTERVAL": 300,
        "CUSTOM_SETTING": "custom_value"
    }


@pytest.fixture
def schema_data() -> Dict[str, Any]:
    """Sample schema data for testing."""
    return {
        "output_base_topic": {
            "log/pepeunit": "pepeunit/logs",
            "state/device": "pepeunit/state"
        },
        "input_base_topic": {
            "commands": "pepeunit/commands",
            "config": "pepeunit/config"
        }
    }


@pytest.fixture
def log_data() -> list:
    """Sample log data for testing."""
    return []


@pytest.fixture
def test_files(temp_dir, env_data, schema_data, log_data):
    """Create test JSON files."""
    env_path = temp_dir / "env.json"
    schema_path = temp_dir / "schema.json"
    log_path = temp_dir / "log.json"
    
    with open(env_path, 'w') as f:
        json.dump(env_data, f)
    
    with open(schema_path, 'w') as f:
        json.dump(schema_data, f)
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f)
    
    return {
        "env_path": str(env_path),
        "schema_path": str(schema_path),
        "log_path": str(log_path)
    }


@pytest.fixture
def client(test_files):
    """Create PepeunitClient instance for testing."""
    return PepeunitClient(
        env_path=test_files["env_path"],
        schema_path=test_files["schema_path"],
        log_path=test_files["log_path"]
    )


class MockMQTTClient:
    """Mock MQTT client for testing."""
    
    def __init__(self):
        self.published_messages = []
        self.subscribed_topics = []
    
    def publish(self, topic: str, payload: str) -> None:
        self.published_messages.append((topic, payload))
    
    def subscribe(self, topics: list) -> None:
        self.subscribed_topics.extend(topics)


class MockRESTClient:
    """Mock REST client for testing."""
    
    def __init__(self):
        self.requests = []
    
    def get(self, url: str, headers: dict = None) -> dict:
        self.requests.append(("GET", url, headers))
        return {"status": "success", "data": "test_data"}
    
    def post(self, url: str, data: dict = None, headers: dict = None) -> dict:
        self.requests.append(("POST", url, data, headers))
        return {"status": "success", "data": "test_data"}


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client for testing."""
    return MockMQTTClient()


@pytest.fixture
def mock_rest_client():
    """Mock REST client for testing."""
    return MockRESTClient()


@pytest.fixture
def client_with_mqtt(test_files, mock_mqtt_client):
    """Create PepeunitClient with MQTT client."""
    return PepeunitClient(
        env_path=test_files["env_path"],
        schema_path=test_files["schema_path"],
        log_path=test_files["log_path"],
        mqtt_client=mock_mqtt_client
    )


@pytest.fixture
def client_with_rest(test_files, mock_rest_client):
    """Create PepeunitClient with REST client."""
    return PepeunitClient(
        env_path=test_files["env_path"],
        schema_path=test_files["schema_path"],
        log_path=test_files["log_path"],
        rest_client=mock_rest_client
    )


@pytest.fixture
def client_with_both(test_files, mock_mqtt_client, mock_rest_client):
    """Create PepeunitClient with both MQTT and REST clients."""
    return PepeunitClient(
        env_path=test_files["env_path"],
        schema_path=test_files["schema_path"],
        log_path=test_files["log_path"],
        mqtt_client=mock_mqtt_client,
        rest_client=mock_rest_client
    )
