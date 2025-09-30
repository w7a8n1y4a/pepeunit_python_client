"""
Тесты для основного класса PepeunitClient
"""
import json
import os
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock

import pytest

from pepeunit_client.client import PepeunitClient
from pepeunit_client.enums import BaseInputTopicType, BaseOutputTopicType


class TestPepeunitClientInit:
    """Тесты инициализации PepeunitClient"""

    def test_init_minimal(self, env_file, schema_file, log_file):
        """Тест минимальной инициализации"""
        client = PepeunitClient(env_file, schema_file, log_file)
        
        assert client.env_file_path == env_file
        assert client.schema_file_path == schema_file
        assert client.log_file_path == log_file
        assert client.enable_mqtt is False
        assert client.enable_rest is False
        assert client.cycle_speed == 0.1
        assert client.mqtt_client is None
        assert client.rest_client is None
        assert client._running is False

    def test_init_with_mqtt_enabled(self, env_file, schema_file, log_file):
        """Тест инициализации с включенным MQTT"""
        with patch.object(PepeunitClient, '_get_default_mqtt_client') as mock_get_mqtt:
            mock_mqtt_client = Mock()
            mock_get_mqtt.return_value = mock_mqtt_client
            
            client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True)
            
            assert client.enable_mqtt is True
            assert client.mqtt_client == mock_mqtt_client
            assert client.logger.mqtt_client == mock_mqtt_client

    def test_init_with_rest_enabled(self, env_file, schema_file, log_file):
        """Тест инициализации с включенным REST"""
        with patch.object(PepeunitClient, '_get_default_rest_client') as mock_get_rest:
            mock_rest_client = Mock()
            mock_get_rest.return_value = mock_rest_client
            
            client = PepeunitClient(env_file, schema_file, log_file, enable_rest=True)
            
            assert client.enable_rest is True
            assert client.rest_client == mock_rest_client

    def test_init_with_custom_clients(self, env_file, schema_file, log_file, mock_mqtt_client, mock_rest_client):
        """Тест инициализации с пользовательскими клиентами"""
        client = PepeunitClient(
            env_file, schema_file, log_file,
            enable_mqtt=True, enable_rest=True,
            mqtt_client=mock_mqtt_client, rest_client=mock_rest_client
        )
        
        assert client.mqtt_client == mock_mqtt_client
        assert client.rest_client == mock_rest_client

    def test_init_with_custom_cycle_speed(self, env_file, schema_file, log_file):
        """Тест инициализации с пользовательской скоростью цикла"""
        client = PepeunitClient(env_file, schema_file, log_file, cycle_speed=0.05)
        
        assert client.cycle_speed == 0.05


class TestPepeunitClientProperties:
    """Тесты свойств PepeunitClient"""

    def test_unit_uuid_valid_token(self, env_file, schema_file, log_file, mock_jwt_token):
        """Тест получения UUID из валидного токена"""
        with patch('pepeunit_client.settings.Settings') as MockSettings:
            mock_settings = Mock()
            mock_settings.PEPEUNIT_TOKEN = mock_jwt_token
            MockSettings.return_value = mock_settings
            
            client = PepeunitClient(env_file, schema_file, log_file)
            
            assert client.unit_uuid == "test-uuid-1234"

    def test_unit_uuid_invalid_token_format(self, env_file, schema_file, log_file):
        """Тест исключения при невалидном формате токена"""
        with patch('pepeunit_client.settings.Settings') as MockSettings:
            mock_settings = Mock()
            mock_settings.PEPEUNIT_TOKEN = "invalid.token"  # Только 2 части вместо 3
            MockSettings.return_value = mock_settings
            
            client = PepeunitClient(env_file, schema_file, log_file)
            
            with pytest.raises(ValueError, match="Invalid JWT token format"):
                _ = client.unit_uuid


class TestPepeunitClientMethods:
    """Тесты методов PepeunitClient"""

    def test_set_cycle_speed_valid(self, env_file, schema_file, log_file):
        """Тест установки валидной скорости цикла"""
        client = PepeunitClient(env_file, schema_file, log_file)
        
        client.set_cycle_speed(0.2)
        assert client.cycle_speed == 0.2
        
        client.set_cycle_speed(1.5)
        assert client.cycle_speed == 1.5

    def test_set_cycle_speed_invalid(self, env_file, schema_file, log_file):
        """Тест исключения при невалидной скорости цикла"""
        client = PepeunitClient(env_file, schema_file, log_file)
        
        with pytest.raises(ValueError, match="Cycle speed must be greater than 0"):
            client.set_cycle_speed(0)
        
        with pytest.raises(ValueError, match="Cycle speed must be greater than 0"):
            client.set_cycle_speed(-0.1)

    @patch('pepeunit_client.client.FileManager')
    @patch('pepeunit_client.client.subprocess')
    @patch('pepeunit_client.client.sys')
    @patch('pepeunit_client.client.tempfile')
    def test_update_device_program(self, mock_tempfile, mock_sys, mock_subprocess, mock_file_manager, 
                                   env_file, schema_file, log_file):
        """Тест обновления программы устройства"""
        client = PepeunitClient(env_file, schema_file, log_file)
        
        archive_path = '/path/to/update.tar.gz'
        temp_extract_dir = '/tmp/extract'
        unit_directory = os.path.dirname(env_file)
        
        mock_tempfile.TemporaryDirectory.return_value.__enter__.return_value = temp_extract_dir
        mock_sys.executable = '/usr/bin/python3'
        mock_sys.argv = ['script.py', 'arg1']
        
        with patch.object(client, 'stop_main_cycle') as mock_stop:
            client.update_device_program(archive_path)
            
            # Проверяем вызовы
            mock_file_manager.extract_tar_gz.assert_called_once_with(archive_path, temp_extract_dir)
            mock_file_manager.copy_directory_contents.assert_called_once_with(temp_extract_dir, unit_directory)
            mock_stop.assert_called_once()
            mock_subprocess.Popen.assert_called_once_with(['/usr/bin/python3', 'script.py', 'arg1'])
            mock_sys.exit.assert_called_once_with(0)

    @patch('pepeunit_client.client.time')
    def test_get_system_state_with_psutil(self, mock_time, env_file, schema_file, log_file, mock_psutil):
        """Тест получения системного состояния с psutil"""
        mock_time.time.return_value = 1672531200.123
        
        client = PepeunitClient(env_file, schema_file, log_file)
        client.settings.COMMIT_VERSION = 'v1.2.3'
        
        result = client.get_system_state()
        
        expected = {
            'millis': 1672531200123,
            'mem_free': 8000000000,
            'mem_alloc': 8000000000,  # 16GB - 8GB
            'freq': 2400.0,
            'commit_version': 'v1.2.3'
        }
        
        assert result == expected

    @patch('pepeunit_client.client.time')
    def test_get_system_state_without_psutil(self, mock_time, env_file, schema_file, log_file):
        """Тест получения системного состояния без psutil"""
        mock_time.time.return_value = 1672531200.456
        
        with patch('pepeunit_client.client.psutil', side_effect=ImportError()):
            client = PepeunitClient(env_file, schema_file, log_file)
            client.settings.COMMIT_VERSION = 'v1.0.0'
            
            result = client.get_system_state()
            
            expected = {
                'millis': 1672531200456,
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': 'v1.0.0'
            }
            
            assert result == expected

    def test_set_mqtt_input_handler(self, env_file, schema_file, log_file, mock_mqtt_client):
        """Тест установки обработчика входящих MQTT сообщений"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, mqtt_client=mock_mqtt_client)
        
        test_handler = Mock()
        client.set_mqtt_input_handler(test_handler)
        
        assert client._mqtt_input_handler == test_handler
        mock_mqtt_client.set_input_handler.assert_called_once()

    def test_download_update_success(self, env_file, schema_file, log_file, mock_rest_client):
        """Тест успешного скачивания обновления"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_rest=True, rest_client=mock_rest_client)
        
        with patch.object(client, 'unit_uuid', 'test-uuid'):
            client.download_update('/path/to/update.tar.gz')
            
            mock_rest_client.download_update.assert_called_once_with('test-uuid', '/path/to/update.tar.gz')

    def test_download_update_no_rest(self, env_file, schema_file, log_file):
        """Тест исключения при скачивании обновления без REST"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_rest=False)
        
        with pytest.raises(RuntimeError, match="REST client is not enabled or available"):
            client.download_update('/path/to/update.tar.gz')

    def test_download_env_success(self, env_file, schema_file, log_file, mock_rest_client):
        """Тест успешного скачивания env файла"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_rest=True, rest_client=mock_rest_client)
        
        with patch.object(client, 'unit_uuid', 'test-uuid'), \
             patch.object(client.settings, 'load_from_file') as mock_load:
            
            client.download_env('/path/to/env.json')
            
            mock_rest_client.download_env.assert_called_once_with('test-uuid', '/path/to/env.json')
            mock_load.assert_called_once()

    def test_download_schema_success(self, env_file, schema_file, log_file, mock_rest_client):
        """Тест успешного скачивания схемы"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_rest=True, rest_client=mock_rest_client)
        
        with patch.object(client, 'unit_uuid', 'test-uuid'), \
             patch.object(client.schema, 'update_from_file') as mock_update:
            
            client.download_schema('/path/to/schema.json')
            
            mock_rest_client.download_schema.assert_called_once_with('test-uuid', '/path/to/schema.json')
            mock_update.assert_called_once()

    def test_set_state_storage(self, env_file, schema_file, log_file, mock_rest_client):
        """Тест установки состояния в хранилище"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_rest=True, rest_client=mock_rest_client)
        
        test_state = {'sensor1': 25.5, 'active': True}
        
        with patch.object(client, 'unit_uuid', 'test-uuid'):
            client.set_state_storage(test_state)
            
            mock_rest_client.set_state_storage.assert_called_once_with('test-uuid', test_state)

    def test_get_state_storage(self, env_file, schema_file, log_file, mock_rest_client):
        """Тест получения состояния из хранилища"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_rest=True, rest_client=mock_rest_client)
        
        expected_state = {'temperature': 22.1}
        mock_rest_client.get_state_storage.return_value = expected_state
        
        with patch.object(client, 'unit_uuid', 'test-uuid'):
            result = client.get_state_storage()
            
            assert result == expected_state
            mock_rest_client.get_state_storage.assert_called_once_with('test-uuid')

    @patch('pepeunit_client.client.tempfile')
    @patch('pepeunit_client.client.os')
    def test_perform_update_success(self, mock_os, mock_tempfile, env_file, schema_file, log_file, mock_rest_client):
        """Тест успешного выполнения полного обновления"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, enable_rest=True, rest_client=mock_rest_client)
        
        mock_tempdir = '/tmp'
        mock_tempfile.gettempdir.return_value = mock_tempdir
        
        with patch.object(client, 'unit_uuid', 'update-uuid'), \
             patch.object(client, 'download_update') as mock_download, \
             patch.object(client, 'update_device_program') as mock_update_program:
            
            client.perform_update()
            
            expected_archive_path = '/tmp/update_update-uuid.tar.gz'
            mock_download.assert_called_once_with(expected_archive_path)
            mock_update_program.assert_called_once_with(expected_archive_path)
            mock_os.remove.assert_called_once_with(expected_archive_path)

    def test_perform_update_requires_both_clients(self, env_file, schema_file, log_file):
        """Тест что обновление требует оба клиента"""
        # Только MQTT
        client1 = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, enable_rest=False)
        with pytest.raises(RuntimeError, match="Both MQTT and REST clients must be enabled"):
            client1.perform_update()
        
        # Только REST
        client2 = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=False, enable_rest=True)
        with pytest.raises(RuntimeError, match="Both MQTT and REST clients must be enabled"):
            client2.perform_update()


class TestPepeunitClientMQTTHandlers:
    """Тесты MQTT обработчиков PepeunitClient"""

    def test_base_mqtt_input_func_update(self, env_file, schema_file, log_file, mock_mqtt_message):
        """Тест обработки сообщения об обновлении"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, enable_rest=True)
        client.schema.input_base_topic = {
            BaseInputTopicType.UPDATE_PEPEUNIT.value: ['test/update/topic']
        }
        
        with patch.object(client, '_handle_update') as mock_handle:
            msg = mock_mqtt_message('test/update/topic', 'update payload')
            client._base_mqtt_input_func(msg)
            
            mock_handle.assert_called_once_with('update payload')

    def test_base_mqtt_input_func_env_update(self, env_file, schema_file, log_file, mock_mqtt_message):
        """Тест обработки сообщения об обновлении env"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, enable_rest=True)
        client.schema.input_base_topic = {
            BaseInputTopicType.ENV_UPDATE_PEPEUNIT.value: ['test/env_update/topic']
        }
        
        with patch.object(client, '_handle_env_update') as mock_handle:
            msg = mock_mqtt_message('test/env_update/topic', 'env payload')
            client._base_mqtt_input_func(msg)
            
            mock_handle.assert_called_once()

    def test_base_mqtt_input_func_exception_handling(self, env_file, schema_file, log_file, mock_mqtt_message):
        """Тест обработки исключений в MQTT обработчике"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True)
        client.schema.input_base_topic = {
            BaseInputTopicType.UPDATE_PEPEUNIT.value: ['test/update/topic']
        }
        
        with patch.object(client, '_handle_update', side_effect=Exception("Handler error")):
            msg = mock_mqtt_message('test/update/topic', 'payload')
            client._base_mqtt_input_func(msg)
            
            # Проверяем что ошибка залогирована
            client.logger.error.assert_called_with("Error in base MQTT input handler: Handler error")

    def test_handle_log_sync(self, env_file, schema_file, log_file, mock_mqtt_client):
        """Тест обработки синхронизации лога"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, mqtt_client=mock_mqtt_client)
        client.schema.output_base_topic = {
            BaseOutputTopicType.LOG_PEPEUNIT.value: ['test/log/topic']
        }
        
        sample_log_data = [{'level': 'Info', 'text': 'Test log'}]
        
        with patch.object(client.logger, 'get_full_log', return_value=sample_log_data):
            client._handle_log_sync()
            
            mock_mqtt_client.publish.assert_called_once_with(
                'test/log/topic', 
                json.dumps(sample_log_data)
            )

    def test_subscribe_all_schema_topics(self, env_file, schema_file, log_file, mock_mqtt_client, sample_schema_data):
        """Тест подписки на все топики схемы"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, mqtt_client=mock_mqtt_client)
        client.schema._schema_data = sample_schema_data
        
        client.subscribe_all_schema_topics()
        
        expected_topics = []
        for topic_list in sample_schema_data['input_base_topic'].values():
            expected_topics.extend(topic_list)
        for topic_list in sample_schema_data['input_topic'].values():
            expected_topics.extend(topic_list)
        
        mock_mqtt_client.subscribe_topics.assert_called_once_with(expected_topics)

    def test_publish_to_topics(self, env_file, schema_file, log_file, mock_mqtt_client, sample_schema_data):
        """Тест публикации в топики"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, mqtt_client=mock_mqtt_client)
        client.schema._schema_data = sample_schema_data
        
        client.publish_to_topics('test_output', 'test message')
        
        expected_topics = sample_schema_data['output_topic']['test_output']
        for topic in expected_topics:
            mock_mqtt_client.publish.assert_any_call(topic, 'test message')


class TestPepeunitClientMainCycle:
    """Тесты главного цикла PepeunitClient"""

    @patch('pepeunit_client.client.time')
    def test_base_mqtt_output_handler(self, mock_time, env_file, schema_file, log_file, mock_mqtt_client):
        """Тест базового обработчика вывода MQTT"""
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, mqtt_client=mock_mqtt_client)
        client.schema.output_base_topic = {
            BaseOutputTopicType.STATE_PEPEUNIT.value: ['test/state/topic']
        }
        client.settings.STATE_SEND_INTERVAL = 10
        client._last_state_send = 0
        
        # Время для отправки состояния
        mock_time.time.return_value = 15
        
        with patch.object(client, 'get_system_state') as mock_get_state:
            mock_get_state.return_value = {'test': 'state'}
            
            client._base_mqtt_output_handler()
            
            mock_mqtt_client.publish.assert_called_once_with(
                'test/state/topic',
                json.dumps({'test': 'state'})
            )
            assert client._last_state_send == 15

    @patch('pepeunit_client.client.time')
    def test_run_main_cycle(self, mock_time, env_file, schema_file, log_file):
        """Тест запуска главного цикла"""
        client = PepeunitClient(env_file, schema_file, log_file)
        client.cycle_speed = 0.01  # Быстрый цикл для теста
        
        cycle_count = 0
        def mock_sleep(duration):
            nonlocal cycle_count
            cycle_count += 1
            if cycle_count >= 3:  # Останавливаем после 3 итераций
                client._running = False
        
        mock_time.sleep.side_effect = mock_sleep
        
        output_handler = Mock()
        
        with patch.object(client, '_base_mqtt_output_handler') as mock_base_handler:
            client.run_main_cycle(output_handler)
            
            assert mock_base_handler.call_count == 3
            assert output_handler.call_count == 3
            assert client._mqtt_output_handler == output_handler

    def test_stop_main_cycle(self, env_file, schema_file, log_file):
        """Тест остановки главного цикла"""
        client = PepeunitClient(env_file, schema_file, log_file)
        client._running = True
        
        client.stop_main_cycle()
        
        assert client._running is False

    def test_set_output_handler(self, env_file, schema_file, log_file):
        """Тест установки обработчика вывода"""
        client = PepeunitClient(env_file, schema_file, log_file)
        
        output_handler = Mock()
        client.set_output_handler(output_handler)
        
        assert client._mqtt_output_handler == output_handler


class TestPepeunitClientIntegration:
    """Интеграционные тесты PepeunitClient"""

    def test_full_initialization_integration(self, temp_dir, sample_env_data, sample_schema_data):
        """Интеграционный тест полной инициализации"""
        # Создаем файлы
        env_file = os.path.join(temp_dir, 'integration_env.json')
        schema_file = os.path.join(temp_dir, 'integration_schema.json')
        log_file = os.path.join(temp_dir, 'integration_log.json')
        
        with open(env_file, 'w') as f:
            json.dump(sample_env_data, f)
        
        with open(schema_file, 'w') as f:
            json.dump(sample_schema_data, f)
        
        # Инициализируем клиент
        client = PepeunitClient(env_file, schema_file, log_file, enable_mqtt=True, enable_rest=True)
        
        # Проверяем что все компоненты инициализированы
        assert client.settings.PEPEUNIT_URL == sample_env_data['PEPEUNIT_URL']
        assert client.schema.input_base_topic == sample_schema_data['input_base_topic']
        assert os.path.exists(log_file)  # Лог файл должен быть создан
        assert client.mqtt_client is not None
        assert client.rest_client is not None

    @patch('pepeunit_client.client.time')
    def test_mqtt_message_flow_integration(self, mock_time, env_file, schema_file, log_file, 
                                          mock_mqtt_client, mock_rest_client, mock_mqtt_message):
        """Интеграционный тест потока MQTT сообщений"""
        client = PepeunitClient(
            env_file, schema_file, log_file,
            enable_mqtt=True, enable_rest=True,
            mqtt_client=mock_mqtt_client, rest_client=mock_rest_client
        )
        
        # Настройка схемы
        client.schema.input_base_topic = {
            BaseInputTopicType.ENV_UPDATE_PEPEUNIT.value: ['test/env_update']
        }
        
        # Установка пользовательского обработчика
        user_handler = Mock()
        client.set_mqtt_input_handler(user_handler)
        
        # Проверяем что установлен комбинированный обработчик
        combined_handler = mock_mqtt_client.set_input_handler.call_args[0][0]
        
        # Симулируем входящее сообщение
        msg = mock_mqtt_message('test/env_update', 'env_update_payload')
        
        with patch.object(client, '_handle_env_update') as mock_handle_env:
            combined_handler(msg)
            
            # Проверяем что вызваны оба обработчика
            mock_handle_env.assert_called_once()
            user_handler.assert_called_once_with(client, msg)
