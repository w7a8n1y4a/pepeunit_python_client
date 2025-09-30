"""
Тесты для класса Logger
"""
import json
import os
from unittest.mock import Mock, patch, MagicMock

import pytest

from pepeunit_client.logger import Logger
from pepeunit_client.enums import LogLevel, BaseOutputTopicType


class TestLogger:
    """Тесты для класса Logger"""

    def test_init_minimal(self, log_file):
        """Тест минимальной инициализации логгера"""
        logger = Logger(log_file)
        
        assert logger.log_file_path == log_file
        assert logger.mqtt_client is None
        assert logger.schema_manager is None
        assert logger.settings is None

    def test_init_with_all_params(self, log_file, mock_settings, mock_schema_manager):
        """Тест полной инициализации логгера"""
        mock_mqtt_client = Mock()
        
        logger = Logger(log_file, mock_mqtt_client, mock_schema_manager, mock_settings)
        
        assert logger.log_file_path == log_file
        assert logger.mqtt_client == mock_mqtt_client
        assert logger.schema_manager == mock_schema_manager
        assert logger.settings == mock_settings

    def test_string_to_log_level_mapping(self, mock_logger):
        """Тест преобразования строки в уровень логирования"""
        test_cases = [
            ('Debug', LogLevel.DEBUG),
            ('Info', LogLevel.INFO),
            ('Warning', LogLevel.WARNING),
            ('Error', LogLevel.ERROR),
            ('Critical', LogLevel.CRITICAL),
            ('Unknown', LogLevel.DEBUG)  # По умолчанию
        ]
        
        for input_str, expected_level in test_cases:
            result = mock_logger._string_to_log_level(input_str)
            assert result == expected_level

    def test_should_log_no_settings(self, log_file):
        """Тест проверки уровня логирования без настроек"""
        logger = Logger(log_file)
        
        # Без настроек должно логировать все
        assert logger._should_log(LogLevel.DEBUG) is True
        assert logger._should_log(LogLevel.CRITICAL) is True

    def test_should_log_with_settings(self, mock_logger):
        """Тест проверки уровня логирования с настройками"""
        # Устанавливаем минимальный уровень Warning
        mock_logger.settings.MINIMAL_LOG_LEVEL = 'Warning'
        
        assert mock_logger._should_log(LogLevel.DEBUG) is False
        assert mock_logger._should_log(LogLevel.INFO) is False
        assert mock_logger._should_log(LogLevel.WARNING) is True
        assert mock_logger._should_log(LogLevel.ERROR) is True
        assert mock_logger._should_log(LogLevel.CRITICAL) is True

    @patch('pepeunit_client.file_manager.FileManager.append_to_json_list')
    def test_write_to_file(self, mock_append, mock_logger, mock_datetime):
        """Тест записи в файл"""
        log_entry = {
            'level': 'Info',
            'text': 'Test message',
            'create_datetime': '2023-01-01T00:00:00.000000'
        }
        
        mock_logger._write_to_file(log_entry)
        
        mock_append.assert_called_once_with(mock_logger.log_file_path, log_entry)

    def test_send_mqtt_no_clients(self, log_file):
        """Тест отправки MQTT без клиентов"""
        logger = Logger(log_file)
        log_entry = {'level': 'Info', 'text': 'Test'}
        
        # Не должно вызывать исключение
        logger._send_mqtt(log_entry)

    def test_send_mqtt_success(self, mock_logger):
        """Тест успешной отправки MQTT"""
        mock_mqtt_client = Mock()
        mock_logger.mqtt_client = mock_mqtt_client
        
        # Настраиваем схему с топиком для логов
        mock_logger.schema_manager.output_base_topic = {
            BaseOutputTopicType.LOG_PEPEUNIT.value: ['test/log/topic']
        }
        
        log_entry = {'level': 'Info', 'text': 'Test message'}
        
        mock_logger._send_mqtt(log_entry)
        
        mock_mqtt_client.publish.assert_called_once_with(
            'test/log/topic',
            json.dumps(log_entry)
        )

    def test_send_mqtt_no_topic(self, mock_logger):
        """Тест отправки MQTT без топика в схеме"""
        mock_mqtt_client = Mock()
        mock_logger.mqtt_client = mock_mqtt_client
        mock_logger.schema_manager.output_base_topic = {}
        
        log_entry = {'level': 'Info', 'text': 'Test message'}
        
        # Не должно вызывать исключение
        mock_logger._send_mqtt(log_entry)
        mock_mqtt_client.publish.assert_not_called()

    def test_send_mqtt_exception_handling(self, mock_logger):
        """Тест обработки исключений при отправке MQTT"""
        mock_mqtt_client = Mock()
        mock_mqtt_client.publish.side_effect = Exception("MQTT Error")
        mock_logger.mqtt_client = mock_mqtt_client
        
        mock_logger.schema_manager.output_base_topic = {
            BaseOutputTopicType.LOG_PEPEUNIT.value: ['test/log/topic']
        }
        
        log_entry = {'level': 'Info', 'text': 'Test message'}
        
        # Не должно вызывать исключение
        mock_logger._send_mqtt(log_entry)

    @patch('pepeunit_client.logger.datetime')
    def test_get_current_datetime(self, mock_datetime, mock_logger):
        """Тест получения текущего времени"""
        mock_datetime.datetime.utcnow.return_value.isoformat.return_value = '2023-01-01T12:00:00.000000'
        
        result = mock_logger._get_current_datetime()
        
        assert result == '2023-01-01T12:00:00.000000'
        mock_datetime.datetime.utcnow.assert_called_once()

    @patch.object(Logger, '_write_to_file')
    @patch.object(Logger, '_send_mqtt')
    @patch.object(Logger, '_should_log')
    def test_log_method_should_log_true(self, mock_should_log, mock_send_mqtt, mock_write_to_file, mock_logger, mock_datetime):
        """Тест метода _log когда нужно логировать"""
        mock_should_log.return_value = True
        
        mock_logger._log(LogLevel.INFO, 'Test message')
        
        mock_should_log.assert_called_once_with(LogLevel.INFO)
        mock_write_to_file.assert_called_once()
        mock_send_mqtt.assert_called_once()

    @patch.object(Logger, '_write_to_file')
    @patch.object(Logger, '_send_mqtt')
    @patch.object(Logger, '_should_log')
    def test_log_method_should_log_false(self, mock_should_log, mock_send_mqtt, mock_write_to_file, mock_logger):
        """Тест метода _log когда не нужно логировать"""
        mock_should_log.return_value = False
        
        mock_logger._log(LogLevel.DEBUG, 'Test message')
        
        mock_should_log.assert_called_once_with(LogLevel.DEBUG)
        mock_write_to_file.assert_not_called()
        mock_send_mqtt.assert_not_called()

    @patch.object(Logger, '_log')
    def test_debug_method(self, mock_log, mock_logger):
        """Тест метода debug"""
        mock_logger.debug('Debug message')
        
        mock_log.assert_called_once_with(LogLevel.DEBUG, 'Debug message')

    @patch.object(Logger, '_log')
    def test_info_method(self, mock_log, mock_logger):
        """Тест метода info"""
        mock_logger.info('Info message')
        
        mock_log.assert_called_once_with(LogLevel.INFO, 'Info message')

    @patch.object(Logger, '_log')
    def test_warning_method(self, mock_log, mock_logger):
        """Тест метода warning"""
        mock_logger.warning('Warning message')
        
        mock_log.assert_called_once_with(LogLevel.WARNING, 'Warning message')

    @patch.object(Logger, '_log')
    def test_error_method(self, mock_log, mock_logger):
        """Тест метода error"""
        mock_logger.error('Error message')
        
        mock_log.assert_called_once_with(LogLevel.ERROR, 'Error message')

    @patch.object(Logger, '_log')
    def test_critical_method(self, mock_log, mock_logger):
        """Тест метода critical"""
        mock_logger.critical('Critical message')
        
        mock_log.assert_called_once_with(LogLevel.CRITICAL, 'Critical message')

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    @patch('pepeunit_client.file_manager.FileManager.read_json')
    def test_get_full_log_file_exists(self, mock_read_json, mock_file_exists, mock_logger, sample_log_entries):
        """Тест получения полного лога когда файл существует"""
        mock_file_exists.return_value = True
        mock_read_json.return_value = sample_log_entries
        
        result = mock_logger.get_full_log()
        
        assert result == sample_log_entries
        mock_file_exists.assert_called_once_with(mock_logger.log_file_path)
        mock_read_json.assert_called_once_with(mock_logger.log_file_path)

    @patch('pepeunit_client.file_manager.FileManager.file_exists')
    def test_get_full_log_file_not_exists(self, mock_file_exists, mock_logger):
        """Тест получения полного лога когда файл не существует"""
        mock_file_exists.return_value = False
        
        result = mock_logger.get_full_log()
        
        assert result == []
        mock_file_exists.assert_called_once_with(mock_logger.log_file_path)

    @patch('pepeunit_client.file_manager.FileManager.write_json')
    def test_reset_log(self, mock_write_json, mock_logger):
        """Тест сброса лога"""
        mock_logger.reset_log()
        
        mock_write_json.assert_called_once_with(mock_logger.log_file_path, [])

    def test_integration_logging_flow(self, temp_dir, mock_settings, mock_schema_manager, mock_datetime):
        """Интеграционный тест полного потока логирования"""
        log_file = os.path.join(temp_dir, 'integration_log.json')
        mock_mqtt_client = Mock()
        
        # Настройка схемы
        mock_schema_manager.output_base_topic = {
            BaseOutputTopicType.LOG_PEPEUNIT.value: ['test/integration/log']
        }
        
        # Настройка уровня логирования
        mock_settings.MINIMAL_LOG_LEVEL = 'Info'
        
        logger = Logger(log_file, mock_mqtt_client, mock_schema_manager, mock_settings)
        
        # Логируем сообщения разных уровней
        logger.debug('This should be filtered out')  # Не должно логироваться
        logger.info('This should be logged')         # Должно логироваться
        logger.error('This is an error')             # Должно логироваться
        
        # Проверяем что файл лога создан и содержит правильные записи
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        # Должно быть 2 записи (debug отфильтрован)
        assert len(log_data) == 2
        assert log_data[0]['level'] == 'Info'
        assert log_data[0]['text'] == 'This should be logged'
        assert log_data[1]['level'] == 'Error'
        assert log_data[1]['text'] == 'This is an error'
        
        # Проверяем MQTT публикации (2 вызова)
        assert mock_mqtt_client.publish.call_count == 2

    def test_log_entry_structure(self, temp_dir, mock_datetime):
        """Тест структуры записи лога"""
        log_file = os.path.join(temp_dir, 'structure_test.json')
        logger = Logger(log_file)
        
        logger.info('Test message for structure')
        
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) == 1
        log_entry = log_data[0]
        
        # Проверяем обязательные поля
        assert 'level' in log_entry
        assert 'text' in log_entry
        assert 'create_datetime' in log_entry
        
        # Проверяем значения
        assert log_entry['level'] == 'Info'
        assert log_entry['text'] == 'Test message for structure'
        assert log_entry['create_datetime'] == '2023-01-01T00:00:00.000000'

    def test_concurrent_logging_safety(self, temp_dir, mock_settings):
        """Тест безопасности при одновременном логировании"""
        log_file = os.path.join(temp_dir, 'concurrent_log.json')
        logger = Logger(log_file, None, None, mock_settings)
        
        # Логируем несколько сообщений подряд
        messages = [f'Message {i}' for i in range(5)]
        
        for msg in messages:
            logger.info(msg)
        
        # Проверяем что все сообщения записались
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) == 5
        for i, entry in enumerate(log_data):
            assert entry['text'] == f'Message {i}'
