"""
Тесты для класса Settings
"""
import os
from unittest.mock import patch, Mock

import pytest

from pepeunit_client.settings import Settings


class TestSettings:
    """Тесты для класса Settings"""

    def test_default_values(self):
        """Тест значений по умолчанию"""
        settings = Settings()
        
        assert settings.PEPEUNIT_URL == ''
        assert settings.PEPEUNIT_APP_PREFIX == ''
        assert settings.PEPEUNIT_API_ACTUAL_PREFIX == ''
        assert settings.HTTP_TYPE == 'https'
        assert settings.MQTT_URL == ''
        assert settings.MQTT_PORT == 1883
        assert settings.PEPEUNIT_TOKEN == ''
        assert settings.SYNC_ENCRYPT_KEY == ''
        assert settings.SECRET_KEY == ''
        assert settings.COMMIT_VERSION == ''
        assert settings.PING_INTERVAL == 30
        assert settings.STATE_SEND_INTERVAL == 300
        assert settings.MINIMAL_LOG_LEVEL == 'Debug'

    def test_init_with_env_file(self, env_file, sample_env_data):
        """Тест инициализации с файлом окружения"""
        settings = Settings(env_file)
        
        assert settings.PEPEUNIT_URL == sample_env_data['PEPEUNIT_URL']
        assert settings.MQTT_PORT == sample_env_data['MQTT_PORT']
        assert settings.PEPEUNIT_TOKEN == sample_env_data['PEPEUNIT_TOKEN']

    def test_init_with_kwargs(self):
        """Тест инициализации с аргументами"""
        custom_values = {
            'PEPEUNIT_URL': 'custom.url.com',
            'MQTT_PORT': 8883,
            'CUSTOM_FIELD': 'custom_value'
        }
        
        settings = Settings(**custom_values)
        
        assert settings.PEPEUNIT_URL == 'custom.url.com'
        assert settings.MQTT_PORT == 8883
        assert settings.CUSTOM_FIELD == 'custom_value'

    def test_init_with_nonexistent_file(self):
        """Тест инициализации с несуществующим файлом"""
        settings = Settings('/nonexistent/file.json')
        
        # Должны остаться значения по умолчанию
        assert settings.PEPEUNIT_URL == ''
        assert settings.MQTT_PORT == 1883

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    @patch('pepeunit_client.file_manager.FileManager.read_json')
    def test_load_from_file_success(self, mock_read_json, mock_file_exists, sample_env_data):
        """Тест успешной загрузки из файла"""
        mock_file_exists.return_value = True
        mock_read_json.return_value = sample_env_data
        
        settings = Settings('test_file.json')
        settings.load_from_file()
        
        assert settings.PEPEUNIT_URL == sample_env_data['PEPEUNIT_URL']
        assert settings.MQTT_PORT == sample_env_data['MQTT_PORT']
        mock_read_json.assert_called_with('test_file.json')

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    def test_load_from_file_no_file_path(self, mock_file_exists):
        """Тест загрузки без указанного пути к файлу"""
        settings = Settings()
        settings.env_file_path = None
        
        settings.load_from_file()
        
        # FileManager.file_exists не должен вызываться
        mock_file_exists.assert_not_called()

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    def test_load_from_file_file_not_exists(self, mock_file_exists):
        """Тест загрузки когда файл не существует"""
        mock_file_exists.return_value = False
        
        settings = Settings('nonexistent.json')
        original_url = settings.PEPEUNIT_URL
        
        settings.load_from_file()
        
        # Значения не должны измениться
        assert settings.PEPEUNIT_URL == original_url

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    @patch('pepeunit_client.file_manager.FileManager.read_json')
    def test_get_env_values_success(self, mock_read_json, mock_file_exists, sample_env_data):
        """Тест успешного получения значений окружения"""
        mock_file_exists.return_value = True
        mock_read_json.return_value = sample_env_data
        
        settings = Settings('test_file.json')
        result = settings.get_env_values()
        
        assert result == sample_env_data
        mock_read_json.assert_called_with('test_file.json')

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    def test_get_env_values_no_file(self, mock_file_exists):
        """Тест получения значений когда файл не существует"""
        mock_file_exists.return_value = False
        
        settings = Settings('nonexistent.json')
        result = settings.get_env_values()
        
        assert result == {}

    def test_get_env_values_no_file_path(self):
        """Тест получения значений без пути к файлу"""
        settings = Settings()
        settings.env_file_path = None
        
        result = settings.get_env_values()
        
        assert result == {}

    @patch('pepeunit_client.file_manager.FileManager.copy_file')
    def test_update_env_file_success(self, mock_copy_file, env_file):
        """Тест успешного обновления файла окружения"""
        settings = Settings(env_file)
        new_file_path = '/path/to/new/env.json'
        
        with patch.object(settings, 'load_from_file') as mock_load:
            settings.update_env_file(new_file_path)
            
            mock_copy_file.assert_called_once_with(new_file_path, env_file)
            mock_load.assert_called_once()

    def test_update_env_file_no_env_path(self):
        """Тест обновления без установленного пути к файлу"""
        settings = Settings()
        settings.env_file_path = None
        
        with pytest.raises(ValueError, match="env_file_path not set"):
            settings.update_env_file('/path/to/new/env.json')

    def test_update_method(self):
        """Тест метода update с новыми значениями"""
        settings = Settings()
        
        update_values = {
            'PEPEUNIT_URL': 'updated.url.com',
            'MQTT_PORT': 8883,
            'NEW_FIELD': 'new_value'
        }
        
        settings.update(**update_values)
        
        assert settings.PEPEUNIT_URL == 'updated.url.com'
        assert settings.MQTT_PORT == 8883
        assert settings.NEW_FIELD == 'new_value'

    def test_kwargs_override_file_values(self, env_file, sample_env_data):
        """Тест что kwargs перезаписывают значения из файла"""
        kwargs_values = {
            'PEPEUNIT_URL': 'overridden.url.com',
            'CUSTOM_SETTING': 'custom_value'
        }
        
        settings = Settings(env_file, **kwargs_values)
        
        # Значение из kwargs должно перезаписать значение из файла
        assert settings.PEPEUNIT_URL == 'overridden.url.com'
        # Значения из файла должны сохраниться
        assert settings.MQTT_PORT == sample_env_data['MQTT_PORT']
        # Новое значение должно добавиться
        assert settings.CUSTOM_SETTING == 'custom_value'

    def test_dynamic_attribute_setting(self):
        """Тест динамического добавления атрибутов"""
        settings = Settings()
        
        # Устанавливаем атрибут напрямую
        settings.DYNAMIC_ATTRIBUTE = 'dynamic_value'
        
        assert settings.DYNAMIC_ATTRIBUTE == 'dynamic_value'

    def test_file_loading_integration(self, temp_dir, sample_env_data):
        """Интеграционный тест загрузки файла"""
        env_file = os.path.join(temp_dir, 'test_env.json')
        
        # Создаем файл с измененными данными
        modified_data = sample_env_data.copy()
        modified_data['PEPEUNIT_URL'] = 'integration.test.com'
        modified_data['MQTT_PORT'] = 9999
        
        import json
        with open(env_file, 'w') as f:
            json.dump(modified_data, f)
        
        # Загружаем настройки
        settings = Settings(env_file)
        
        assert settings.PEPEUNIT_URL == 'integration.test.com'
        assert settings.MQTT_PORT == 9999
        assert settings.PEPEUNIT_TOKEN == modified_data['PEPEUNIT_TOKEN']

    def test_load_from_file_partial_data(self, temp_dir):
        """Тест загрузки файла с частичными данными"""
        env_file = os.path.join(temp_dir, 'partial_env.json')
        partial_data = {
            'PEPEUNIT_URL': 'partial.test.com',
            'MQTT_PORT': 7777
            # Остальные поля отсутствуют
        }
        
        import json
        with open(env_file, 'w') as f:
            json.dump(partial_data, f)
        
        settings = Settings(env_file)
        
        # Установленные значения
        assert settings.PEPEUNIT_URL == 'partial.test.com'
        assert settings.MQTT_PORT == 7777
        
        # Значения по умолчанию должны остаться
        assert settings.HTTP_TYPE == 'https'
        assert settings.STATE_SEND_INTERVAL == 300

    def test_multiple_updates(self):
        """Тест множественных обновлений настроек"""
        settings = Settings()
        
        # Первое обновление
        settings.update(PEPEUNIT_URL='first.com', MQTT_PORT=1111)
        assert settings.PEPEUNIT_URL == 'first.com'
        assert settings.MQTT_PORT == 1111
        
        # Второе обновление
        settings.update(PEPEUNIT_URL='second.com', HTTP_TYPE='http')
        assert settings.PEPEUNIT_URL == 'second.com'  # Перезаписано
        assert settings.MQTT_PORT == 1111  # Осталось
        assert settings.HTTP_TYPE == 'http'  # Новое
