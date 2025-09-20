"""
Integration tests for PepeunitClient class.
Tests cover all methods of the PepeunitClient class.
"""

import json
import tempfile
from pathlib import Path

import pytest

from pepeunit_client import PepeunitClient, LogLevel


class TestPepeunitClientInitialization:
    """Test PepeunitClient initialization."""
    
    def test_init_without_clients(self, client):
        """Test initialization without MQTT and REST clients."""
        assert client.env_path.exists()
        assert client.schema_path.exists()
        assert client.log_path.exists()
        assert client.mqtt_client is None
        assert client.rest_client is None
        assert client.settings is not None
    
    def test_init_with_mqtt_client(self, client_with_mqtt):
        """Test initialization with MQTT client."""
        assert client_with_mqtt.mqtt_client is not None
        assert client_with_mqtt.rest_client is None
    
    def test_init_with_rest_client(self, client_with_rest):
        """Test initialization with REST client."""
        assert client_with_rest.mqtt_client is None
        assert client_with_rest.rest_client is not None
    
    def test_init_with_both_clients(self, client_with_both):
        """Test initialization with both MQTT and REST clients."""
        assert client_with_both.mqtt_client is not None
        assert client_with_both.rest_client is not None


class TestEnvJsonFunctions:
    """Test env.json related functions."""
    
    def test_update_env_from_file(self, client, temp_dir, env_data):
        """Test updating env.json from file."""
        new_env_data = {"NEW_SETTING": "new_value", "PING_INTERVAL": 60}
        new_env_path = temp_dir / "new_env.json"
        
        with open(new_env_path, 'w') as f:
            json.dump(new_env_data, f)
        
        client.update_env_from_file(str(new_env_path))
        
        assert client.get_env_value("NEW_SETTING") == "new_value"
        assert client.get_env_value("PING_INTERVAL") == 60
    
    def test_update_env_from_dict(self, client):
        """Test updating env.json from dictionary."""
        new_data = {"CUSTOM_SETTING_2": "value_2", "PING_INTERVAL": 45}
        client.update_env(new_data)
        
        assert client.get_env_value("CUSTOM_SETTING_2") == "value_2"
        assert client.get_env_value("PING_INTERVAL") == 45
    
    def test_get_env_value(self, client, env_data):
        """Test getting value from env.json by key."""
        assert client.get_env_value("PEPEUNIT_URL") == env_data["PEPEUNIT_URL"]
        assert client.get_env_value("NON_EXISTENT_KEY", "default") == "default"
    
    def test_get_env_data(self, client, env_data):
        """Test getting all env.json data."""
        data = client.get_env_data()
        assert isinstance(data, dict)
        assert "PEPEUNIT_URL" in data
    
    def test_get_reserved_settings(self, client):
        """Test getting only reserved settings."""
        reserved = client.get_reserved_settings()
        assert isinstance(reserved, dict)
        assert "PEPEUNIT_URL" in reserved
        assert "CUSTOM_SETTING" not in reserved
    
    def test_get_custom_settings(self, client):
        """Test getting only custom settings."""
        custom = client.get_custom_settings()
        assert isinstance(custom, dict)
        assert "CUSTOM_SETTING" in custom
        assert "PEPEUNIT_URL" not in custom


class TestSchemaJsonFunctions:
    """Test schema.json related functions."""
    
    def test_update_schema_from_file(self, client, temp_dir, schema_data):
        """Test updating schema.json from file."""
        new_schema_data = {"new_topic_type": {"new_topic": "new_value"}}
        new_schema_path = temp_dir / "new_schema.json"
        
        with open(new_schema_path, 'w') as f:
            json.dump(new_schema_data, f)
        
        client.update_schema_from_file(str(new_schema_path))
        
        assert client.get_schema_value("new_topic_type") == new_schema_data["new_topic_type"]
    
    def test_update_schema_from_dict(self, client):
        """Test updating schema.json from dictionary."""
        new_data = {"additional_topic": {"test": "value"}}
        client.update_schema(new_data)
        
        assert client.get_schema_value("additional_topic") == new_data["additional_topic"]
    
    def test_get_schema_value(self, client, schema_data):
        """Test getting value from schema.json by key."""
        assert client.get_schema_value("output_base_topic") == schema_data["output_base_topic"]
        assert client.get_schema_value("NON_EXISTENT_KEY", "default") == "default"
    
    def test_get_schema_data(self, client, schema_data):
        """Test getting all schema.json data."""
        data = client.get_schema_data()
        assert isinstance(data, dict)
        assert "output_base_topic" in data


class TestTopicsFunctions:
    """Test topics related functions."""
    
    def test_get_input_topics(self, client, schema_data):
        """Test getting input topics for subscription."""
        topics = client.get_input_topics()
        assert isinstance(topics, list)
        # Should find topics from input_base_topic
        assert any("commands" in topic for topic in topics)
    
    def test_get_topic_by_key(self, client, schema_data):
        """Test getting topic by key from schema."""
        topic = client.get_topic_by_key("log/pepeunit")
        assert topic == "pepeunit/logs"
        
        non_existent = client.get_topic_by_key("non_existent")
        assert non_existent is None
    
    def test_search_topic_in_schema(self, client, schema_data):
        """Test searching topic in schema by node_uuid."""
        # This test would need actual node_uuid in topics
        result = client.search_topic_in_schema("pepeunit")
        # Should return None if not found
        assert result is None or isinstance(result, tuple)


class TestDeviceStateFunctions:
    """Test device state generation functions."""
    
    def test_generate_device_state(self, client):
        """Test generating device state."""
        state = client.generate_device_state()
        
        assert isinstance(state, dict)
        assert "millis" in state
        assert "timestamp" in state
        assert "commit_version" in state
        assert isinstance(state["millis"], int)
        assert isinstance(state["timestamp"], str)


class TestLoggingFunctions:
    """Test logging related functions."""
    
    def test_save_log(self, client):
        """Test saving log."""
        initial_logs = len(client.get_all_logs())
        client.save_log(LogLevel.INFO, "Test log message")
        
        logs = client.get_all_logs()
        assert len(logs) == initial_logs + 1
        assert logs[-1]["level"] == "Info"
        assert logs[-1]["text"] == "Test log message"
    
    def test_get_all_logs(self, client):
        """Test getting all logs."""
        logs = client.get_all_logs()
        assert isinstance(logs, list)
    
    def test_clear_logs(self, client):
        """Test clearing all logs."""
        client.save_log(LogLevel.INFO, "Test message")
        assert len(client.get_all_logs()) > 0
        
        client.clear_logs()
        assert len(client.get_all_logs()) == 0


class TestMQTTFunctions:
    """Test MQTT related functions."""
    
    def test_send_mqtt_message_without_client(self, client):
        """Test sending MQTT message without client."""
        result = client.send_mqtt_message("test/topic", "test message")
        assert result is False
    
    def test_send_mqtt_message_with_client(self, client_with_mqtt, mock_mqtt_client):
        """Test sending MQTT message with client."""
        result = client_with_mqtt.send_mqtt_message("test/topic", "test message")
        assert result is True
        assert len(mock_mqtt_client.published_messages) == 1
        assert mock_mqtt_client.published_messages[0] == ("test/topic", "test message")
    
    def test_subscribe_to_topics_without_client(self, client):
        """Test subscribing to topics without client."""
        result = client.subscribe_to_topics(["test/topic1", "test/topic2"])
        assert result is False
    
    def test_subscribe_to_topics_with_client(self, client_with_mqtt, mock_mqtt_client):
        """Test subscribing to topics with client."""
        topics = ["test/topic1", "test/topic2"]
        result = client_with_mqtt.subscribe_to_topics(topics)
        assert result is True
        assert mock_mqtt_client.subscribed_topics == topics
    
    def test_send_log_via_mqtt_without_client(self, client):
        """Test sending log via MQTT without client."""
        result = client.send_log_via_mqtt(LogLevel.INFO, "Test log", save_to_file=True)
        assert result is False
    
    def test_send_log_via_mqtt_with_client(self, client_with_mqtt, mock_mqtt_client):
        """Test sending log via MQTT with client."""
        result = client_with_mqtt.send_log_via_mqtt(LogLevel.INFO, "Test log", save_to_file=True)
        assert result is True
        assert len(mock_mqtt_client.published_messages) == 1
        
        # Check that message was published
        topic, payload = mock_mqtt_client.published_messages[0]
        assert topic == "pepeunit/logs"
        
        # Parse payload to check structure
        log_data = json.loads(payload)
        assert log_data["level"] == "Info"
        assert log_data["text"] == "Test log"


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_invalid_json_file_handling(self, client, temp_dir):
        """Test handling of invalid JSON files."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("invalid json content")
        
        # Should not raise exception
        client.update_env_from_file(str(invalid_file))
        client.update_schema_from_file(str(invalid_file))
    
    def test_missing_file_handling(self, temp_dir):
        """Test handling of missing files."""
        # Create client with non-existent files
        client = PepeunitClient(
            env_path=str(temp_dir / "missing_env.json"),
            schema_path=str(temp_dir / "missing_schema.json"),
            log_path=str(temp_dir / "missing_log.json")
        )
        
        # Should not raise exception and should have default values
        assert client.settings is not None
        assert isinstance(client.get_all_logs(), list)
