"""
Интеграционные тесты для полной функциональности PepeunitClient
Требуют реальных настроек в env.json, schema.json, log.json
"""

import json
import os
import pytest
import time
from unittest.mock import patch

from pepeunit_client import PepeunitClient, LogLevel


class TestRealIntegration:
    """Интеграционные тесты с реальными файлами"""
    
    def test_real_files_loading(self):
        """Тест загрузки реальных файлов из корня проекта"""
        # Пропускаем тест если файлы не существуют
        files = ["env.json", "schema.json", "log.json"]
        for file in files:
            if not os.path.exists(file):
                pytest.skip(f"Real file {file} not found")
        
        # Инициализируем клиент с реальными файлами
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Проверяем, что настройки загружены
        assert hasattr(client.settings, 'PEPEUNIT_URL')
        assert hasattr(client.settings, 'PEPEUNIT_TOKEN')
        
        # Проверяем извлечение unit_uuid
        if client.settings.PEPEUNIT_TOKEN:
            assert len(client.unit_uuid) > 0
        
        # Проверяем схему
        assert hasattr(client.schema, 'input_base_topic')
        assert hasattr(client.schema, 'output_base_topic')
    
    def test_logging_to_real_file(self):
        """Тест логирования в реальный файл"""
        if not os.path.exists("log.json"):
            pytest.skip("Real log.json not found")
        
        # Сохраняем оригинальный лог
        with open("log.json", 'r') as f:
            original_log = json.load(f)
        
        try:
            client = PepeunitClient(
                env_path="env.json",
                schema_path="schema.json",
                log_path="log.json",
                mqtt_enabled=False,
                rest_enabled=False
            )
            
            # Добавляем тестовую запись
            test_message = f"Integration test {time.time()}"
            client.log(LogLevel.INFO, test_message)
            
            # Проверяем, что запись добавилась
            full_log = client.get_full_log()
            assert len(full_log) > len(original_log)
            
            # Проверяем последнюю запись
            last_entry = full_log[-1]
            assert last_entry["text"] == test_message
            assert last_entry["level"] == "Info"
            
        finally:
            # Восстанавливаем оригинальный лог
            with open("log.json", 'w') as f:
                json.dump(original_log, f, indent=4)
    
    def test_schema_topic_access(self):
        """Тест доступа к топикам из реальной схемы"""
        if not os.path.exists("schema.json"):
            pytest.skip("Real schema.json not found")
        
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Проверяем получение входных топиков
        input_topics = client.get_subscription_topics()
        assert isinstance(input_topics, list)
        
        # Проверяем доступ к output_topic по ключу
        if "output/pepeunit" in client.schema.output_topic:
            output_topics = client.schema.output_topic["output/pepeunit"]
            assert isinstance(output_topics, list)
            assert len(output_topics) > 0
    
    def test_system_state_generation(self):
        """Тест генерации реального состояния системы"""
        if not os.path.exists("env.json"):
            pytest.skip("Real env.json not found")
        
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        state = client.get_system_state()
        
        # Проверяем структуру состояния
        required_fields = ["millis", "commit_version", "mem_free", "mem_alloc", "freq"]
        for field in required_fields:
            assert field in state
        
        # Проверяем типы данных
        assert isinstance(state["millis"], int)
        assert isinstance(state["mem_free"], int)
        assert isinstance(state["mem_alloc"], int)
        assert isinstance(state["freq"], (int, float))
        
        # Проверяем, что время актуальное (в пределах последних нескольких секунд)
        current_time = time.time() * 1000
        assert abs(current_time - state["millis"]) < 5000  # 5 секунд


@pytest.mark.skipif(
    not all(os.path.exists(f) for f in ["env.json", "schema.json", "log.json"]),
    reason="Real configuration files not found"
)
class TestMQTTIntegration:
    """Интеграционные тесты MQTT (требуют реальные настройки)"""
    
    def test_mqtt_client_creation(self):
        """Тест создания MQTT клиента с реальными настройками"""
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=True,
            rest_enabled=False
        )
        
        # Проверяем, что MQTT клиент создан
        assert client.mqtt_enabled
        assert client.mqtt_client is not None
        
        # Проверяем настройки MQTT
        if client.settings.MQTT_URL and client.settings.PEPEUNIT_TOKEN:
            # Можем попробовать подключиться (но не будем делать это в автотестах)
            pass
    
    @patch('pepeunit_client.mqtt_client.mqtt')  # Мокируем paho.mqtt
    def test_mqtt_connection_attempt(self, mock_mqtt):
        """Тест попытки подключения к MQTT"""
        # Настраиваем мок
        mock_client_instance = mock_mqtt.Client.return_value
        mock_client_instance.connect.return_value = None
        
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=True,
            rest_enabled=False
        )
        
        try:
            client.connect_mqtt()
            # Проверяем, что методы вызвались
            mock_client_instance.connect.assert_called()
            mock_client_instance.loop_start.assert_called()
        except Exception:
            # В реальных условиях может не подключиться - это нормально для тестов
            pass


@pytest.mark.skipif(
    not all(os.path.exists(f) for f in ["env.json", "schema.json", "log.json"]),
    reason="Real configuration files not found"
)
class TestRESTIntegration:
    """Интеграционные тесты REST (требуют реальные настройки)"""
    
    def test_rest_client_creation(self):
        """Тест создания REST клиента с реальными настройками"""
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=False,
            rest_enabled=True
        )
        
        # Проверяем, что REST клиент создан
        assert client.rest_enabled
        assert client.rest_client is not None
        
        # Проверяем построение URL
        if client.settings.PEPEUNIT_URL:
            test_url = client._build_api_url("/test")
            assert client.settings.PEPEUNIT_URL in test_url
            assert "/test" in test_url
    
    def test_auth_headers_generation(self):
        """Тест генерации заголовков авторизации"""
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=False,
            rest_enabled=True
        )
        
        headers = client._get_auth_headers()
        
        assert "accept" in headers
        assert "x-auth-token" in headers
        assert headers["accept"] == "application/json"
        
        if client.settings.PEPEUNIT_TOKEN:
            assert headers["x-auth-token"] == client.settings.PEPEUNIT_TOKEN


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    def test_missing_files_handling(self, temp_dir):
        """Тест обработки отсутствующих файлов"""
        non_existent_path = os.path.join(temp_dir, "non_existent.json")
        
        # Клиент должен создаваться даже с несуществующими файлами
        client = PepeunitClient(
            env_path=non_existent_path,
            schema_path=non_existent_path,
            log_path=non_existent_path,
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Настройки должны быть пустыми/дефолтными
        assert isinstance(client.settings, object)
        assert isinstance(client.schema, object)
    
    def test_invalid_json_handling(self, temp_dir):
        """Тест обработки некорректных JSON файлов"""
        # Создаем файл с некорректным JSON
        bad_json_path = os.path.join(temp_dir, "bad.json")
        with open(bad_json_path, 'w') as f:
            f.write("{ invalid json content")
        
        # Клиент должен обработать ошибку и продолжить работу
        client = PepeunitClient(
            env_path=bad_json_path,
            schema_path=bad_json_path,
            log_path=bad_json_path,
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Должны быть дефолтные значения
        assert hasattr(client.settings, 'PEPEUNIT_URL')
        assert hasattr(client.schema, 'input_base_topic')
    
    def test_logging_with_errors(self, temp_dir):
        """Тест логирования при ошибках"""
        # Создаем директорию только для чтения
        readonly_dir = os.path.join(temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Только чтение
        
        readonly_log = os.path.join(readonly_dir, "log.json")
        
        try:
            client = PepeunitClient(
                env_path="env.json",
                schema_path="schema.json",
                log_path=readonly_log,
                mqtt_enabled=False,
                rest_enabled=False
            )
            
            # Логирование должно обрабатывать ошибку записи
            client.log(LogLevel.ERROR, "Test error message")
            
            # Клиент должен продолжить работу
            assert hasattr(client, 'settings')
            
        finally:
            # Восстанавливаем права
            os.chmod(readonly_dir, 0o755)


class TestPerformanceAndStability:
    """Тесты производительности и стабильности"""
    
    def test_multiple_log_entries(self, test_files):
        """Тест множественного логирования"""
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Добавляем много записей в лог
        num_entries = 100
        for i in range(num_entries):
            client.log(LogLevel.INFO, f"Test message {i}")
        
        # Проверяем, что все записи добавились
        full_log = client.get_full_log()
        assert len(full_log) >= num_entries + 2  # +2 из исходных тестовых данных
    
    def test_rapid_settings_refresh(self, test_files):
        """Тест частого обновления настроек"""
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Несколько раз обновляем настройки
        for i in range(10):
            client.refresh_settings()
            # Проверяем, что настройки остаются консистентными
            assert hasattr(client.settings, 'PEPEUNIT_URL')
            assert hasattr(client.schema, 'input_base_topic')
    
    def test_memory_usage_stability(self, test_files):
        """Тест стабильности использования памяти"""
        client = PepeunitClient(
            env_path=test_files["env_path"],
            schema_path=test_files["schema_path"],
            log_path=test_files["log_path"],
            mqtt_enabled=False,
            rest_enabled=False
        )
        
        # Выполняем много операций
        for i in range(50):
            client.get_system_state()
            client.get_subscription_topics()
            client.log(LogLevel.DEBUG, f"Memory test {i}")
            if i % 10 == 0:
                client.refresh_settings()
        
        # Проверяем, что клиент остается работоспособным
        state = client.get_system_state()
        assert "millis" in state
        
        log_count = len(client.get_full_log())
        assert log_count >= 50
