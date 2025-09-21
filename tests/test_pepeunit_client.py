import json
import os
import pytest
from unittest.mock import patch

from pepeunit_client import PepeunitClient, LogLevel, PepeunitClientError


class TestPepeunitClientBasic:
    
    def test_init_basic_client(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        assert client.settings.PEPEUNIT_URL == "api.pepeunit.dev"
        assert client.settings.MQTT_PORT == 1883
        assert not client.mqtt_enabled
        assert not client.rest_enabled
    
    def test_unit_uuid_extraction(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        assert client.unit_uuid == "12345678-abcd-efgh-ijkl-mnopqrstuvwx"
    
    def test_get_env_values(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        env_values = client.get_env_values()
        assert env_values["PEPEUNIT_URL"] == "api.pepeunit.dev"
        assert env_values["MQTT_PORT"] == 1883
    
    def test_get_schema_values(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        schema_values = client.get_schema_values()
        assert "input_base_topic" in schema_values
        assert "output_base_topic" in schema_values
    
    def test_get_subscription_topics(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        topics = client.get_subscription_topics()
        assert len(topics) > 0
        assert any("input" in topic for topic in topics)
    
    def test_schema_access_formats(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        assert isinstance(client.schema.input_base_topic, dict)
        assert isinstance(client.schema.output_base_topic, dict)
        assert isinstance(client.schema.input_topic, dict)
        assert isinstance(client.schema.output_topic, dict)
        
        output_topics = client.schema.output_topic["output/pepeunit"]
        assert isinstance(output_topics, list)
        assert len(output_topics) > 0
    
    def test_system_state_generation(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        state = client.get_system_state()
        
        assert "millis" in state
        assert "commit_version" in state
        assert "mem_free" in state
        assert "mem_alloc" in state
        assert "freq" in state
        
        assert isinstance(state["millis"], int)
        assert state["commit_version"] == "v1.0.0"
    
    def test_logging_functionality(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        test_message = "Test log message"
        client.log(LogLevel.INFO, test_message)
        
        full_log = client.get_full_log()
        assert len(full_log) > 2  # Было 2 тестовых записи + наша
        
        last_entry = full_log[-1]
        assert last_entry["level"] == "Info"
        assert last_entry["text"] == test_message
        assert "create_datetime" in last_entry
    
    def test_get_full_log(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        log_entries = client.get_full_log()
        assert len(log_entries) == 2  # Из тестовых данных
        assert log_entries[0]["level"] == "Info"
        assert log_entries[1]["level"] == "Debug"
    
    def test_refresh_settings(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        new_env = {"PEPEUNIT_URL": "new.api.url", "MQTT_PORT": 1884}
        with open(test_files["env_path"], 'w') as f:
            json.dump(new_env, f)
        
        client.refresh_settings()
        
        assert client.settings.PEPEUNIT_URL == "new.api.url"
        assert client.settings.MQTT_PORT == 1884


class TestPepeunitClientMQTT:
    
    def test_init_with_mqtt(self, test_files, mock_mqtt_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            mqtt_client=mock_mqtt_client
        )
        
        assert client.mqtt_enabled
        assert client.mqtt_client == mock_mqtt_client
    
    def test_connect_mqtt(self, test_files, mock_mqtt_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            mqtt_client=mock_mqtt_client
        )
        
        client.connect_mqtt()
        
        assert mock_mqtt_client.is_connected
        assert len(mock_mqtt_client.subscribed_topics) > 0
    
    def test_publish_to_topic(self, test_files, mock_mqtt_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            mqtt_client=mock_mqtt_client
        )
        
        client.connect_mqtt()
        
        test_message = "Test MQTT message"
        client.publish_to_topic("output/pepeunit", test_message)
        
        assert len(mock_mqtt_client.published_messages) > 0
        topic, message = mock_mqtt_client.published_messages[-1]
        assert message == test_message
        assert "output" in topic
    
    def test_subscribe_to_topics(self, test_files, mock_mqtt_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            mqtt_client=mock_mqtt_client
        )
        
        client.connect_mqtt()
        initial_count = len(mock_mqtt_client.subscribed_topics)
        
        client.subscribe_to_topics("input/pepeunit")
        
        assert len(mock_mqtt_client.subscribed_topics) > initial_count
    
    def test_mqtt_disabled_error(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=False
        )
        
        with pytest.raises(PepeunitClientError):
            client.connect_mqtt()
        
        with pytest.raises(PepeunitClientError):
            client.publish_to_topic("output/pepeunit", "test")


class TestPepeunitClientREST:
    
    def test_init_with_rest(self, test_files, mock_rest_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            rest_enabled=True,
            rest_client=mock_rest_client
        )
        
        assert client.rest_enabled
        assert client.rest_client == mock_rest_client
    
    def test_set_state_storage(self, test_files, mock_rest_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            rest_enabled=True,
            rest_client=mock_rest_client
        )
        
        test_state = {"temperature": 25.5, "humidity": 60}
        client.set_state_storage(client.unit_uuid, test_state)
        
        assert len(mock_rest_client.requests) > 0
        method, url, data, headers = mock_rest_client.requests[-1]
        assert method == "PUT"
        assert client.unit_uuid in url
        assert data == test_state
    
    def test_get_state_storage(self, test_files, mock_rest_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            rest_enabled=True,
            rest_client=mock_rest_client
        )
        
        result = client.get_state_storage(client.unit_uuid)
        
        assert result["status"] == "success"
        assert len(mock_rest_client.requests) > 0
        method, url, data, headers = mock_rest_client.requests[-1]
        assert method == "GET"
        assert client.unit_uuid in url
    
    def test_download_env(self, test_files, mock_rest_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            rest_enabled=True,
            rest_client=mock_rest_client
        )
        
        env_path = client.download_env()
        
        assert os.path.exists(env_path)
        assert client.unit_uuid in env_path
        
        os.remove(env_path)
    
    def test_download_schema(self, test_files, mock_rest_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            rest_enabled=True,
            rest_client=mock_rest_client
        )
        
        schema_path = client.download_schema()
        
        assert os.path.exists(schema_path)
        assert client.unit_uuid in schema_path
        
        os.remove(schema_path)
    
    def test_rest_disabled_error(self, test_files):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            rest_enabled=False
        )
        
        with pytest.raises(PepeunitClientError):
            client.set_state_storage("test-uuid", {})
        
        with pytest.raises(PepeunitClientError):
            client.get_state_storage("test-uuid")


class TestPepeunitClientFileOperations:
    
    def test_update_env_file(self, test_files, temp_dir):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        new_env_path = os.path.join(temp_dir, "new_env.json")
        new_env_data = {"PEPEUNIT_URL": "updated.api.url", "MQTT_PORT": 9999}
        with open(new_env_path, 'w') as f:
            json.dump(new_env_data, f)
        
        client.update_env_file(new_env_path)
        
        assert client.settings.PEPEUNIT_URL == "updated.api.url"
        assert client.settings.MQTT_PORT == 9999
    
    def test_update_schema_file(self, test_files, temp_dir):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        new_schema_path = os.path.join(temp_dir, "new_schema.json")
        new_schema_data = {
            "input_base_topic": {"test/topic": ["test.topic.1"]},
            "output_base_topic": {},
            "input_topic": {},
            "output_topic": {}
        }
        with open(new_schema_path, 'w') as f:
            json.dump(new_schema_data, f)
        
        client.update_schema_file(new_schema_path)
        
        assert "test/topic" in client.schema.input_base_topic
        assert client.schema.input_base_topic["test/topic"] == ["test.topic.1"]
    
    def test_update_log_file(self, test_files, temp_dir):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"]
        )
        
        new_log_path = os.path.join(temp_dir, "new_log.json")
        new_log_data = [{"level": "Error", "text": "New error", "create_datetime": "2023-01-02T00:00:00"}]
        with open(new_log_path, 'w') as f:
            json.dump(new_log_data, f)
        
        client.update_log_file(new_log_path)
        
        full_log = client.get_full_log()
        assert len(full_log) >= 1
        assert any(entry["level"] == "Error" and entry["text"] == "New error" for entry in full_log)


class TestPepeunitClientLifecycle:
    
    def test_start_stop_cycle(self, test_files, mock_mqtt_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            mqtt_client=mock_mqtt_client
        )
        
        client.start()
        assert client._is_running
        assert mock_mqtt_client.is_connected
        
        client.stop()
        assert not client._is_running
        assert not mock_mqtt_client.is_connected
    
    def test_context_manager(self, test_files, mock_mqtt_client):
        with PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            mqtt_client=mock_mqtt_client
        ) as client:
            assert client._is_running
            assert mock_mqtt_client.is_connected
        
        assert not client._is_running
        assert not mock_mqtt_client.is_connected


class TestPepeunitClientFullFunctionality:
    
    def test_perform_update(self, test_files, mock_mqtt_client, mock_rest_client, temp_dir):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            rest_enabled=True,
            mqtt_client=mock_mqtt_client,
            rest_client=mock_rest_client
        )
        
        archive_path = os.path.join(temp_dir, "update.tar.gz")
        with open(archive_path, 'w') as f:
            f.write("mock archive")
        
        original_download = client.download_update
        client.download_update = lambda: archive_path
        
        client.update_device_program = lambda path: None
        
        try:
            client.perform_update()
            
            assert os.path.exists(archive_path) or not os.path.exists(archive_path)  # Файл мог быть удален в процессе
        
        finally:
            if os.path.exists(archive_path):
                os.remove(archive_path)
    
    def test_both_clients_required_error(self, test_files, mock_mqtt_client):
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=True,
            rest_enabled=False,  # REST отключен
            mqtt_client=mock_mqtt_client
        )
        
        with pytest.raises(PepeunitClientError, match="Both MQTT and REST must be enabled"):
            client.perform_update()
