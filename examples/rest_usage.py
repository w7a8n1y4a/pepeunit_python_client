#!/usr/bin/env python3
"""
Пример использования PepeunitClient с REST API
"""

import json
from pepeunit_client import PepeunitClient, LogLevel, RESTClientInterface

class SimpleRESTClient(RESTClientInterface):
    """Простая реализация REST клиента для примера"""
    
    def get(self, url: str, headers: dict = None) -> dict:
        """Имитация GET запроса"""
        print(f"🌐 REST GET: {url}")
        if headers:
            print(f"   Headers: {headers}")
        
        # Имитируем ответы в зависимости от URL
        if "env" in url:
            return {
                "COMMIT_VERSION": "2.0.0",
                "PING_INTERVAL": 60,
                "STATE_SEND_INTERVAL": 600
            }
        elif "schema" in url:
            return {
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
        elif "firmware" in url:
            return {"status": "downloaded", "size": 1024000}
        else:
            return {"status": "ok", "data": "test"}
    
    def post(self, url: str, data: dict = None, headers: dict = None) -> dict:
        """Имитация POST запроса"""
        print(f"🌐 REST POST: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        if headers:
            print(f"   Headers: {headers}")
        return {"status": "success"}

def main():
    # Создаем REST клиент
    rest_client = SimpleRESTClient()
    
    # Создаем PepeunitClient с REST
    client = PepeunitClient(
        env_path="config/env.json",
        schema_path="config/schema.json",
        log_path="logs/log.json",
        rest_client=rest_client
    )
    
    print("=== REST функционал ===")
    
    # Скачиваем и обновляем env.json
    print("\n--- Обновление env.json ---")
    success = client.download_and_update_env(
        "https://api.pepeunit.com/units/env/12345",
        {"Authorization": "Bearer token123"}
    )
    print(f"Обновление env.json: {'успешно' if success else 'ошибка'}")
    
    # Скачиваем и обновляем schema.json
    print("\n--- Обновление schema.json ---")
    success = client.download_and_update_schema(
        "https://api.pepeunit.com/units/schema/12345",
        {"Authorization": "Bearer token123"}
    )
    print(f"Обновление schema.json: {'успешно' if success else 'ошибка'}")
    
    # Скачиваем и обновляем прошивку
    print("\n--- Обновление прошивки ---")
    success = client.download_and_update_firmware(
        "https://api.pepeunit.com/units/firmware/12345",
        {"Authorization": "Bearer token123"}
    )
    print(f"Обновление прошивки: {'успешно' if success else 'ошибка'}")
    
    # Показываем обновленные данные
    print("\n--- Обновленные данные ---")
    env_data = client.get_env_data()
    print(f"env.json: {json.dumps(env_data, indent=2)}")
    
    schema_data = client.get_schema_data()
    print(f"schema.json: {json.dumps(schema_data, indent=2)}")

if __name__ == "__main__":
    main()
