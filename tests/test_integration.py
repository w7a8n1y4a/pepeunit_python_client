import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from pepeunit_client import PepeunitClient, MQTTClient, RESTClient, LogLevel


class TestIntegration:
    
    def setup_method(self):
        # Create temporary files for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_path = self.temp_dir / "env.json"
        self.schema_path = self.temp_dir / "schema.json"
        self.log_path = self.temp_dir / "log.json"
        
        # Create test data
        env_data = {
            "PEPEUNIT_URL": "test.example.com",
            "PEPEUNIT_TOKEN": "test-token",
            "MQTT_URL": "mqtt.example.com",
            "MQTT_PORT": 1883,
            "COMMIT_VERSION": "1.0.0"
        }
        
        schema_data = {
            "output_base_topic": {
                "log/pepeunit": ["pepeunit/unit/test/log"],
                "state/pepeunit": ["pepeunit/unit/test/state"]
            },
            "input_base_topic": {
                "update": ["pepeunit/unit/test/update"],
                "env_update": ["pepeunit/unit/test/env_update"]
            },
            "output_topic": {
                "output/pepeunit": ["pepeunit/unit/test/output"]
            }
        }
        
        # Write test files
        with open(self.env_path, 'w') as f:
            json.dump(env_data, f)
        
        with open(self.schema_path, 'w') as f:
            json.dump(schema_data, f)
        
        with open(self.log_path, 'w') as f:
            json.dump([], f)
    
    def teardown_method(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pepeunit_client_without_clients(self):
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path)
        )
        
        assert client.mqtt_client is None
        assert client.rest_client is None
        assert client.settings.PEPEUNIT_URL == "test.example.com"
        assert client.settings.PEPEUNIT_TOKEN == "test-token"
    
    def test_pepeunit_client_with_mqtt_client(self):
        mqtt_client = MQTTClient(
            host="mqtt.example.com",
            port=1883,
            username="test-token"
        )
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            mqtt_client=mqtt_client
        )
        
        assert client.mqtt_client is not None
        assert client.rest_client is None
        assert isinstance(client.mqtt_client, MQTTClient)
    
    def test_pepeunit_client_with_rest_client(self):
        rest_client = RESTClient(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer test-token"}
        )
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            rest_client=rest_client
        )
        
        assert client.mqtt_client is None
        assert client.rest_client is not None
        assert isinstance(client.rest_client, RESTClient)
    
    def test_pepeunit_client_with_both_clients(self):
        mqtt_client = MQTTClient(
            host="mqtt.example.com",
            port=1883,
            username="test-token"
        )
        
        rest_client = RESTClient(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer test-token"}
        )
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            mqtt_client=mqtt_client,
            rest_client=rest_client
        )
        
        assert client.mqtt_client is not None
        assert client.rest_client is not None
        assert isinstance(client.mqtt_client, MQTTClient)
        assert isinstance(client.rest_client, RESTClient)
    
    def test_mqtt_message_sending(self):
        mqtt_client = MQTTClient(host="mqtt.example.com")
        mqtt_client._connected = True  # Simulate connected state
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            mqtt_client=mqtt_client
        )
        
        with patch.object(mqtt_client, 'publish', return_value=True) as mock_publish:
            result = client.send_mqtt_message("test/topic", "test message")
            
            assert result is True
            mock_publish.assert_called_once_with("test/topic", "test message")
    
    def test_mqtt_topic_subscription(self):
        mqtt_client = MQTTClient(host="mqtt.example.com")
        mqtt_client._connected = True  # Simulate connected state
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            mqtt_client=mqtt_client
        )
        
        with patch.object(mqtt_client, 'subscribe', return_value=True) as mock_subscribe:
            topics = ["topic1", "topic2"]
            result = client.subscribe_to_topics(topics)
            
            assert result is True
            mock_subscribe.assert_called_once_with(topics)
    
    def test_log_sending_via_mqtt(self):
        mqtt_client = MQTTClient(host="mqtt.example.com")
        mqtt_client._connected = True  # Simulate connected state
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            mqtt_client=mqtt_client
        )
        
        with patch.object(mqtt_client, 'publish', return_value=True) as mock_publish:
            result = client.send_log_via_mqtt(LogLevel.INFO, "Test log message")
            
            assert result is True
            mock_publish.assert_called_once()
            
            # Check that the published message contains log data
            call_args = mock_publish.call_args
            published_data = json.loads(call_args[0][1])
            assert published_data["level"] == "Info"
            assert published_data["text"] == "Test log message"
    
    def test_rest_client_usage(self):
        rest_client = RESTClient(base_url="https://api.example.com")
        
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path),
            rest_client=rest_client
        )
        
        # Test that we can access the REST client
        assert client.rest_client is not None
        assert client.rest_client.base_url == "https://api.example.com"
    
    def test_schema_operations(self):
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path)
        )
        
        # Test getting input topics
        input_topics = client.get_input_topics()
        assert "pepeunit/unit/test/update" in input_topics
        assert "pepeunit/unit/test/env_update" in input_topics
        
        # Test getting topic by key
        log_topic = client.get_topic_by_key("log/pepeunit")
        assert log_topic == "pepeunit/unit/test/log"
        
        # Test searching topic in schema
        topic_type, topic_name = client.search_topic_in_schema("test")
        assert topic_type == "output_base_topic"
        assert topic_name == "log/pepeunit"
    
    def test_env_operations(self):
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path)
        )
        
        # Test getting env value
        url = client.get_env_value("PEPEUNIT_URL")
        assert url == "test.example.com"
        
        # Test getting default value
        default_value = client.get_env_value("NON_EXISTENT_KEY", "default")
        assert default_value == "default"
        
        # Test updating env
        client.update_env({"NEW_KEY": "new_value"})
        new_value = client.get_env_value("NEW_KEY")
        assert new_value == "new_value"
    
    def test_log_operations(self):
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path)
        )
        
        # Test saving log
        client.save_log(LogLevel.INFO, "Test log message")
        
        # Test getting all logs
        logs = client.get_all_logs()
        assert len(logs) == 1
        assert logs[0]["level"] == "Info"
        assert logs[0]["text"] == "Test log message"
        
        # Test clearing logs
        client.clear_logs()
        logs = client.get_all_logs()
        assert len(logs) == 0
    
    def test_device_state_generation(self):
        client = PepeunitClient(
            env_path=str(self.env_path),
            schema_path=str(self.schema_path),
            log_path=str(self.log_path)
        )
        
        state = client.generate_device_state()
        
        assert "millis" in state
        assert "commit_version" in state
        assert state["commit_version"] == "1.0.0"
        assert "timestamp" in state
    
    def test_mqtt_client_connection_simulation(self):
        mqtt_client = MQTTClient(host="mqtt.example.com", port=1883)
        
        # Test initial state
        assert not mqtt_client.is_connected()
        assert mqtt_client.get_connection_error() is None
        
        # Simulate connection
        mqtt_client._connected = True
        assert mqtt_client.is_connected()
        
        # Test client info
        info = mqtt_client.get_client_info()
        assert info["host"] == "mqtt.example.com"
        assert info["port"] == 1883
        assert info["connected"] is True
    
    def test_rest_client_configuration(self):
        rest_client = RESTClient(
            base_url="https://api.example.com",
            timeout=60.0,
            headers={"Authorization": "Bearer token"}
        )
        
        # Test client info
        info = rest_client.get_client_info()
        assert info["base_url"] == "https://api.example.com"
        assert info["timeout"] == 60.0
        assert info["default_headers"]["Authorization"] == "Bearer token"
        
        # Test header management
        rest_client.add_default_header("X-Custom", "value")
        assert rest_client._default_headers["X-Custom"] == "value"
        
        rest_client.remove_default_header("X-Custom")
        assert "X-Custom" not in rest_client._default_headers
