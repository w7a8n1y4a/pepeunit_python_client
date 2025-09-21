import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pepeunit_client import PepeunitClient, LogLevel


def custom_message_handler(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")


def example_1_basic():
    print("\n=== Сценарий 1: Базовый клиент ===")
    
    client = PepeunitClient(
        env_path="env.json",
        schema_path="schema.json", 
        log_path="log.json",
        mqtt_enabled=False,
        rest_enabled=False
    )
    
    print(f"Unit UUID: {client.unit_uuid}")
    print(f"Settings: {client.settings.PEPEUNIT_URL}")
    
    env_values = client.get_env_values()
    schema_values = client.get_schema_values()
    
    client.log(LogLevel.INFO, "Basic client example started")
    
    state = client.get_system_state()
    print(f"System state: {json.dumps(state, indent=2)}")
    
    topics = client.get_subscription_topics()
    print(f"Available input topics: {topics}")
    
    print("Базовый клиент работает!")


def example_2_mqtt_only():
    print("\n=== Сценарий 2: Клиент с MQTT ===")
    
    try:
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json", 
            mqtt_enabled=True,
            rest_enabled=False,
            message_handler=custom_message_handler
        )
        
        client.connect_mqtt()
        
        client.publish_to_topic("output/pepeunit", "Hello from MQTT client!")
        
        client.start_state_publishing()
        
        client.subscribe_to_topics("input/pepeunit")
        
        print("MQTT клиент подключен и работает!")
        
        time.sleep(5)
        
        client.disconnect_mqtt()
        
    except Exception as e:
        print(f"Ошибка MQTT клиента: {e}")
        print("MQTT функциональность недоступна (возможно не установлен paho-mqtt)")


def example_3_rest_only():
    print("\n=== Сценарий 3: Клиент с REST ===")
    
    try:
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=False,
            rest_enabled=True
        )
        
        test_state = {"temperature": 25.5, "humidity": 60}
        
        try:
            client.set_state_storage(client.unit_uuid, test_state)
            retrieved_state = client.get_state_storage(client.unit_uuid)
            print(f"Сохранено и получено состояние: {retrieved_state}")
        except Exception as e:
            print(f"Unit Storage недоступен: {e}")
        
        try:
            env_path = client.download_env()
            print(f"Environment скачан в: {env_path}")
            
            schema_path = client.download_schema()
            print(f"Schema скачана в: {schema_path}")
        except Exception as e:
            print(f"Скачивание недоступно: {e}")
        
        print("REST клиент работает!")
        
    except Exception as e:
        print(f"Ошибка REST клиента: {e}")
        print("REST функциональность недоступна (возможно не установлен httpx)")


def example_4_full_functionality():
    print("\n=== Сценарий 4: Полная функциональность ===")
    
    try:
        client = PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=True,
            rest_enabled=True,
            message_handler=custom_message_handler
        )
        
        client.start()
        
        print("Клиент с полной функциональностью запущен!")
        
        try:
            client.publish_to_topic("output/pepeunit", "Full client working!")
            
            state = client.get_system_state()
            client.set_state_storage(client.unit_uuid, state)
            
        except Exception as e:
            print(f"Некоторые функции недоступны: {e}")
        
        print("Работаем 10 секунд...")
        time.sleep(10)
        
        client.stop()
        
    except Exception as e:
        print(f"Ошибка полного клиента: {e}")
        print("Полная функциональность недоступна")


def example_5_context_manager():
    print("\n=== Сценарий 5: Контекстный менеджер ===")
    
    try:
        with PepeunitClient(
            env_path="env.json",
            schema_path="schema.json",
            log_path="log.json",
            mqtt_enabled=True,
            rest_enabled=True,
            message_handler=custom_message_handler
        ) as client:
            
            print("Клиент автоматически запущен в контекстном менеджере")
            
            client.log(LogLevel.INFO, "Context manager example")
            print(f"Unit UUID: {client.unit_uuid}")
            
            time.sleep(3)
            
        print("Клиент автоматически остановлен при выходе из контекста")
        
    except Exception as e:
        print(f"Ошибка в контекстном менеджере: {e}")


def main():
    print("=== Демонстрация PepeunitClient ===")
    print("Примеры всех сценариев использования")
    
    required_files = ["env.json", "schema.json", "log.json"]
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"Внимание: файл {file_path} не найден")
    
    try:
        example_1_basic()
        example_2_mqtt_only()
        example_3_rest_only() 
        example_4_full_functionality()
        example_5_context_manager()
        
    except KeyboardInterrupt:
        print("\nПрерывание выполнения пользователем")
    except Exception as e:
        print(f"Общая ошибка: {e}")
    
    print("\n=== Демонстрация завершена ===")


if __name__ == "__main__":
    main()
