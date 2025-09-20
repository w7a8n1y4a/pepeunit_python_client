#!/usr/bin/env python3
"""
Пример использования PepeunitClient с MQTT
"""

import json
import time
from pepeunit_client import PepeunitClient, LogLevel, MQTTClientInterface

class SimpleMQTTClient(MQTTClientInterface):
    """Простая реализация MQTT клиента для примера"""
    
    def __init__(self):
        self.connected = False
        self.subscribed_topics = []
    
    def publish(self, topic: str, payload: str) -> None:
        """Имитация отправки сообщения"""
        print(f"📤 MQTT PUBLISH: {topic} -> {payload}")
        self.connected = True
    
    def subscribe(self, topics: list) -> None:
        """Имитация подписки на топики"""
        self.subscribed_topics.extend(topics)
        print(f"📥 MQTT SUBSCRIBE: {topics}")
        self.connected = True

def main():
    # Создаем MQTT клиент
    mqtt_client = SimpleMQTTClient()
    
    # Создаем PepeunitClient с MQTT
    client = PepeunitClient(
        env_path="config/env.json",
        schema_path="config/schema.json",
        log_path="logs/log.json",
        mqtt_client=mqtt_client
    )
    
    print("=== MQTT функционал ===")
    
    # Отправляем сообщение через MQTT
    client.send_mqtt_message("test/topic", "Hello MQTT!")
    
    # Подписываемся на топики
    topics = ["input/test", "input/pepeunit"]
    client.subscribe_to_topics(topics)
    
    # Отправляем лог через MQTT
    client.send_log_via_mqtt(LogLevel.INFO, "Лог отправлен через MQTT")
    
    # Получаем входные топики и подписываемся
    input_topics = client.get_input_topics()
    if input_topics:
        client.subscribe_to_topics(input_topics)
    
    # Отправляем состояние устройства
    state = client.generate_device_state()
    state_topic = client.get_topic_by_key("state/pepeunit")
    if state_topic:
        client.send_mqtt_message(state_topic, json.dumps(state))
    
    print(f"\nMQTT клиент подключен: {mqtt_client.connected}")
    print(f"Подписанные топики: {mqtt_client.subscribed_topics}")

if __name__ == "__main__":
    main()
