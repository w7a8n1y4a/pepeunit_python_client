#!/usr/bin/env python3
"""
Тест для проверки рефакторинга с FileManager
"""

import os
import tempfile
import json
from pathlib import Path
from src.pepeunit_client import PepeunitClient, LogLevel, FileManager

def test_file_manager():
    """Тестирует FileManager отдельно"""
    print("🧪 Тестирование FileManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.json"
        
        # Тест сохранения и загрузки JSON
        test_data = {"key": "value", "number": 42}
        FileManager.save_json_file(test_file, test_data)
        
        loaded_data = FileManager.load_json_file(test_file)
        assert loaded_data == test_data
        
        # Тест определения формата архива
        assert FileManager.get_archive_format("test.zip") == "zip"
        assert FileManager.get_archive_format("test.tar.gz") == "tgz"
        assert FileManager.get_archive_format("test.tgz") == "tgz"
        assert FileManager.get_archive_format("test.tar") == "tar"
        
        print("  ✅ FileManager работает корректно!")

def test_pepeunit_client_with_file_manager():
    """Тестирует PepeunitClient с новой структурой"""
    print("\n🧪 Тестирование PepeunitClient с FileManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        env_path = os.path.join(temp_dir, "env.json")
        schema_path = os.path.join(temp_dir, "schema.json")
        log_path = os.path.join(temp_dir, "log.json")
        
        # Создаем тестовые данные
        test_env = {
            "COMMIT_VERSION": "2.0.0",
            "PING_INTERVAL": 60,
            "STATE_SEND_INTERVAL": 600
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
        assert client.get_env_value("COMMIT_VERSION") == "2.0.0"
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
        client.save_log(LogLevel.INFO, "Тестовое сообщение с FileManager")
        logs = client.get_all_logs()
        assert len(logs) == initial_logs_count + 1
        
        # Тест 4: Генерация состояния
        print("  ✅ Тест 4: Генерация состояния устройства")
        state = client.generate_device_state()
        assert "millis" in state
        assert "commit_version" in state
        assert state["commit_version"] == "2.0.0"
        
        # Тест 5: Обновление из файла
        print("  ✅ Тест 5: Обновление из файла")
        new_env_file = os.path.join(temp_dir, "new_env.json")
        new_env_data = {"COMMIT_VERSION": "3.0.0", "NEW_FIELD": "new_value"}
        with open(new_env_file, 'w') as f:
            json.dump(new_env_data, f)
        
        client.update_env_from_file(new_env_file)
        assert client.get_env_value("COMMIT_VERSION") == "3.0.0"
        assert client.get_env_value("NEW_FIELD") == "new_value"
        
        print("  ✅ PepeunitClient с FileManager работает корректно!")

def test_file_manager_archive_operations():
    """Тестирует операции с архивами в FileManager"""
    print("\n🧪 Тестирование операций с архивами...")
    
    # Тест подготовки директории обновления
    test_uuid = "test-unit-123"
    update_dir = FileManager.prepare_update_directory(test_uuid)
    assert os.path.exists(update_dir)
    
    # Тест копирования файлов
    source_dir = os.path.join(update_dir, "source")
    dest_dir = os.path.join(update_dir, "dest")
    os.makedirs(source_dir)
    
    test_file = os.path.join(source_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("test content")
    
    FileManager.copy_update_files(source_dir, dest_dir)
    assert os.path.exists(os.path.join(dest_dir, "test.txt"))
    
    print("  ✅ Операции с архивами работают корректно!")

if __name__ == "__main__":
    try:
        test_file_manager()
        test_pepeunit_client_with_file_manager()
        test_file_manager_archive_operations()
        print("\n🎉 Все тесты рефакторинга прошли успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
