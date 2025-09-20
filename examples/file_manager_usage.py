#!/usr/bin/env python3
"""
Пример использования FileManager для работы с файлами и архивами
"""

import os
import tempfile
from pathlib import Path
from pepeunit_client import FileManager

def main():
    print("📁 Примеры использования FileManager")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n📂 Рабочая директория: {temp_dir}")
        
        # ==================== Работа с JSON файлами ====================
        print("\n--- Работа с JSON файлами ---")
        
        # Создаем тестовые данные
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "pepeunit"
            },
            "mqtt": {
                "broker": "mqtt.example.com",
                "port": 1883
            },
            "settings": {
                "debug": True,
                "log_level": "INFO"
            }
        }
        
        # Сохраняем конфигурацию
        config_file = Path(temp_dir) / "config.json"
        FileManager.save_json_file(config_file, config_data)
        print(f"✅ Конфигурация сохранена в {config_file}")
        
        # Загружаем конфигурацию
        loaded_config = FileManager.load_json_file(config_file)
        print(f"✅ Конфигурация загружена: {loaded_config['database']['host']}")
        
        # ==================== Работа с архивами ====================
        print("\n--- Работа с архивами ---")
        
        # Тестируем определение формата архива
        test_files = [
            "firmware.zip",
            "update.tar.gz", 
            "patch.tgz",
            "backup.tar",
            "data.gz",
            "unknown.xyz"
        ]
        
        for filename in test_files:
            format_type = FileManager.get_archive_format(filename)
            print(f"📦 {filename} -> {format_type}")
        
        # ==================== Подготовка обновления ====================
        print("\n--- Подготовка обновления ---")
        
        # Подготавливаем директорию обновления
        unit_uuid = "test-unit-12345"
        update_dir = FileManager.prepare_update_directory(unit_uuid)
        print(f"✅ Директория обновления создана: {update_dir}")
        
        # Создаем тестовые файлы для обновления
        source_dir = os.path.join(update_dir, "source")
        os.makedirs(source_dir, exist_ok=True)
        
        # Создаем файлы обновления
        files_to_create = [
            "main.py",
            "config.json", 
            "requirements.txt",
            "README.md"
        ]
        
        for filename in files_to_create:
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"# Содержимое файла {filename}\n")
                f.write(f"# Версия: 1.0.0\n")
                f.write(f"# Дата: {os.path.basename(temp_dir)}\n")
            print(f"📄 Создан файл: {filename}")
        
        # Копируем файлы обновления
        dest_dir = os.path.join(update_dir, "destination")
        FileManager.copy_update_files(source_dir, dest_dir)
        print(f"✅ Файлы скопированы в {dest_dir}")
        
        # Проверяем, что файлы скопированы
        copied_files = os.listdir(dest_dir)
        print(f"📋 Скопированные файлы: {copied_files}")
        
        # ==================== Работа с логами ====================
        print("\n--- Работа с логами ---")
        
        # Создаем файл логов
        log_data = [
            {
                "level": "INFO",
                "text": "Приложение запущено",
                "create_datetime": "2024-01-01T10:00:00.000Z"
            },
            {
                "level": "DEBUG", 
                "text": "Инициализация модулей",
                "create_datetime": "2024-01-01T10:00:01.000Z"
            },
            {
                "level": "WARNING",
                "text": "Конфигурация не найдена, используются значения по умолчанию",
                "create_datetime": "2024-01-01T10:00:02.000Z"
            }
        ]
        
        log_file = Path(temp_dir) / "app.log.json"
        FileManager.save_json_file(log_file, log_data)
        print(f"✅ Логи сохранены в {log_file}")
        
        # Загружаем и отображаем логи
        loaded_logs = FileManager.load_json_file(log_file)
        print(f"📊 Загружено {len(loaded_logs)} записей логов:")
        for log_entry in loaded_logs:
            print(f"  {log_entry['level']}: {log_entry['text']}")
        
        print(f"\n🎉 Все примеры FileManager выполнены успешно!")

if __name__ == "__main__":
    main()
