"""
Тесты для абстрактных клиентов
"""
from abc import ABC
from unittest.mock import Mock

import pytest

from pepeunit_client.abstract_clients import AbstractPepeunitMqttClient, AbstractPepeunitRestClient


class TestAbstractPepeunitMqttClient:
    """Тесты для абстрактного MQTT клиента"""

    def test_is_abstract_class(self):
        """Тест что класс является абстрактным"""
        assert issubclass(AbstractPepeunitMqttClient, ABC)
        
        # Не можем создать экземпляр абстрактного класса
        with pytest.raises(TypeError):
            AbstractPepeunitMqttClient(Mock(), Mock(), Mock())

    def test_init_stores_dependencies(self):
        """Тест что инициализация сохраняет зависимости"""
        mock_settings = Mock()
        mock_schema = Mock()
        mock_logger = Mock()
        
        # Создаем конкретную реализацию для тестирования
        class ConcreteMqttClient(AbstractPepeunitMqttClient):
            def connect(self): pass
            def disconnect(self): pass
            def subscribe_topics(self, topics): pass
            def publish(self, topic, message): pass
            def set_input_handler(self, handler): pass
        
        client = ConcreteMqttClient(mock_settings, mock_schema, mock_logger)
        
        assert client.settings == mock_settings
        assert client.schema_manager == mock_schema
        assert client.logger == mock_logger

    def test_abstract_methods_exist(self):
        """Тест что все абстрактные методы определены"""
        abstract_methods = AbstractPepeunitMqttClient.__abstractmethods__
        
        expected_methods = {
            'connect', 'disconnect', 'subscribe_topics', 
            'publish', 'set_input_handler'
        }
        
        assert abstract_methods == expected_methods

    def test_concrete_implementation_works(self):
        """Тест что конкретная реализация работает корректно"""
        class TestMqttClient(AbstractPepeunitMqttClient):
            def __init__(self, settings, schema_manager, logger):
                super().__init__(settings, schema_manager, logger)
                self.connected = False
                self.subscribed_topics = []
                self.published_messages = []
                self.input_handler = None
            
            def connect(self):
                self.connected = True
            
            def disconnect(self):
                self.connected = False
            
            def subscribe_topics(self, topics):
                self.subscribed_topics.extend(topics)
            
            def publish(self, topic, message):
                self.published_messages.append((topic, message))
            
            def set_input_handler(self, handler):
                self.input_handler = handler
        
        mock_settings = Mock()
        mock_schema = Mock()
        mock_logger = Mock()
        
        client = TestMqttClient(mock_settings, mock_schema, mock_logger)
        
        # Тестируем методы
        client.connect()
        assert client.connected is True
        
        client.subscribe_topics(['topic1', 'topic2'])
        assert client.subscribed_topics == ['topic1', 'topic2']
        
        client.publish('test/topic', 'test message')
        assert client.published_messages == [('test/topic', 'test message')]
        
        test_handler = Mock()
        client.set_input_handler(test_handler)
        assert client.input_handler == test_handler
        
        client.disconnect()
        assert client.connected is False


class TestAbstractPepeunitRestClient:
    """Тесты для абстрактного REST клиента"""

    def test_is_abstract_class(self):
        """Тест что класс является абстрактным"""
        assert issubclass(AbstractPepeunitRestClient, ABC)
        
        # Не можем создать экземпляр абстрактного класса
        with pytest.raises(TypeError):
            AbstractPepeunitRestClient(Mock())

    def test_init_stores_settings(self):
        """Тест что инициализация сохраняет настройки"""
        mock_settings = Mock()
        
        # Создаем конкретную реализацию для тестирования
        class ConcreteRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): pass
            def download_env(self, unit_uuid, file_path): pass
            def download_schema(self, unit_uuid, file_path): pass
            def set_state_storage(self, unit_uuid, state): pass
            def get_state_storage(self, unit_uuid): pass
        
        client = ConcreteRestClient(mock_settings)
        
        assert client.settings == mock_settings

    def test_abstract_methods_exist(self):
        """Тест что все абстрактные методы определены"""
        abstract_methods = AbstractPepeunitRestClient.__abstractmethods__
        
        expected_methods = {
            'download_update', 'download_env', 'download_schema',
            'set_state_storage', 'get_state_storage'
        }
        
        assert abstract_methods == expected_methods

    def test_get_auth_headers_default(self):
        """Тест получения заголовков аутентификации по умолчанию"""
        class TestRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): pass
            def download_env(self, unit_uuid, file_path): pass
            def download_schema(self, unit_uuid, file_path): pass
            def set_state_storage(self, unit_uuid, state): pass
            def get_state_storage(self, unit_uuid): pass
        
        mock_settings = Mock()
        mock_settings.PEPEUNIT_TOKEN = 'test_token_123'
        
        client = TestRestClient(mock_settings)
        headers = client._get_auth_headers()
        
        expected_headers = {
            'accept': 'application/json',
            'x-auth-token': 'test_token_123'
        }
        
        assert headers == expected_headers

    def test_get_auth_headers_can_be_overridden(self):
        """Тест что метод получения заголовков можно переопределить"""
        class CustomRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): pass
            def download_env(self, unit_uuid, file_path): pass
            def download_schema(self, unit_uuid, file_path): pass
            def set_state_storage(self, unit_uuid, state): pass
            def get_state_storage(self, unit_uuid): pass
            
            def _get_auth_headers(self):
                return {
                    'authorization': f'Bearer {self.settings.PEPEUNIT_TOKEN}',
                    'content-type': 'application/json'
                }
        
        mock_settings = Mock()
        mock_settings.PEPEUNIT_TOKEN = 'custom_token'
        
        client = CustomRestClient(mock_settings)
        headers = client._get_auth_headers()
        
        expected_headers = {
            'authorization': 'Bearer custom_token',
            'content-type': 'application/json'
        }
        
        assert headers == expected_headers

    def test_get_base_url_default(self):
        """Тест получения базового URL по умолчанию"""
        class TestRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): pass
            def download_env(self, unit_uuid, file_path): pass
            def download_schema(self, unit_uuid, file_path): pass
            def set_state_storage(self, unit_uuid, state): pass
            def get_state_storage(self, unit_uuid): pass
        
        mock_settings = Mock()
        mock_settings.HTTP_TYPE = 'https'
        mock_settings.PEPEUNIT_URL = 'api.pepeunit.com'
        mock_settings.PEPEUNIT_APP_PREFIX = '/app'
        mock_settings.PEPEUNIT_API_ACTUAL_PREFIX = '/api/v1'
        
        client = TestRestClient(mock_settings)
        base_url = client._get_base_url()
        
        expected_url = 'https://api.pepeunit.com/app/api/v1'
        assert base_url == expected_url

    def test_get_base_url_can_be_overridden(self):
        """Тест что метод получения базового URL можно переопределить"""
        class CustomRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): pass
            def download_env(self, unit_uuid, file_path): pass
            def download_schema(self, unit_uuid, file_path): pass
            def set_state_storage(self, unit_uuid, state): pass
            def get_state_storage(self, unit_uuid): pass
            
            def _get_base_url(self):
                return f"custom://{self.settings.PEPEUNIT_URL}/v2"
        
        mock_settings = Mock()
        mock_settings.PEPEUNIT_URL = 'custom.api.com'
        
        client = CustomRestClient(mock_settings)
        base_url = client._get_base_url()
        
        assert base_url == 'custom://custom.api.com/v2'

    def test_concrete_implementation_works(self):
        """Тест что конкретная реализация работает корректно"""
        class TestRestClient(AbstractPepeunitRestClient):
            def __init__(self, settings):
                super().__init__(settings)
                self.operations = []
            
            def download_update(self, unit_uuid, file_path):
                self.operations.append(('download_update', unit_uuid, file_path))
            
            def download_env(self, unit_uuid, file_path):
                self.operations.append(('download_env', unit_uuid, file_path))
            
            def download_schema(self, unit_uuid, file_path):
                self.operations.append(('download_schema', unit_uuid, file_path))
            
            def set_state_storage(self, unit_uuid, state):
                self.operations.append(('set_state_storage', unit_uuid, state))
            
            def get_state_storage(self, unit_uuid):
                self.operations.append(('get_state_storage', unit_uuid))
                return {'retrieved': 'state'}
        
        mock_settings = Mock()
        client = TestRestClient(mock_settings)
        
        # Тестируем методы
        client.download_update('uuid1', '/path/to/update')
        client.download_env('uuid2', '/path/to/env')
        client.download_schema('uuid3', '/path/to/schema')
        client.set_state_storage('uuid4', {'state': 'data'})
        result = client.get_state_storage('uuid5')
        
        expected_operations = [
            ('download_update', 'uuid1', '/path/to/update'),
            ('download_env', 'uuid2', '/path/to/env'),
            ('download_schema', 'uuid3', '/path/to/schema'),
            ('set_state_storage', 'uuid4', {'state': 'data'}),
            ('get_state_storage', 'uuid5')
        ]
        
        assert client.operations == expected_operations
        assert result == {'retrieved': 'state'}

    def test_base_url_construction_variations(self):
        """Тест различных вариантов конструирования базового URL"""
        class TestRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): pass
            def download_env(self, unit_uuid, file_path): pass
            def download_schema(self, unit_uuid, file_path): pass
            def set_state_storage(self, unit_uuid, state): pass
            def get_state_storage(self, unit_uuid): pass
        
        test_cases = [
            # (HTTP_TYPE, URL, APP_PREFIX, API_PREFIX, expected)
            ('http', 'localhost', '', '/api', 'http://localhost/api'),
            ('https', 'api.example.com', '/v1', '/rest', 'https://api.example.com/v1/rest'),
            ('https', 'test.com', '/app', '', 'https://test.com/app'),
            ('http', '192.168.1.1:8080', '/service', '/v2', 'http://192.168.1.1:8080/service/v2'),
        ]
        
        for http_type, url, app_prefix, api_prefix, expected in test_cases:
            mock_settings = Mock()
            mock_settings.HTTP_TYPE = http_type
            mock_settings.PEPEUNIT_URL = url
            mock_settings.PEPEUNIT_APP_PREFIX = app_prefix
            mock_settings.PEPEUNIT_API_ACTUAL_PREFIX = api_prefix
            
            client = TestRestClient(mock_settings)
            result = client._get_base_url()
            
            assert result == expected, f"Failed for {http_type}://{url}{app_prefix}{api_prefix}"


class TestAbstractClientIntegration:
    """Интеграционные тесты абстрактных клиентов"""

    def test_both_clients_can_coexist(self):
        """Тест что оба клиента могут существовать одновременно"""
        class TestMqttClient(AbstractPepeunitMqttClient):
            def connect(self): return "mqtt_connected"
            def disconnect(self): return "mqtt_disconnected"
            def subscribe_topics(self, topics): return f"subscribed_to_{len(topics)}"
            def publish(self, topic, message): return f"published_{topic}"
            def set_input_handler(self, handler): return "handler_set"
        
        class TestRestClient(AbstractPepeunitRestClient):
            def download_update(self, unit_uuid, file_path): return "update_downloaded"
            def download_env(self, unit_uuid, file_path): return "env_downloaded"
            def download_schema(self, unit_uuid, file_path): return "schema_downloaded"
            def set_state_storage(self, unit_uuid, state): return "state_stored"
            def get_state_storage(self, unit_uuid): return {"state": "retrieved"}
        
        mock_settings = Mock()
        mock_schema = Mock()
        mock_logger = Mock()
        
        mqtt_client = TestMqttClient(mock_settings, mock_schema, mock_logger)
        rest_client = TestRestClient(mock_settings)
        
        # Тестируем что оба клиента работают независимо
        assert mqtt_client.connect() == "mqtt_connected"
        assert rest_client.download_update("uuid", "path") == "update_downloaded"
        
        # Проверяем что они имеют правильные зависимости
        assert mqtt_client.settings == mock_settings
        assert mqtt_client.schema_manager == mock_schema
        assert mqtt_client.logger == mock_logger
        assert rest_client.settings == mock_settings

    def test_clients_enforce_interface_contract(self):
        """Тест что клиенты обеспечивают соблюдение интерфейса"""
        # Неполная реализация MQTT клиента должна вызывать ошибку
        with pytest.raises(TypeError):
            class IncompleteMqttClient(AbstractPepeunitMqttClient):
                def connect(self): pass
                # Отсутствуют остальные методы
            
            IncompleteMqttClient(Mock(), Mock(), Mock())
        
        # Неполная реализация REST клиента должна вызывать ошибку
        with pytest.raises(TypeError):
            class IncompleteRestClient(AbstractPepeunitRestClient):
                def download_update(self, unit_uuid, file_path): pass
                # Отсутствуют остальные методы
            
            IncompleteRestClient(Mock())
