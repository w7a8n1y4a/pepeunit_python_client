#!/usr/bin/env python3
"""
Пример базового использования PepeunitClient
"""

import json
from pepeunit_client import PepeunitClient, LogLevel

def main():
    # Создаем клиент с базовыми путями
    client = PepeunitClient(
        env_path="config/env.json",
        schema_path="config/schema.json", 
        log_path="logs/log.json"
    )
    
    # Работа с env.json
    print("=== Работа с env.json ===")
    
    # Получаем значение из env
    commit_version = client.get_env_value("COMMIT_VERSION", "unknown")
    print(f"Версия коммита: {commit_version}")
    
    # Обновляем env
    client.update_env({
        "COMMIT_VERSION": "1.0.0",
        "PING_INTERVAL": 30,
        "STATE_SEND_INTERVAL": 300
    })
    
    # Работа с schema.json
    print("\n=== Работа с schema.json ===")
    
    # Получаем входные топики
    input_topics = client.get_input_topics()
    print(f"Входные топики: {input_topics}")
    
    # Ищем топик по ключу
    log_topic = client.get_topic_by_key("log/pepeunit")
    print(f"Топик для логов: {log_topic}")
    
    # Работа с логами
    print("\n=== Работа с логами ===")
    
    client.save_log(LogLevel.INFO, "Приложение запущено")
    client.save_log(LogLevel.DEBUG, "Отладочная информация")
    client.save_log(LogLevel.ERROR, "Произошла ошибка")
    
    # Получаем все логи
    logs = client.get_all_logs()
    print(f"Количество логов: {len(logs)}")
    for log in logs[-3:]:  # Показываем последние 3 лога
        print(f"  {log['level']}: {log['text']}")
    
    # Генерация состояния устройства
    print("\n=== Состояние устройства ===")
    
    state = client.generate_device_state()
    print(f"Состояние устройства: {json.dumps(state, indent=2)}")
    
    # Обновление прошивки
    print("\n=== Обновление прошивки ===")
    
    # Пример обновления прошивки (файл должен существовать)
    # success = client.update_firmware("firmware_update.zip")
    # print(f"Обновление прошивки: {'успешно' if success else 'ошибка'}")

if __name__ == "__main__":
    main()
