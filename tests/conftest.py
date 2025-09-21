import json
import os
import tempfile
import pytest
from typing import Dict, Any


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_env_data() -> Dict[str, Any]:
    return {
        "PEPEUNIT_URL": "api.pepeunit.dev",
        "PEPEUNIT_APP_PREFIX": "/app",
        "PEPEUNIT_API_ACTUAL_PREFIX": "/api/v1",
        "HTTP_TYPE": "https",
        "MQTT_URL": "mqtt.pepeunit.dev",
        "MQTT_PORT": 1883,
        "PEPEUNIT_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiMTIzNDU2NzgtYWJjZC1lZmdoLWlqa2wtbW5vcHFyc3R1dnd4Iiwic3ViIjoiMTIzNDU2NzgwIiwibmFtZSI6IlRlc3QgVW5pdCIsImlhdCI6MTUxNjIzOTAyMn0.test_signature",
        "SYNC_ENCRYPT_KEY": "test_encrypt_key",
        "SECRET_KEY": "test_secret_key",
        "COMMIT_VERSION": "v1.0.0",
        "PING_INTERVAL": 30,
        "STATE_SEND_INTERVAL": 300
    }


@pytest.fixture
def sample_schema_data() -> Dict[str, Any]:
    return {
        "input_base_topic": {
            "update/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/update"],
            "env_update/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/env_update"],
            "schema_update/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/schema_update"],
            "log_sync/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/log_sync"]
        },
        "output_base_topic": {
            "state/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/state"],
            "log/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/log"]
        },
        "input_topic": {
            "input/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/input"]
        },
        "output_topic": {
            "output/pepeunit": ["devunit.pepeunit.com/12345678-abcd-efgh-ijkl-mnopqrstuvwx/output"]
        }
    }


@pytest.fixture
def sample_log_data() -> list:
    return [
        {
            "level": "Info",
            "text": "Test log entry 1",
            "create_datetime": "2023-01-01T12:00:00.000000"
        },
        {
            "level": "Debug",
            "text": "Test log entry 2", 
            "create_datetime": "2023-01-01T12:01:00.000000"
        }
    ]


@pytest.fixture
def test_files(temp_dir, sample_env_data, sample_schema_data, sample_log_data):
    env_path = os.path.join(temp_dir, "env.json")
    schema_path = os.path.join(temp_dir, "schema.json")
    log_path = os.path.join(temp_dir, "log.json")
    
    with open(env_path, 'w') as f:
        json.dump(sample_env_data, f)
    
    with open(schema_path, 'w') as f:
        json.dump(sample_schema_data, f)
    
    with open(log_path, 'w') as f:
        json.dump(sample_log_data, f)
    
    return {
        "env_path": env_path,
        "schema_path": schema_path,
        "log_path": log_path,
        "temp_dir": temp_dir
    }


@pytest.fixture
def mock_mqtt_client():
    class MockMQTTClient:
        def __init__(self):
            self.is_connected = False
            self.subscribed_topics = []
            self.published_messages = []
            self.message_handler = None
        
        def connect(self):
            self.is_connected = True
        
        def disconnect(self):
            self.is_connected = False
        
        def subscribe(self, topics):
            self.subscribed_topics.extend(topics)
        
        def unsubscribe(self, topics):
            for topic in topics:
                if topic in self.subscribed_topics:
                    self.subscribed_topics.remove(topic)
        
        def publish(self, topic, message):
            self.published_messages.append((topic, message))
            return True
        
        def set_message_handler(self, handler):
            self.message_handler = handler
        
        def start_loop(self):
            pass
        
        def stop_loop(self):
            pass
    
    return MockMQTTClient()


@pytest.fixture
def mock_rest_client():
    class MockRESTClient:
        def __init__(self):
            self.requests = []
        
        def get(self, url, headers=None):
            self.requests.append(('GET', url, None, headers))
            return {"status": "success", "data": "test"}
        
        def post(self, url, data=None, headers=None):
            self.requests.append(('POST', url, data, headers))
            return {"status": "success", "data": "test"}
        
        def put(self, url, data=None, headers=None):
            self.requests.append(('PUT', url, data, headers))
            return {"status": "success", "data": "test"}
        
        def delete(self, url, headers=None):
            self.requests.append(('DELETE', url, None, headers))
            return {"status": "success", "data": "test"}
        
        def download_file(self, url, file_path, headers=None):
            self.requests.append(('DOWNLOAD', url, file_path, headers))
            with open(file_path, 'w') as f:
                f.write("test file content")
    
    return MockRESTClient()
