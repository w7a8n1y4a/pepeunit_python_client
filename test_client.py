#!/usr/bin/env python3
"""
Простой тест для проверки работоспособности PepeunitClient
"""

import os
import tempfile
import json
from src.pepeunit_client import PepeunitClient, LogLevel

def test_basic_functionality():
    """Тестирует базовую функциональность"""
    print("🧪 Тестирование PepeunitClient...")
    
    # Создаем временные файлы
    with tempfile.TemporaryDirectory() as temp_dir:
        env_path = os.path.join(temp_dir, "env.json")
        schema_path = os.path.join(temp_dir, "schema.json")
        log_path = os.path.join(temp_dir, "log.json")
        
        # Создаем тестовые данные
        test_env = {
            "COMMIT_VERSION": "1.0.0",
            "PING_INTERVAL": 30,
            "STATE_SEND_INTERVAL": 300
        }
        
        test_schema = {
            "input_topic": {
                "input/pepeunit": ["test/input/pepeunit"]
            },
            "output_topic": {
                "output/pepeunit": ["test/output/pepeunit"]
            },
            "output_base_topic": {
                "log/pepeunit": ["test/log/pepeunit"],
                "state/pepeunit": ["test/state/pepeunit"]
            }
        }
        
        # Сохраняем тестовые файлы
        with open(env_path, 'w') as f:
            json.dump(test_env, f)
        
        with open(schema_path, 'w') as f:
            json.dump(test_schema, f)
        
        # Создаем клиент
        client = PepeunitClient(env_path, schema_path, log_path)
        
        # Тест 1: Работа с env.json
        print("  ✅ Тест 1: Работа с env.json")
        assert client.get_env_value("COMMIT_VERSION") == "1.0.0"
        client.update_env({"NEW_SETTING": "test_value"})
        assert client.get_env_value("NEW_SETTING") == "test_value"
        
        # Тест 2: Работа с schema.json
        print("  ✅ Тест 2: Работа с schema.json")
        topics = client.get_input_topics()
        assert "test/input/pepeunit" in topics
        
        log_topic = client.get_topic_by_key("log/pepeunit")
        assert log_topic == "test/log/pepeunit"
        
        # Тест 3: Логирование
        print("  ✅ Тест 3: Логирование")
        initial_logs_count = len(client.get_all_logs())
        client.save_log(LogLevel.INFO, "Тестовое сообщение")
        logs = client.get_all_logs()
        assert len(logs) == initial_logs_count + 1
        # Проверяем последний лог
        last_log = logs[-1]
        assert last_log["level"] == "Info"
        assert last_log["text"] == "Тестовое сообщение"
        
        # Тест 4: Генерация состояния
        print("  ✅ Тест 4: Генерация состояния устройства")
        state = client.generate_device_state()
        assert "millis" in state
        assert "commit_version" in state
        assert state["commit_version"] == "1.0.0"
        
        # Тест 5: Поиск топиков
        print("  ✅ Тест 5: Поиск топиков")
        result = client.search_topic_in_schema("test")
        assert result is not None
        
        print("🎉 Все тесты прошли успешно!")

def test_mqtt_interface():
    """Тестирует MQTT интерфейс"""
    print("\n🧪 Тестирование MQTT интерфейса...")
    
    from src.pepeunit_client import MQTTClientInterface
    
    class TestMQTTClient(MQTTClientInterface):
        def __init__(self):
            self.published_messages = []
            self.subscribed_topics = []
        
        def publish(self, topic: str, payload: str) -> None:
            self.published_messages.append((topic, payload))
        
        def subscribe(self, topics: list) -> None:
            self.subscribed_topics.extend(topics)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        env_path = os.path.join(temp_dir, "env.json")
        schema_path = os.path.join(temp_dir, "schema.json")
        log_path = os.path.join(temp_dir, "log.json")
        
        # Создаем пустые файлы
        for path in [env_path, schema_path, log_path]:
            with open(path, 'w') as f:
                json.dump({}, f)
        
        # Создаем тестовую схему
        test_schema = {
            "output_base_topic": {
                "log/pepeunit": ["test/log/pepeunit"]
            }
        }
        with open(schema_path, 'w') as f:
            json.dump(test_schema, f)
        
        # Создаем клиент с MQTT
        mqtt_client = TestMQTTClient()
        client = PepeunitClient(env_path, schema_path, log_path, mqtt_client=mqtt_client)
        
        # Тест отправки сообщения
        client.send_mqtt_message("test/topic", "test message")
        assert len(mqtt_client.published_messages) == 1
        assert mqtt_client.published_messages[0] == ("test/topic", "test message")
        
        # Тест подписки на топики
        client.subscribe_to_topics(["topic1", "topic2"])
        assert "topic1" in mqtt_client.subscribed_topics
        assert "topic2" in mqtt_client.subscribed_topics
        
        # Тест отправки лога через MQTT
        initial_messages = len(mqtt_client.published_messages)
        client.send_log_via_mqtt(LogLevel.INFO, "MQTT log test")
        assert len(mqtt_client.published_messages) == initial_messages + 1
        
        print("  ✅ MQTT интерфейс работает корректно!")

def test_rest_interface():
    """Тестирует REST интерфейс"""
    print("\n🧪 Тестирование REST интерфейса...")
    
    from src.pepeunit_client import RESTClientInterface
    
    class TestRESTClient(RESTClientInterface):
        def __init__(self):
            self.requests = []
        
        def get(self, url: str, headers: dict = None) -> dict:
            self.requests.append(("GET", url, headers))
            return {"test": "data"}
        
        def post(self, url: str, data: dict = None, headers: dict = None) -> dict:
            self.requests.append(("POST", url, headers, data))
            return {"status": "success"}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        env_path = os.path.join(temp_dir, "env.json")
        schema_path = os.path.join(temp_dir, "schema.json")
        log_path = os.path.join(temp_dir, "log.json")
        
        # Создаем пустые файлы
        for path in [env_path, schema_path, log_path]:
            with open(path, 'w') as f:
                json.dump({}, f)
        
        # Создаем клиент с REST
        rest_client = TestRESTClient()
        client = PepeunitClient(env_path, schema_path, log_path, rest_client=rest_client)
        
        # Тест скачивания и обновления
        client.download_and_update_env("http://test.com/env")
        assert len(rest_client.requests) == 1
        assert rest_client.requests[0][0] == "GET"
        assert rest_client.requests[0][1] == "http://test.com/env"
        
        client.download_and_update_schema("http://test.com/schema")
        assert len(rest_client.requests) == 2
        
        client.download_and_update_firmware("http://test.com/firmware")
        assert len(rest_client.requests) == 3
        
        print("  ✅ REST интерфейс работает корректно!")

if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_mqtt_interface()
        test_rest_interface()
        print("\n🎉 Все тесты завершены успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
