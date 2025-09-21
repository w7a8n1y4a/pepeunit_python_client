"""
Тесты MQTT клиента
"""

import pytest
from unittest.mock import Mock, patch

from pepeunit_client.mqtt_client import MQTTClient, DummyMQTTClient
from pepeunit_client.exceptions import PepeunitClientError


class TestMQTTClient:
    """Тесты реального MQTT клиента"""
    
    @patch('pepeunit_client.mqtt_client.MQTT_AVAILABLE', False)
    def test_mqtt_not_available(self):
        """Тест ошибки когда paho-mqtt не установлен"""
        with pytest.raises(PepeunitClientError, match="paho-mqtt is not installed"):
            MQTTClient("localhost", 1883, "user", "pass")
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_client_initialization(self, mock_mqtt):
        """Тест инициализации MQTT клиента"""
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        
        assert client.host == "test.host"
        assert client.port == 1883
        assert client.username == "test_user"
        assert client.password == "test_pass"
        assert not client.is_connected
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_connect(self, mock_mqtt):
        """Тест подключения MQTT"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        # Проверяем вызовы
        mock_mqtt.Client.assert_called_once()
        mock_client_instance.username_pw_set.assert_called_with("test_user", "test_pass")
        mock_client_instance.connect.assert_called_with("test.host", 1883)
        assert client.is_connected
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_disconnect(self, mock_mqtt):
        """Тест отключения MQTT"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        client.disconnect()
        
        mock_client_instance.disconnect.assert_called_once()
        assert not client.is_connected
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_subscribe(self, mock_mqtt):
        """Тест подписки на топики"""
        mock_client_instance = Mock()
        mock_client_instance.subscribe.return_value = (0, 1)  # MQTT_ERR_SUCCESS, message_id
        mock_mqtt.Client.return_value = mock_client_instance
        mock_mqtt.MQTT_ERR_SUCCESS = 0
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        test_topics = ["topic1", "topic2"]
        client.subscribe(test_topics)
        
        # Проверяем, что подписка была сделана для каждого топика
        assert mock_client_instance.subscribe.call_count == 2
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_publish(self, mock_mqtt):
        """Тест публикации сообщений"""
        mock_client_instance = Mock()
        mock_result = Mock()
        mock_result.rc = 0  # MQTT_ERR_SUCCESS
        mock_client_instance.publish.return_value = mock_result
        mock_mqtt.Client.return_value = mock_client_instance
        mock_mqtt.MQTT_ERR_SUCCESS = 0
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        result = client.publish("test/topic", "test message")
        
        mock_client_instance.publish.assert_called_with("test/topic", "test message")
        assert result is True
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_message_handler(self, mock_mqtt):
        """Тест установки обработчика сообщений"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        
        def test_handler(client, userdata, msg):
            pass
        
        client.set_message_handler(test_handler)
        assert client.message_handler == test_handler
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_mqtt_loop_control(self, mock_mqtt):
        """Тест управления циклом обработки сообщений"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        client.start_loop()
        mock_client_instance.loop_start.assert_called_once()
        
        client.stop_loop()
        mock_client_instance.loop_stop.assert_called_once()
    
    def test_mqtt_not_connected_errors(self):
        """Тест ошибок при отсутствии подключения"""
        client = DummyMQTTClient()  # Используем dummy клиент
        
        with pytest.raises(PepeunitClientError):
            client.connect()
        
        with pytest.raises(PepeunitClientError):
            client.subscribe(["topic1"])
        
        with pytest.raises(PepeunitClientError):
            client.publish("topic1", "message")


class TestDummyMQTTClient:
    """Тесты заглушки MQTT клиента"""
    
    def test_dummy_client_initialization(self):
        """Тест инициализации dummy клиента"""
        client = DummyMQTTClient()
        
        assert not client.is_connected
        assert client.message_handler is None
    
    def test_dummy_client_methods_raise_errors(self):
        """Тест что методы dummy клиента вызывают ошибки"""
        client = DummyMQTTClient()
        
        with pytest.raises(PepeunitClientError, match="MQTT client is not available"):
            client.connect()
        
        with pytest.raises(PepeunitClientError, match="MQTT client is not available"):
            client.subscribe(["topic"])
        
        with pytest.raises(PepeunitClientError, match="MQTT client is not available"):
            client.unsubscribe(["topic"])
        
        with pytest.raises(PepeunitClientError, match="MQTT client is not available"):
            client.publish("topic", "message")
    
    def test_dummy_client_safe_methods(self):
        """Тест безопасных методов dummy клиента"""
        client = DummyMQTTClient()
        
        # Эти методы не должны вызывать ошибки
        client.disconnect()
        client.start_loop()
        client.stop_loop()
        
        def test_handler(client, userdata, msg):
            pass
        
        client.set_message_handler(test_handler)
        assert client.message_handler == test_handler


class TestMQTTCallbacks:
    """Тесты callback функций MQTT"""
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_on_connect_callback(self, mock_mqtt):
        """Тест callback при подключении"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        # Симулируем успешное подключение
        client._on_connect(None, None, None, 0)
        assert client.is_connected
        
        # Симулируем неуспешное подключение
        with pytest.raises(PepeunitClientError):
            client._on_connect(None, None, None, 1)
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_on_disconnect_callback(self, mock_mqtt):
        """Тест callback при отключении"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        client.is_connected = True
        
        # Симулируем отключение
        client._on_disconnect(None, None, 0)
        assert not client.is_connected
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_on_message_callback(self, mock_mqtt):
        """Тест callback при получении сообщения"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        
        # Устанавливаем обработчик сообщений
        handler_called = False
        
        def test_handler(client, userdata, msg):
            nonlocal handler_called
            handler_called = True
        
        client.set_message_handler(test_handler)
        
        # Симулируем получение сообщения
        mock_msg = Mock()
        client._on_message(None, None, mock_msg)
        
        assert handler_called
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_on_message_callback_error_handling(self, mock_mqtt):
        """Тест обработки ошибок в callback сообщений"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        
        # Устанавливаем обработчик который вызывает ошибку
        def error_handler(client, userdata, msg):
            raise Exception("Test error")
        
        client.set_message_handler(error_handler)
        
        # Симулируем получение сообщения - не должно вызывать исключение
        mock_msg = Mock()
        client._on_message(None, None, mock_msg)
        # Тест проходит если исключение не было вызвано


class TestMQTTClientEdgeCases:
    """Тесты граничных случаев MQTT клиента"""
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_subscribe_without_connection(self, mock_mqtt):
        """Тест подписки без подключения"""
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        
        with pytest.raises(PepeunitClientError, match="MQTT client is not connected"):
            client.subscribe(["topic1"])
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_publish_without_connection(self, mock_mqtt):
        """Тест публикации без подключения"""
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        
        with pytest.raises(PepeunitClientError, match="MQTT client is not connected"):
            client.publish("topic1", "message")
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_subscribe_failure(self, mock_mqtt):
        """Тест неуспешной подписки"""
        mock_client_instance = Mock()
        mock_client_instance.subscribe.return_value = (1, 1)  # Ошибка подписки
        mock_mqtt.Client.return_value = mock_client_instance
        mock_mqtt.MQTT_ERR_SUCCESS = 0
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        with pytest.raises(PepeunitClientError, match="Failed to subscribe"):
            client.subscribe(["topic1"])
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_publish_failure(self, mock_mqtt):
        """Тест неуспешной публикации"""
        mock_client_instance = Mock()
        mock_result = Mock()
        mock_result.rc = 1  # Ошибка публикации
        mock_client_instance.publish.return_value = mock_result
        mock_mqtt.Client.return_value = mock_client_instance
        mock_mqtt.MQTT_ERR_SUCCESS = 0
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        result = client.publish("test/topic", "test message")
        assert result is False
    
    @patch('pepeunit_client.mqtt_client.mqtt')
    def test_empty_topic_list(self, mock_mqtt):
        """Тест пустого списка топиков"""
        mock_client_instance = Mock()
        mock_mqtt.Client.return_value = mock_client_instance
        
        client = MQTTClient("test.host", 1883, "test_user", "test_pass")
        client.connect()
        
        # Подписка на пустой список не должна вызывать ошибок
        client.subscribe([])
        client.unsubscribe([])
        
        # Методы не должны были вызываться
        mock_client_instance.subscribe.assert_not_called()
        mock_client_instance.unsubscribe.assert_not_called()
