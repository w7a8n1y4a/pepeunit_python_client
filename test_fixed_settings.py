#!/usr/bin/env python3
"""
Тест для проверки исправленных настроек Settings
"""

import os
import tempfile
import json
from pathlib import Path
from src.pepeunit_client import PepeunitClient, LogLevel, Settings, ReservedEnvVariableName

def test_reserved_variables():
    """Тестирует зарезервированные переменные"""
    print("🧪 Тестирование зарезервированных переменных...")
    
    # Проверяем, что все константы соответствуют бэкенду
    expected_vars = [
        'PEPEUNIT_URL', 'HTTP_TYPE', 'PEPEUNIT_APP_PREFIX', 'PEPEUNIT_API_ACTUAL_PREFIX',
        'MQTT_URL', 'MQTT_PORT', 'PEPEUNIT_TOKEN', 'SYNC_ENCRYPT_KEY', 'SECRET_KEY',
        'COMMIT_VERSION', 'PING_INTERVAL', 'STATE_SEND_INTERVAL'
    ]
    
    for var_name in expected_vars:
        assert hasattr(ReservedEnvVariableName, var_name)
        assert getattr(ReservedEnvVariableName, var_name) == var_name
    
    # Проверяем, что лишние переменные удалены
    assert not hasattr(ReservedEnvVariableName, 'DELAY_PUB_MSG')
    assert not hasattr(ReservedEnvVariableName, 'PUBLISH_LOG_LEVEL')
    
    print("  ✅ Зарезервированные переменные корректны!")

def test_settings_reserved_attributes():
    """Тестирует зарезервированные атрибуты Settings"""
    print("\n🧪 Тестирование зарезервированных атрибутов...")
    
    # Создаем Settings с зарезервированными переменными
    settings_data = {
        ReservedEnvVariableName.PEPEUNIT_URL: "api.test.com",
        ReservedEnvVariableName.MQTT_PORT: 1883,
        ReservedEnvVariableName.COMMIT_VERSION: "1.2.3",
        ReservedEnvVariableName.PING_INTERVAL: 30,
        ReservedEnvVariableName.STATE_SEND_INTERVAL: 300
    }
    
    settings = Settings(**settings_data)
    
    # Проверяем, что зарезервированные переменные доступны как атрибуты
    assert settings.PEPEUNIT_URL == "api.test.com"
    assert settings.MQTT_PORT == 1883
    assert settings.COMMIT_VERSION == "1.2.3"
    assert settings.PING_INTERVAL == 30
    assert settings.STATE_SEND_INTERVAL == 300
    
    # Проверяем значения по умолчанию
    assert settings.HTTP_TYPE == "https"  # значение по умолчанию
    assert settings.MQTT_URL == ""  # значение по умолчанию
    
    print("  ✅ Зарезервированные атрибуты работают корректно!")

def test_settings_custom_attributes():
    """Тестирует пользовательские атрибуты Settings"""
    print("\n🧪 Тестирование пользовательских атрибутов...")
    
    # Создаем Settings с пользовательскими переменными
    settings_data = {
        ReservedEnvVariableName.PEPEUNIT_URL: "api.test.com",  # зарезервированная
        ReservedEnvVariableName.COMMIT_VERSION: "1.2.3",  # зарезервированная
        "DELAY_PUB_MSG": 1,  # пользовательская
        "PUBLISH_LOG_LEVEL": "Debug",  # пользовательская
        "CUSTOM_DEBUG": True,  # пользовательская
        "CUSTOM_MAX_RETRIES": 5  # пользовательская
    }
    
    settings = Settings(**settings_data)
    
    # Проверяем зарезервированные атрибуты
    assert settings.PEPEUNIT_URL == "api.test.com"
    assert settings.COMMIT_VERSION == "1.2.3"
    
    # Проверяем пользовательские атрибуты через __getattr__
    assert settings.DELAY_PUB_MSG == 1
    assert settings.PUBLISH_LOG_LEVEL == "Debug"
    assert settings.CUSTOM_DEBUG == True
    assert settings.CUSTOM_MAX_RETRIES == 5
    
    # Проверяем, что несуществующий атрибут вызывает AttributeError
    try:
        _ = settings.NONEXISTENT_ATTRIBUTE
        assert False, "Должно было возникнуть AttributeError"
    except AttributeError:
        pass  # Ожидаемое поведение
    
    print("  ✅ Пользовательские атрибуты работают корректно!")

def test_settings_methods():
    """Тестирует методы Settings"""
    print("\n🧪 Тестирование методов Settings...")
    
    settings_data = {
        ReservedEnvVariableName.PEPEUNIT_URL: "api.test.com",
        ReservedEnvVariableName.MQTT_PORT: 1883,
        "COMMIT_VERSION": "1.2.3",
        "CUSTOM_DEBUG": True
    }
    
    settings = Settings(**settings_data)
    
    # Тест get_reserved_variables()
    reserved = settings.get_reserved_variables()
    assert ReservedEnvVariableName.PEPEUNIT_URL in reserved
    assert ReservedEnvVariableName.MQTT_PORT in reserved
    assert ReservedEnvVariableName.COMMIT_VERSION in reserved
    assert "CUSTOM_DEBUG" not in reserved
    
    # Тест get_custom_variables()
    custom = settings.get_custom_variables()
    assert "CUSTOM_DEBUG" in custom
    assert ReservedEnvVariableName.PEPEUNIT_URL not in custom
    assert ReservedEnvVariableName.MQTT_PORT not in custom
    assert ReservedEnvVariableName.COMMIT_VERSION not in custom
    
    # Тест to_dict()
    all_settings = settings.to_dict()
    assert all_settings[ReservedEnvVariableName.PEPEUNIT_URL] == "api.test.com"
    assert all_settings[ReservedEnvVariableName.COMMIT_VERSION] == "1.2.3"
    
    # Тест update()
    settings.update(
        **{ReservedEnvVariableName.PING_INTERVAL: 60},  # зарезервированная
        CUSTOM_NEW_VALUE=42  # пользовательская
    )
    assert settings.PING_INTERVAL == 60
    assert settings.CUSTOM_NEW_VALUE == 42
    
    # Тест get()
    assert settings.get(ReservedEnvVariableName.PEPEUNIT_URL) == "api.test.com"
    assert settings.get(ReservedEnvVariableName.COMMIT_VERSION) == "1.2.3"
    assert settings.get("NONEXISTENT", "default") == "default"
    
    print("  ✅ Методы Settings работают корректно!")

def test_pepeunit_client_with_fixed_settings():
    """Тестирует PepeunitClient с исправленными настройками"""
    print("\n🧪 Тестирование PepeunitClient с исправленными настройками...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем env.json с правильной структурой
        env_data = {
            # Зарезервированные переменные
            ReservedEnvVariableName.PEPEUNIT_URL: "api.pepeunit.com",
            ReservedEnvVariableName.HTTP_TYPE: "https",
            ReservedEnvVariableName.MQTT_URL: "mqtt.pepeunit.com",
            ReservedEnvVariableName.MQTT_PORT: 1883,
            ReservedEnvVariableName.PEPEUNIT_TOKEN: "test-token-123",
            ReservedEnvVariableName.COMMIT_VERSION: "1.0.0",
            ReservedEnvVariableName.PING_INTERVAL: 30,
            ReservedEnvVariableName.STATE_SEND_INTERVAL: 300,
            
            # Пользовательские переменные
            "DELAY_PUB_MSG": 1,
            "PUBLISH_LOG_LEVEL": "Info",
            "CUSTOM_DEBUG_MODE": True,
            "CUSTOM_MAX_RETRIES": 5
        }
        
        env_path = Path(temp_dir) / "env.json"
        with open(env_path, 'w') as f:
            json.dump(env_data, f)
        
        # Создаем schema.json
        schema_data = {
            "output_base_topic": {
                "log/pepeunit": ["test/log/pepeunit"],
                "state/pepeunit": ["test/state/pepeunit"]
            }
        }
        
        schema_path = Path(temp_dir) / "schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema_data, f)
        
        log_path = Path(temp_dir) / "log.json"
        
        # Создаем клиент
        client = PepeunitClient(str(env_path), str(schema_path), str(log_path))
        
        # Тест 1: Зарезервированные переменные как атрибуты
        print("  ✅ Тест 1: Зарезервированные переменные")
        assert client.settings.PEPEUNIT_URL == "api.pepeunit.com"
        assert client.settings.MQTT_PORT == 1883
        assert client.settings.COMMIT_VERSION == "1.0.0"
        assert client.settings.PING_INTERVAL == 30
        
        # Тест 2: Пользовательские переменные как атрибуты
        print("  ✅ Тест 2: Пользовательские переменные")
        assert client.settings.DELAY_PUB_MSG == 1
        assert client.settings.PUBLISH_LOG_LEVEL == "Info"
        assert client.settings.CUSTOM_DEBUG_MODE == True
        assert client.settings.CUSTOM_MAX_RETRIES == 5
        
        # Тест 3: Методы разделения переменных
        print("  ✅ Тест 3: Разделение переменных")
        reserved = client.get_reserved_settings()
        assert ReservedEnvVariableName.PEPEUNIT_URL in reserved
        assert ReservedEnvVariableName.COMMIT_VERSION in reserved
        
        custom = client.get_custom_settings()
        assert "DELAY_PUB_MSG" in custom
        assert ReservedEnvVariableName.PEPEUNIT_URL not in custom
        assert ReservedEnvVariableName.COMMIT_VERSION not in custom
        
        # Тест 4: Генерация состояния устройства
        print("  ✅ Тест 4: Генерация состояния")
        state = client.generate_device_state()
        assert state['commit_version'] == "1.0.0"  # зарезервированная переменная
        
        # Тест 5: Обновление настроек
        print("  ✅ Тест 5: Обновление настроек")
        client.update_env({
            ReservedEnvVariableName.PING_INTERVAL: 60,  # зарезервированная
            "CUSTOM_NEW_FEATURE": "enabled"  # пользовательская
        })
        
        assert client.settings.PING_INTERVAL == 60
        assert client.settings.CUSTOM_NEW_FEATURE == "enabled"
        
        print("  ✅ PepeunitClient с исправленными настройками работает корректно!")

if __name__ == "__main__":
    try:
        test_reserved_variables()
        test_settings_reserved_attributes()
        test_settings_custom_attributes()
        test_settings_methods()
        test_pepeunit_client_with_fixed_settings()
        print("\n🎉 Все тесты исправленных настроек прошли успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
