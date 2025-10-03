"""
Тесты для класса PepeunitRestClient
"""
import json
import os
from unittest.mock import Mock, patch, mock_open

import pytest

from pepeunit_client.pepeunit_rest_client import PepeunitRestClient
from pepeunit_client.abstract_clients import AbstractPepeunitRestClient


class TestPepeunitRestClient:
    """Тесты для класса PepeunitRestClient"""

    def test_inheritance(self):
        """Тест что класс наследуется от абстрактного клиента"""
        assert issubclass(PepeunitRestClient, AbstractPepeunitRestClient)

    def test_init(self, mock_settings):
        """Тест инициализации"""
        with patch.object(PepeunitRestClient, '_get_httpx_client') as mock_get_httpx:
            mock_httpx = Mock()
            mock_get_httpx.return_value = mock_httpx
            
            client = PepeunitRestClient(mock_settings)
            
            assert client.settings == mock_settings
            assert client._httpx_client == mock_httpx
            mock_get_httpx.assert_called_once()

    def test_get_httpx_client_success(self, mock_settings):
        """Тест успешного получения httpx клиента"""
        with patch('pepeunit_client.pepeunit_rest_client.httpx') as mock_httpx_module:
            client = PepeunitRestClient(mock_settings)
            result = client._get_httpx_client()
            
            assert result == mock_httpx_module

    def test_get_httpx_client_import_error(self, mock_settings):
        """Тест исключения при отсутствии httpx"""
        with patch('pepeunit_client.pepeunit_rest_client.httpx', None):
            with pytest.raises(ImportError, match="httpx is required for REST functionality"):
                PepeunitRestClient(mock_settings)

    def test_download_update_success(self, mock_settings, mock_httpx, temp_dir):
        """Тест успешного скачивания обновления"""
        # Настройка мока настроек
        mock_settings.PEPEUNIT_TOKEN = 'test_token'
        
        # Настройка базового URL
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            # Настройка ответа
            mock_response = Mock()
            mock_response.content = b'test archive content'
            mock_httpx.get.return_value = mock_response
            
            file_path = f"{temp_dir}/update.tar.gz"
            unit_uuid = 'test-uuid-123'
            
            client.download_update(unit_uuid, file_path)
            
            # Проверяем вызов API
            expected_url = 'https://api.test.com/units/firmware/tgz/test-uuid-123?wbits=9&level=9'
            expected_headers = {
                'accept': 'application/json',
                'x-auth-token': 'test_token'
            }
            mock_httpx.get.assert_called_once_with(expected_url, headers=expected_headers)
            mock_response.raise_for_status.assert_called_once()
            
            # Проверяем что файл записан
            with open(file_path, 'rb') as f:
                content = f.read()
            assert content == b'test archive content'

    def test_download_update_http_error(self, mock_settings, mock_httpx):
        """Тест обработки HTTP ошибки при скачивании обновления"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 404")
            mock_httpx.get.return_value = mock_response
            
            with pytest.raises(Exception, match="HTTP 404"):
                client.download_update('uuid', '/path/to/file')

    @patch('pepeunit_client.file_manager.FileManager.write_json')
    def test_download_env_success(self, mock_write_json, mock_settings, mock_httpx):
        """Тест успешного скачивания env файла"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            env_data = {'PEPEUNIT_URL': 'test.com', 'MQTT_PORT': 1883}
            mock_response = Mock()
            mock_response.json.return_value = env_data
            mock_httpx.get.return_value = mock_response
            
            unit_uuid = 'env-test-uuid'
            file_path = '/path/to/env.json'
            
            client.download_env(unit_uuid, file_path)
            
            expected_url = 'https://api.test.com/units/env/env-test-uuid'
            mock_httpx.get.assert_called_once()
            args, kwargs = mock_httpx.get.call_args
            assert args[0] == expected_url
            
            mock_response.raise_for_status.assert_called_once()
            mock_write_json.assert_called_once_with(file_path, env_data)

    @patch('pepeunit_client.file_manager.FileManager.write_json')
    def test_download_env_string_response(self, mock_write_json, mock_settings, mock_httpx):
        """Тест скачивания env файла когда ответ - строка JSON"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            env_data = {'PEPEUNIT_URL': 'string.test.com'}
            env_string = json.dumps(env_data)
            
            mock_response = Mock()
            mock_response.json.return_value = env_string
            mock_httpx.get.return_value = mock_response
            
            client.download_env('uuid', '/path/to/env.json')
            
            mock_write_json.assert_called_once_with('/path/to/env.json', env_data)

    @patch('pepeunit_client.file_manager.FileManager.write_json')
    def test_download_schema_success(self, mock_write_json, mock_settings, mock_httpx):
        """Тест успешного скачивания схемы"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            schema_data = {
                'input_base_topic': {'test': ['topic1']},
                'output_base_topic': {'test': ['topic2']}
            }
            mock_response = Mock()
            mock_response.json.return_value = schema_data
            mock_httpx.get.return_value = mock_response
            
            unit_uuid = 'schema-test-uuid'
            file_path = '/path/to/schema.json'
            
            client.download_schema(unit_uuid, file_path)
            
            expected_url = 'https://api.test.com/units/get_current_schema/schema-test-uuid'
            mock_httpx.get.assert_called_once()
            args, kwargs = mock_httpx.get.call_args
            assert args[0] == expected_url
            
            mock_response.raise_for_status.assert_called_once()
            mock_write_json.assert_called_once_with(file_path, schema_data)

    @patch('pepeunit_client.file_manager.FileManager.write_json')
    def test_download_schema_string_response(self, mock_write_json, mock_settings, mock_httpx):
        """Тест скачивания схемы когда ответ - строка JSON"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            schema_data = {'input_topic': {'test': ['topic']}}
            schema_string = json.dumps(schema_data)
            
            mock_response = Mock()
            mock_response.json.return_value = schema_string
            mock_httpx.get.return_value = mock_response
            
            client.download_schema('uuid', '/path/to/schema.json')
            
            mock_write_json.assert_called_once_with('/path/to/schema.json', schema_data)

    def test_set_state_storage_success(self, mock_settings, mock_httpx):
        """Тест успешной установки состояния в хранилище"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            mock_response = Mock()
            mock_httpx.put.return_value = mock_response
            
            unit_uuid = 'state-test-uuid'
            state_data = {'sensor1': 25.5, 'sensor2': 'active'}
            
            client.set_state_storage(unit_uuid, state_data)
            
            expected_url = 'https://api.test.com/unit/state-test-uuid'
            expected_headers = {
                'accept': 'application/json',
                'x-auth-token': mock_settings.PEPEUNIT_TOKEN,
                'content-type': 'application/json'
            }
            
            mock_httpx.put.assert_called_once_with(
                expected_url, 
                headers=expected_headers, 
                json=state_data
            )
            mock_response.raise_for_status.assert_called_once()

    def test_get_state_storage_success(self, mock_settings, mock_httpx):
        """Тест успешного получения состояния из хранилища"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://api.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            expected_state = {'temperature': 22.1, 'humidity': 65}
            mock_response = Mock()
            mock_response.json.return_value = expected_state
            mock_httpx.get.return_value = mock_response
            
            unit_uuid = 'get-state-uuid'
            result = client.get_state_storage(unit_uuid)
            
            expected_url = 'https://api.test.com/unit/get-state-uuid'
            expected_headers = {
                'accept': 'application/json',
                'x-auth-token': mock_settings.PEPEUNIT_TOKEN
            }
            
            mock_httpx.get.assert_called_once_with(expected_url, headers=expected_headers)
            mock_response.raise_for_status.assert_called_once()
            assert result == expected_state

    def test_download_file_from_url_success(self, mock_settings, mock_httpx, temp_dir):
        """Тест успешного скачивания файла по URL"""
        client = PepeunitRestClient(mock_settings)
        client._httpx_client = mock_httpx
        
        # Настройка ответа
        mock_response = Mock()
        mock_response.content = b'test file content from url'
        mock_httpx.get.return_value = mock_response
        
        url = 'https://external.example.com/file.txt'
        file_path = f"{temp_dir}/downloaded_file.txt"
        
        client.download_file_from_url(url, file_path)
        
        # Проверяем вызов API
        mock_httpx.get.assert_called_once_with(url)
        mock_response.raise_for_status.assert_called_once()
        
        # Проверяем что файл записан
        with open(file_path, 'rb') as f:
            content = f.read()
        assert content == b'test file content from url'

    def test_download_file_from_url_http_error(self, mock_settings, mock_httpx):
        """Тест обработки HTTP ошибки при скачивании файла по URL"""
        client = PepeunitRestClient(mock_settings)
        client._httpx_client = mock_httpx
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 403")
        mock_httpx.get.return_value = mock_response
        
        with pytest.raises(Exception, match="HTTP 403"):
            client.download_file_from_url('https://example.com/file', '/path/to/file')

    def test_inherited_auth_headers_method(self, mock_settings):
        """Тест использования унаследованного метода получения заголовков"""
        mock_settings.PEPEUNIT_TOKEN = 'inherited_token'
        
        with patch.object(PepeunitRestClient, '_get_httpx_client'):
            client = PepeunitRestClient(mock_settings)
            headers = client._get_auth_headers()
            
            expected_headers = {
                'accept': 'application/json',
                'x-auth-token': 'inherited_token'
            }
            assert headers == expected_headers

    def test_inherited_base_url_method(self, mock_settings):
        """Тест использования унаследованного метода получения базового URL"""
        mock_settings.HTTP_TYPE = 'http'
        mock_settings.PEPEUNIT_URL = 'localhost:8000'
        mock_settings.PEPEUNIT_APP_PREFIX = '/myapp'
        mock_settings.PEPEUNIT_API_ACTUAL_PREFIX = '/api/v2'
        
        with patch.object(PepeunitRestClient, '_get_httpx_client'):
            client = PepeunitRestClient(mock_settings)
            base_url = client._get_base_url()
            
            expected_url = 'http://localhost:8000/myapp/api/v2'
            assert base_url == expected_url

    def test_integration_full_workflow(self, mock_settings, mock_httpx, temp_dir):
        """Интеграционный тест полного рабочего процесса REST клиента"""
        # Настройка
        mock_settings.HTTP_TYPE = 'https'
        mock_settings.PEPEUNIT_URL = 'integration.api.com'
        mock_settings.PEPEUNIT_APP_PREFIX = '/app'
        mock_settings.PEPEUNIT_API_ACTUAL_PREFIX = '/api/v1'
        mock_settings.PEPEUNIT_TOKEN = 'integration_token'
        
        client = PepeunitRestClient(mock_settings)
        client._httpx_client = mock_httpx
        
        unit_uuid = 'integration-uuid-123'
        
        # 1. Скачиваем обновление
        update_response = Mock()
        update_response.content = b'integration update content'
        
        # 2. Скачиваем env
        env_data = {'INTEGRATION_TEST': 'true', 'PORT': 9999}
        env_response = Mock()
        env_response.json.return_value = env_data
        
        # 3. Скачиваем схему
        schema_data = {'integration_topic': {'test': ['integration/topic']}}
        schema_response = Mock()
        schema_response.json.return_value = schema_data
        
        # 4. Устанавливаем состояние
        state_response = Mock()
        
        # 5. Скачиваем файл по URL
        file_response = Mock()
        file_response.content = b'external file content'
        
        # 6. Получаем состояние
        get_state_data = {'integration_state': 'active'}
        get_state_response = Mock()
        get_state_response.json.return_value = get_state_data
        
        # Настройка ответов mock_httpx
        mock_httpx.get.side_effect = [update_response, env_response, schema_response, file_response, get_state_response]
        mock_httpx.put.return_value = state_response
        
        # Выполняем операции
        update_file = f"{temp_dir}/integration_update.tar.gz"
        env_file = f"{temp_dir}/integration_env.json"
        schema_file = f"{temp_dir}/integration_schema.json"
        external_file = f"{temp_dir}/external_file.txt"
        
        with patch('pepeunit_client.file_manager.FileManager.write_json') as mock_write_json:
            # 1. Скачиваем обновление
            client.download_update(unit_uuid, update_file)
            
            # 2. Скачиваем env
            client.download_env(unit_uuid, env_file)
            
            # 3. Скачиваем схему
            client.download_schema(unit_uuid, schema_file)
            
            # 4. Скачиваем файл по URL
            client.download_file_from_url('https://external.example.com/file.txt', external_file)
            
            # 5. Устанавливаем состояние
            test_state = {'sensor': 42}
            client.set_state_storage(unit_uuid, test_state)
            
            # 6. Получаем состояние
            retrieved_state = client.get_state_storage(unit_uuid)
        
        # Проверяем результаты
        assert retrieved_state == get_state_data
        
        # Проверяем что файл обновления записан
        with open(update_file, 'rb') as f:
            assert f.read() == b'integration update content'
        
        # Проверяем что внешний файл записан
        with open(external_file, 'rb') as f:
            assert f.read() == b'external file content'
        
        # Проверяем вызовы записи JSON
        assert mock_write_json.call_count == 2
        mock_write_json.assert_any_call(env_file, env_data)
        mock_write_json.assert_any_call(schema_file, schema_data)
        
        # Проверяем HTTP вызовы
        assert mock_httpx.get.call_count == 5
        assert mock_httpx.put.call_count == 1

    def test_error_handling_in_all_methods(self, mock_settings, mock_httpx):
        """Тест обработки ошибок во всех методах"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://error.test.com'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            # Настраиваем mock для генерации ошибок
            error_response = Mock()
            error_response.raise_for_status.side_effect = Exception("HTTP Error")
            mock_httpx.get.return_value = error_response
            mock_httpx.put.return_value = error_response
            
            test_uuid = 'error-test-uuid'
            
            # Проверяем что все методы правильно передают исключения
            with pytest.raises(Exception, match="HTTP Error"):
                client.download_update(test_uuid, '/path')
            
            with pytest.raises(Exception, match="HTTP Error"):
                client.download_env(test_uuid, '/path')
            
            with pytest.raises(Exception, match="HTTP Error"):
                client.download_schema(test_uuid, '/path')
            
            with pytest.raises(Exception, match="HTTP Error"):
                client.set_state_storage(test_uuid, {})
            
            with pytest.raises(Exception, match="HTTP Error"):
                client.get_state_storage(test_uuid)

    def test_url_construction_with_parameters(self, mock_settings, mock_httpx, temp_dir):
        """Тест правильного построения URL с параметрами"""
        with patch.object(PepeunitRestClient, '_get_base_url', return_value='https://param.test.com/api'):
            client = PepeunitRestClient(mock_settings)
            client._httpx_client = mock_httpx
            
            mock_response = Mock()
            mock_response.content = b'test'
            mock_httpx.get.return_value = mock_response
            
            # Используем временный файл
            temp_file = os.path.join(temp_dir, 'test_update.tar.gz')
            client.download_update('param-uuid', temp_file)
            
            # Проверяем что URL построен правильно с параметрами
            call_args = mock_httpx.get.call_args
            url = call_args[0][0]
            
            assert 'https://param.test.com/api/units/firmware/tgz/param-uuid' in url
            assert 'wbits=9' in url
            assert 'level=9' in url
