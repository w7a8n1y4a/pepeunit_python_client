import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from pepeunit_client.mqtt_client import MQTTClient
from pepeunit_client.interfaces import MQTTClientInterface


class TestMQTTClient:
    
    def test_implements_interface(self):
        assert issubclass(MQTTClient, MQTTClientInterface)
    
    def test_init_with_defaults(self):
        client = MQTTClient(host="localhost")
        assert client.host == "localhost"
        assert client.port == 1883
        assert client.username is None
        assert client.password is None
        assert client.client_id is not None
        assert client.keepalive == 60
        assert not client.is_connected()
    
    def test_init_with_custom_params(self):
        client = MQTTClient(
            host="test.example.com",
            port=8883,
            username="user",
            password="pass",
            client_id="test-client",
            keepalive=120
        )
        assert client.host == "test.example.com"
        assert client.port == 8883
        assert client.username == "user"
        assert client.password == "pass"
        assert client.client_id == "test-client"
        assert client.keepalive == 120
    
    def test_connect_success(self):
        client = MQTTClient(host="localhost")
        
        with patch.object(client.client, 'connect', return_value=0) as mock_connect:
            with patch.object(client.client, 'loop_start') as mock_loop_start:
                result = client.connect()
                
                assert result is True
                assert client.is_connected()
                mock_connect.assert_called_once_with("localhost", 1883, 60)
                mock_loop_start.assert_called_once()
    
    def test_connect_failure(self):
        client = MQTTClient(host="localhost")
        
        with patch.object(client.client, 'connect', return_value=1) as mock_connect:
            result = client.connect()
            
            assert result is False
            assert not client.is_connected()
            assert client.get_connection_error() == "Connection failed with result 1"
    
    def test_connect_exception(self):
        client = MQTTClient(host="localhost")
        
        with patch.object(client.client, 'connect', side_effect=Exception("Connection error")):
            result = client.connect()
            
            assert result is False
            assert not client.is_connected()
            assert client.get_connection_error() == "Connection error"
    
    def test_disconnect(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'loop_stop') as mock_loop_stop:
            with patch.object(client.client, 'disconnect') as mock_disconnect:
                client.disconnect()
                
                assert not client.is_connected()
                mock_loop_stop.assert_called_once()
                mock_disconnect.assert_called_once()
    
    def test_publish_success(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        mock_result = Mock()
        mock_result.rc = 0
        
        with patch.object(client.client, 'publish', return_value=mock_result) as mock_publish:
            result = client.publish("test/topic", "test message")
            
            assert result is True
            mock_publish.assert_called_once_with("test/topic", "test message", 0, False)
    
    def test_publish_failure(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        mock_result = Mock()
        mock_result.rc = 1
        
        with patch.object(client.client, 'publish', return_value=mock_result) as mock_publish:
            result = client.publish("test/topic", "test message")
            
            assert result is False
    
    def test_publish_not_connected(self):
        client = MQTTClient(host="localhost")
        client._connected = False
        
        result = client.publish("test/topic", "test message")
        assert result is False
    
    def test_publish_exception(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'publish', side_effect=Exception("Publish error")):
            result = client.publish("test/topic", "test message")
            assert result is False
    
    def test_publish_json_success(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        mock_result = Mock()
        mock_result.rc = 0
        
        with patch.object(client, 'publish', return_value=True) as mock_publish:
            data = {"key": "value", "number": 123}
            result = client.publish_json("test/topic", data)
            
            assert result is True
            mock_publish.assert_called_once_with("test/topic", json.dumps(data), 0, False)
    
    def test_publish_json_invalid_data(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        # Test with non-serializable data
        class NonSerializable:
            pass
        
        result = client.publish_json("test/topic", {"obj": NonSerializable()})
        assert result is False
    
    def test_subscribe_success(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'subscribe', return_value=(0, 1)) as mock_subscribe:
            result = client.subscribe(["topic1", "topic2"])
            
            assert result is True
            mock_subscribe.assert_called_once_with([("topic1", 0), ("topic2", 0)])
    
    def test_subscribe_single_topic(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'subscribe', return_value=(0, 1)) as mock_subscribe:
            result = client.subscribe("single_topic")
            
            assert result is True
            mock_subscribe.assert_called_once_with([("single_topic", 0)])
    
    def test_subscribe_failure(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'subscribe', return_value=(1, 1)) as mock_subscribe:
            result = client.subscribe(["topic1"])
            assert result is False
    
    def test_subscribe_not_connected(self):
        client = MQTTClient(host="localhost")
        client._connected = False
        
        result = client.subscribe(["topic1"])
        assert result is False
    
    def test_subscribe_exception(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'subscribe', side_effect=Exception("Subscribe error")):
            result = client.subscribe(["topic1"])
            assert result is False
    
    def test_unsubscribe_success(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'unsubscribe', return_value=(0, 1)) as mock_unsubscribe:
            result = client.unsubscribe(["topic1", "topic2"])
            
            assert result is True
            mock_unsubscribe.assert_called_once_with(["topic1", "topic2"])
    
    def test_unsubscribe_single_topic(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'unsubscribe', return_value=(0, 1)) as mock_unsubscribe:
            result = client.unsubscribe("single_topic")
            
            assert result is True
            mock_unsubscribe.assert_called_once_with(["single_topic"])
    
    def test_unsubscribe_failure(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'unsubscribe', return_value=(1, 1)) as mock_unsubscribe:
            result = client.unsubscribe(["topic1"])
            assert result is False
    
    def test_unsubscribe_not_connected(self):
        client = MQTTClient(host="localhost")
        client._connected = False
        
        result = client.unsubscribe(["topic1"])
        assert result is False
    
    def test_unsubscribe_exception(self):
        client = MQTTClient(host="localhost")
        client._connected = True
        
        with patch.object(client.client, 'unsubscribe', side_effect=Exception("Unsubscribe error")):
            result = client.unsubscribe(["topic1"])
            assert result is False
    
    def test_get_client_info(self):
        client = MQTTClient(
            host="test.example.com",
            port=8883,
            username="user",
            password="pass",
            client_id="test-client"
        )
        
        info = client.get_client_info()
        
        assert info["client_id"] == "test-client"
        assert info["host"] == "test.example.com"
        assert info["port"] == 8883
        assert info["username"] == "user"
        assert info["connected"] is False
        assert info["connection_error"] is None
    
    def test_callback_wrappers(self):
        client = MQTTClient(host="localhost")
        
        # Test that callbacks are properly wrapped
        assert callable(client.client.on_connect)
        assert callable(client.client.on_disconnect)
        assert callable(client.client.on_message)
        assert callable(client.client.on_publish)
        assert callable(client.client.on_subscribe)
        assert callable(client.client.on_unsubscribe)
        assert callable(client.client.on_log)
    
    def test_custom_callbacks(self):
        on_connect_callback = Mock()
        on_message_callback = Mock()
        
        client = MQTTClient(
            host="localhost",
            on_connect=on_connect_callback,
            on_message=on_message_callback
        )
        
        # Simulate callbacks being called
        client.client.on_connect(None, None, None, 0)
        client.client.on_message(None, None, None)
        
        on_connect_callback.assert_called_once()
        on_message_callback.assert_called_once()
