#!/usr/bin/env python3
"""
Тест для проверки типизированных настроек Settings
"""

import os
import tempfile
import json
from pathlib import Path
from src.pepeunit_client import PepeunitClient, LogLevel, Settings, ReservedEnvVariableName

def test_settings_class():
    """Тестирует класс Settings"""
    print("🧪 Тестирование класса Settings...")
    
    # Тест создания Settings с зарезервированными переменными
    settings_data = {
        ReservedEnvVariableName.PEPEUNIT_URL: "api.test.com",
        ReservedEnvVariableName.MQTT_PORT: 1883,
        ReservedEnvVariableName.PING_INTERVAL: 30,
        "CUSTOM_DEBUG": True,
        "CUSTOM_VALUE": 42
    }
    
    settings = Settings(**settings_data)
    
    # Проверяем зарезервированные переменные
    assert settings.PEPEUNIT_URL == "api.test.com"
    assert settings.MQTT_PORT == 1883
    assert settings.PING_INTERVAL == 30
    
    # Проверяем пользовательские переменные
    assert settings.CUSTOM_DEBUG == True
    assert settings.CUSTOM_VALUE == 42
    
    # Проверяем методы
    reserved = settings.get_reserved_variables()
    assert ReservedEnvVariableName.PEPEUNIT_URL in reserved
    assert ReservedEnvVariableName.MQTT_PORT in reserved
    
    custom = settings.get_custom_variables()
    assert "CUSTOM_DEBUG" in custom
    assert "CUSTOM_VALUE" in custom
    
    # Проверяем обновление
    settings.update(PING_INTERVAL=60, CUSTOM_NEW=100)
    assert settings.PING_INTERVAL == 60
    assert settings.CUSTOM_NEW == 100
    
    print("  ✅ Settings работает корректно!")

def test_pepeunit_client_with_settings():
    """Тестирует PepeunitClient с типизированными настройками"""
    print("\n🧪 Тестирование PepeunitClient с Settings...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем env.json с полным набором настроек
        env_data = {
            ReservedEnvVariableName.PEPEUNIT_URL: "api.pepeunit.com",
            ReservedEnvVariableName.HTTP_TYPE: "https",
            ReservedEnvVariableName.MQTT_URL: "mqtt.pepeunit.com",
            ReservedEnvVariableName.MQTT_PORT: 1883,
            ReservedEnvVariableName.PEPEUNIT_TOKEN: "test-token-123",
            ReservedEnvVariableName.COMMIT_VERSION: "1.0.0",
            ReservedEnvVariableName.PING_INTERVAL: 30,
            ReservedEnvVariableName.STATE_SEND_INTERVAL: 300,
            ReservedEnvVariableName.DELAY_PUB_MSG: 1,
            ReservedEnvVariableName.PUBLISH_LOG_LEVEL: "Info",
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
        
        # Тест 1: Проверка типизированного доступа к настройкам
        print("  ✅ Тест 1: Типизированный доступ к настройкам")
        assert client.settings.PEPEUNIT_URL == "api.pepeunit.com"
        assert client.settings.MQTT_PORT == 1883
        assert client.settings.CUSTOM_DEBUG_MODE == True
        assert client.settings.CUSTOM_MAX_RETRIES == 5
        
        # Тест 2: Проверка методов получения настроек
        print("  ✅ Тест 2: Методы получения настроек")
        reserved = client.get_reserved_settings()
        assert ReservedEnvVariableName.PEPEUNIT_URL in reserved
        assert ReservedEnvVariableName.MQTT_PORT in reserved
        
        custom = client.get_custom_settings()
        assert "CUSTOM_DEBUG_MODE" in custom
        assert "CUSTOM_MAX_RETRIES" in custom
        
        # Тест 3: Обновление настроек
        print("  ✅ Тест 3: Обновление настроек")
        client.update_env({
            ReservedEnvVariableName.PING_INTERVAL: 60,
            "CUSTOM_NEW_FEATURE": "enabled"
        })
        
        assert client.settings.PING_INTERVAL == 60
        assert client.settings.CUSTOM_NEW_FEATURE == "enabled"
        
        # Тест 4: Генерация состояния устройства с настройками
        print("  ✅ Тест 4: Генерация состояния устройства")
        state = client.generate_device_state()
        assert state['commit_version'] == "1.0.0"
        
        # Тест 5: Работа с логами
        print("  ✅ Тест 5: Работа с логами")
        client.save_log(LogLevel.INFO, f"Debug режим: {client.settings.CUSTOM_DEBUG_MODE}")
        logs = client.get_all_logs()
        assert len(logs) > 0
        
        print("  ✅ PepeunitClient с Settings работает корректно!")

def test_reserved_variable_names():
    """Тестирует константы зарезервированных переменных"""
    print("\n🧪 Тестирование ReservedEnvVariableName...")
    
    # Проверяем, что все константы определены
    expected_vars = [
        'PEPEUNIT_URL', 'PEPEUNIT_APP_PREFIX', 'PEPEUNIT_API_ACTUAL_PREFIX',
        'HTTP_TYPE', 'MQTT_URL', 'MQTT_PORT', 'PEPEUNIT_TOKEN',
        'SYNC_ENCRYPT_KEY', 'SECRET_KEY', 'COMMIT_VERSION',
        'PING_INTERVAL', 'STATE_SEND_INTERVAL', 'DELAY_PUB_MSG', 'PUBLISH_LOG_LEVEL'
    ]
    
    for var_name in expected_vars:
        assert hasattr(ReservedEnvVariableName, var_name)
        assert getattr(ReservedEnvVariableName, var_name) == var_name
    
    print("  ✅ ReservedEnvVariableName работает корректно!")

if __name__ == "__main__":
    try:
        test_settings_class()
        test_pepeunit_client_with_settings()
        test_reserved_variable_names()
        print("\n🎉 Все тесты типизированных настроек прошли успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
