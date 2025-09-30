"""
Тесты для класса PepeunitMqttClient
"""
from unittest.mock import Mock, patch, MagicMock

import pytest

from pepeunit_client.pepeunit_mqtt_client import PepeunitMqttClient
from pepeunit_client.abstract_clients import AbstractPepeunitMqttClient


class TestPepeunitMqttClient:
    """Тесты для класса PepeunitMqttClient"""

    def test_inheritance(self):
        """Тест что класс наследуется от абстрактного клиента"""
        assert issubclass(PepeunitMqttClient, AbstractPepeunitMqttClient)

    def test_init(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест инициализации"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        assert client.settings == mock_settings
        assert client.schema_manager == mock_schema_manager
        assert client.logger == mock_logger
        assert client._client is None
        assert client._input_handler is None

    @patch('pepeunit_client.pepeunit_mqtt_client.mqtt_client_paho')
    @patch('pepeunit_client.pepeunit_mqtt_client.uuid')
    def test_get_paho_client_success(self, mock_uuid, mock_mqtt_paho, mock_settings, mock_schema_manager, mock_logger):
        """Тест успешного создания paho MQTT клиента"""
        mock_uuid.uuid4.return_value = 'test-uuid-123'
        mock_client = Mock()
        mock_mqtt_paho.Client.return_value = mock_client
        mock_mqtt_paho.CallbackAPIVersion.VERSION1 = 'VERSION1'
        
        mock_settings.PEPEUNIT_TOKEN = 'test_token'
        
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        result = client._get_paho_client()
        
        assert result == mock_client
        mock_mqtt_paho.Client.assert_called_once_with('VERSION1', 'test-uuid-123')
        mock_client.username_pw_set.assert_called_once_with('test_token', '')
        assert mock_client.on_connect == client._on_connect
        assert mock_client.on_message == client._on_message

    def test_get_paho_client_import_error(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест исключения при отсутствии paho-mqtt"""
        with patch('pepeunit_client.pepeunit_mqtt_client.mqtt_client_paho', None):
            client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
            
            with pytest.raises(ImportError, match="paho-mqtt is required for MQTT functionality"):
                client._get_paho_client()

    def test_connect_creates_client(self, mock_settings, mock_schema_manager, mock_logger, mock_paho_mqtt):
        """Тест подключения создает клиента"""
        mock_settings.MQTT_URL = 'test.mqtt.com'
        mock_settings.MQTT_PORT = 1883
        
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        with patch.object(client, '_get_paho_client', return_value=mock_paho_mqtt) as mock_get_client:
            client.connect()
            
            mock_get_client.assert_called_once()
            assert client._client == mock_paho_mqtt
            mock_paho_mqtt.connect.assert_called_once_with('test.mqtt.com', 1883)
            mock_paho_mqtt.loop_start.assert_called_once()

    def test_connect_reuses_existing_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест что подключение переиспользует существующий клиент"""
        existing_client = Mock()
        
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = existing_client
        
        mock_settings.MQTT_URL = 'test.mqtt.com'
        mock_settings.MQTT_PORT = 1883
        
        with patch.object(client, '_get_paho_client') as mock_get_client:
            client.connect()
            
            mock_get_client.assert_not_called()
            assert client._client == existing_client
            existing_client.connect.assert_called_once_with('test.mqtt.com', 1883)

    def test_disconnect_with_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест отключения с активным клиентом"""
        mock_client = Mock()
        
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = mock_client
        
        client.disconnect()
        
        mock_client.loop_stop.assert_called_once()
        mock_client.disconnect.assert_called_once()

    def test_disconnect_without_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест отключения без активного клиента"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = None
        
        # Не должно вызывать исключение
        client.disconnect()

    def test_on_connect_success(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест успешного callback подключения"""
        mock_logger.info = Mock()
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        client._on_connect(None, None, None, 0)  # rc=0 означает успех
        
        mock_logger.info.assert_called_once_with("Connected to MQTT Broker!")

    def test_on_connect_failure(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест неуспешного callback подключения"""
        mock_logger.critical = Mock()
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        client._on_connect(None, None, None, 1)  # rc=1 означает ошибку
        
        mock_logger.critical.assert_called_once_with("Failed to connect to MQTT, return code 1")

    def test_on_message_with_handler(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест обработки сообщения с установленным обработчиком"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        mock_handler = Mock()
        client._input_handler = mock_handler
        
        mock_msg = Mock()
        mock_msg.topic = 'test/topic'
        mock_msg.payload = b'test message'
        
        client._on_message(None, None, mock_msg)
        
        mock_handler.assert_called_once_with(mock_msg)

    def test_on_message_without_handler(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест обработки сообщения без обработчика"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._input_handler = None
        
        mock_msg = Mock()
        
        # Не должно вызывать исключение
        client._on_message(None, None, mock_msg)

    def test_on_message_handler_exception(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест обработки исключения в обработчике сообщений"""
        mock_logger.error = Mock()
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        mock_handler = Mock()
        mock_handler.side_effect = Exception("Handler error")
        client._input_handler = mock_handler
        
        mock_msg = Mock()
        
        client._on_message(None, None, mock_msg)
        
        mock_logger.error.assert_called_once_with("Error processing MQTT message: Handler error")

    def test_set_input_handler(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест установки обработчика входящих сообщений"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        mock_handler = Mock()
        client.set_input_handler(mock_handler)
        
        assert client._input_handler == mock_handler

    def test_subscribe_topics_with_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест подписки на топики с активным клиентом"""
        mock_client = Mock()
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = mock_client
        
        topics = ['topic1', 'topic2', 'topic3']
        client.subscribe_topics(topics)
        
        expected_calls = [((topic,), {}) for topic in topics]
        assert mock_client.subscribe.call_args_list == expected_calls

    def test_subscribe_topics_without_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест подписки на топики без активного клиента"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = None
        
        topics = ['topic1', 'topic2']
        
        # Не должно вызывать исключение
        client.subscribe_topics(topics)

    def test_publish_with_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест публикации сообщения с активным клиентом"""
        mock_client = Mock()
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = mock_client
        
        client.publish('test/topic', 'test message')
        
        mock_client.publish.assert_called_once_with('test/topic', 'test message')

    def test_publish_without_client(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест публикации сообщения без активного клиента"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        client._client = None
        
        # Не должно вызывать исключение
        client.publish('test/topic', 'test message')

    def test_integration_full_workflow(self, mock_settings, mock_schema_manager, mock_logger, mock_paho_mqtt):
        """Интеграционный тест полного рабочего процесса"""
        mock_settings.MQTT_URL = 'test.broker.com'
        mock_settings.MQTT_PORT = 8883
        mock_settings.PEPEUNIT_TOKEN = 'integration_token'
        
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        # Устанавливаем обработчик
        mock_handler = Mock()
        client.set_input_handler(mock_handler)
        
        with patch.object(client, '_get_paho_client', return_value=mock_paho_mqtt):
            # Подключаемся
            client.connect()
            
            # Подписываемся на топики
            topics = ['integration/topic1', 'integration/topic2']
            client.subscribe_topics(topics)
            
            # Публикуем сообщение
            client.publish('integration/output', 'integration message')
            
            # Симулируем входящее сообщение
            mock_msg = Mock()
            mock_msg.topic = 'integration/topic1'
            mock_msg.payload = b'incoming message'
            client._on_message(None, None, mock_msg)
            
            # Отключаемся
            client.disconnect()
        
        # Проверяем что все операции выполнились
        mock_paho_mqtt.connect.assert_called_once_with('test.broker.com', 8883)
        mock_paho_mqtt.loop_start.assert_called_once()
        
        assert mock_paho_mqtt.subscribe.call_count == 2
        mock_paho_mqtt.subscribe.assert_any_call('integration/topic1')
        mock_paho_mqtt.subscribe.assert_any_call('integration/topic2')
        
        mock_paho_mqtt.publish.assert_called_once_with('integration/output', 'integration message')
        mock_handler.assert_called_once_with(mock_msg)
        
        mock_paho_mqtt.loop_stop.assert_called_once()
        mock_paho_mqtt.disconnect.assert_called_once()

    def test_connection_callback_integration(self, mock_settings, mock_schema_manager, mock_logger):
        """Интеграционный тест callback'ов подключения"""
        # Мокируем методы логгера
        mock_logger.info = Mock()
        mock_logger.critical = Mock()
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        # Тестируем различные коды результата
        test_cases = [
            (0, "Connected to MQTT Broker!", "info"),
            (1, "Failed to connect to MQTT, return code 1", "critical"),
            (2, "Failed to connect to MQTT, return code 2", "critical"),
            (5, "Failed to connect to MQTT, return code 5", "critical"),
        ]
        
        for rc, expected_message, expected_level in test_cases:
            mock_logger.info.reset_mock()
            mock_logger.critical.reset_mock()
            
            client._on_connect(None, None, None, rc)
            
            if expected_level == "info":
                mock_logger.info.assert_called_once_with(expected_message)
                mock_logger.critical.assert_not_called()
            else:
                mock_logger.critical.assert_called_once_with(expected_message)
                mock_logger.info.assert_not_called()

    def test_message_handling_different_payloads(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест обработки сообщений с различными payload"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        messages_received = []
        
        def test_handler(msg):
            messages_received.append((msg.topic, msg.payload))
        
        client.set_input_handler(test_handler)
        
        # Тестируем различные типы payload
        test_messages = [
            ('test/topic1', b'simple text'),
            ('test/topic2', b'{"json": "data"}'),
            ('test/topic3', b''),  # Пустое сообщение
            ('test/topic4', b'\x00\x01\x02'),  # Бинарные данные
        ]
        
        for topic, payload in test_messages:
            mock_msg = Mock()
            mock_msg.topic = topic
            mock_msg.payload = payload
            
            client._on_message(None, None, mock_msg)
        
        # Проверяем что все сообщения обработались
        assert len(messages_received) == 4
        for i, (topic, payload) in enumerate(test_messages):
            assert messages_received[i] == (topic, payload)

    def test_multiple_handlers_override(self, mock_settings, mock_schema_manager, mock_logger):
        """Тест что новый обработчик перезаписывает старый"""
        client = PepeunitMqttClient(mock_settings, mock_schema_manager, mock_logger)
        
        handler1 = Mock()
        handler2 = Mock()
        
        # Устанавливаем первый обработчик
        client.set_input_handler(handler1)
        assert client._input_handler == handler1
        
        # Устанавливаем второй обработчик
        client.set_input_handler(handler2)
        assert client._input_handler == handler2
        
        # Проверяем что используется только второй обработчик
        mock_msg = Mock()
        client._on_message(None, None, mock_msg)
        
        handler1.assert_not_called()
        handler2.assert_called_once_with(mock_msg)
