#!/usr/bin/env python3
"""
Пример использования типизированных настроек Settings
"""

import os
import tempfile
import json
from pathlib import Path
from pepeunit_client import PepeunitClient, LogLevel, Settings, ReservedEnvVariableName

def main():
    print("⚙️ Примеры использования типизированных настроек")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n📂 Рабочая директория: {temp_dir}")
        
        # ==================== Создание env.json с настройками ====================
        print("\n--- Создание env.json с настройками ---")
        
        # Создаем полный набор настроек как в бэкенде
        env_data = {
            # Зарезервированные переменные
            ReservedEnvVariableName.PEPEUNIT_URL: "api.pepeunit.com",
            ReservedEnvVariableName.HTTP_TYPE: "https",
            ReservedEnvVariableName.PEPEUNIT_APP_PREFIX: "/app",
            ReservedEnvVariableName.PEPEUNIT_API_ACTUAL_PREFIX: "/api/v1",
            ReservedEnvVariableName.MQTT_URL: "mqtt.pepeunit.com",
            ReservedEnvVariableName.MQTT_PORT: 1883,
            ReservedEnvVariableName.PEPEUNIT_TOKEN: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            ReservedEnvVariableName.SYNC_ENCRYPT_KEY: "dGVzdC1lbmNyeXB0LWtleQ==",
            ReservedEnvVariableName.SECRET_KEY: "dGVzdC1zZWNyZXQta2V5",
            ReservedEnvVariableName.COMMIT_VERSION: "1.2.3",
            ReservedEnvVariableName.PING_INTERVAL: 30,
            ReservedEnvVariableName.STATE_SEND_INTERVAL: 300,
            ReservedEnvVariableName.DELAY_PUB_MSG: 1,
            ReservedEnvVariableName.PUBLISH_LOG_LEVEL: "Info",
            
            # Пользовательские переменные
            "CUSTOM_DEBUG_MODE": True,
            "CUSTOM_MAX_RETRIES": 5,
            "CUSTOM_TIMEOUT": 30.5,
            "CUSTOM_FEATURES": ["feature1", "feature2", "feature3"],
            "CUSTOM_CONFIG": {
                "database": {
                    "host": "localhost",
                    "port": 5432
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600
                }
            }
        }
        
        # Сохраняем env.json
        env_path = Path(temp_dir) / "env.json"
        with open(env_path, 'w') as f:
            json.dump(env_data, f, indent=2)
        print(f"✅ env.json создан с {len(env_data)} настройками")
        
        # ==================== Работа с Settings ====================
        print("\n--- Работа с Settings ---")
        
        # Создаем объект Settings
        settings = Settings(**env_data)
        print(f"📊 Settings: {settings}")
        
        # Получаем зарезервированные настройки
        reserved = settings.get_reserved_variables()
        print(f"🔒 Зарезервированные настройки ({len(reserved)}):")
        for key, value in reserved.items():
            print(f"  {key}: {value}")
        
        # Получаем пользовательские настройки
        custom = settings.get_custom_variables()
        print(f"\n🔧 Пользовательские настройки ({len(custom)}):")
        for key, value in custom.items():
            print(f"  {key}: {value}")
        
        # Доступ к конкретным настройкам
        print(f"\n📡 MQTT URL: {settings.MQTT_URL}")
        print(f"🔑 Token: {settings.PEPEUNIT_TOKEN[:20]}...")
        print(f"📦 Версия: {settings.COMMIT_VERSION}")
        print(f"🐛 Debug режим: {settings.CUSTOM_DEBUG_MODE}")
        
        # ==================== Работа с PepeunitClient ====================
        print("\n--- Работа с PepeunitClient ---")
        
        # Создаем схему
        schema_data = {
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
        
        schema_path = Path(temp_dir) / "schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema_data, f)
        
        log_path = Path(temp_dir) / "log.json"
        
        # Создаем клиент
        client = PepeunitClient(str(env_path), str(schema_path), str(log_path))
        
        # Работа с настройками через клиент
        print(f"🌐 Pepeunit URL: {client.settings.PEPEUNIT_URL}")
        print(f"🔌 MQTT Port: {client.settings.MQTT_PORT}")
        print(f"⏱️ Ping Interval: {client.settings.PING_INTERVAL}")
        print(f"📊 State Send Interval: {client.settings.STATE_SEND_INTERVAL}")
        
        # Получаем настройки через методы клиента
        print(f"\n📋 Все настройки через get_env_data():")
        all_settings = client.get_env_data()
        for key, value in list(all_settings.items())[:5]:  # Показываем первые 5
            print(f"  {key}: {value}")
        print(f"  ... и еще {len(all_settings) - 5} настроек")
        
        # Получаем только зарезервированные настройки
        reserved_settings = client.get_reserved_settings()
        print(f"\n🔒 Зарезервированные настройки: {len(reserved_settings)}")
        
        # Получаем только пользовательские настройки
        custom_settings = client.get_custom_settings()
        print(f"🔧 Пользовательские настройки: {len(custom_settings)}")
        
        # ==================== Обновление настроек ====================
        print("\n--- Обновление настроек ---")
        
        # Обновляем зарезервированную настройку
        client.update_env({ReservedEnvVariableName.PING_INTERVAL: 60})
        print(f"✅ Ping Interval обновлен: {client.settings.PING_INTERVAL}")
        
        # Добавляем новую пользовательскую настройку
        client.update_env({"CUSTOM_NEW_FEATURE": "enabled"})
        print(f"✅ Новая пользовательская настройка: {client.settings.CUSTOM_NEW_FEATURE}")
        
        # Обновляем несколько настроек сразу
        client.update_env({
            ReservedEnvVariableName.STATE_SEND_INTERVAL: 600,
            "CUSTOM_BATCH_UPDATE": True,
            "CUSTOM_NEW_VALUE": 42
        })
        print(f"✅ Batch обновление: State Send Interval = {client.settings.STATE_SEND_INTERVAL}")
        print(f"✅ Batch обновление: Custom Batch Update = {client.settings.CUSTOM_BATCH_UPDATE}")
        
        # ==================== Генерация состояния устройства ====================
        print("\n--- Генерация состояния устройства ---")
        
        state = client.generate_device_state()
        print(f"📊 Состояние устройства:")
        print(f"  Версия: {state['commit_version']}")
        print(f"  Время: {state['millis']} мс")
        print(f"  Память свободна: {state['mem_free']} байт")
        
        # ==================== Работа с логами ====================
        print("\n--- Работа с логами ---")
        
        # Логируем с использованием настроек
        client.save_log(LogLevel.INFO, f"Приложение запущено с версией {client.settings.COMMIT_VERSION}")
        client.save_log(LogLevel.DEBUG, f"Debug режим: {client.settings.CUSTOM_DEBUG_MODE}")
        client.save_log(LogLevel.WARNING, f"Ping интервал: {client.settings.PING_INTERVAL} сек")
        
        logs = client.get_all_logs()
        print(f"📝 Создано {len(logs)} записей логов")
        
        print(f"\n🎉 Все примеры работы с настройками выполнены успешно!")

if __name__ == "__main__":
    main()
