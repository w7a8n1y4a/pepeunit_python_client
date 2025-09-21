# PepeunitClient

Мультиплатформенная библиотека для работы с Pepeunit Unit Storage.

## Установка

```bash
pip install pepeunit-client
```

### Опциональные зависимости

Библиотека поддерживает четыре сценария использования с различными наборами зависимостей:

```bash
# Базовая функциональность
pip install pepeunit-client

# С поддержкой MQTT
pip install pepeunit-client[mqtt]

# С поддержкой REST API
pip install pepeunit-client[rest]

# Полная функциональность
pip install pepeunit-client[all]
```

## Сценарии использования

### 1. Базовый клиент (без MQTT и REST)

Минимальная функциональность для работы с файлами конфигурации и логирования:

```python
from pepeunit_client import PepeunitClient, LogLevel

client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json",
    log_path="log.json",
    mqtt_enabled=False,
    rest_enabled=False
)

# Работа с настройками
print(f"Unit UUID: {client.unit_uuid}")
print(f"API URL: {client.settings.PEPEUNIT_URL}")

# Логирование
client.log(LogLevel.INFO, "Application started")

# Состояние системы
state = client.get_system_state()
print(f"System state: {state}")

# Получение топиков для подписки
topics = client.get_subscription_topics()
print(f"Input topics: {topics}")
```

### 2. Клиент с MQTT

Добавляет возможности публикации и подписки на MQTT топики:

```python
from pepeunit_client import PepeunitClient, LogLevel

def message_handler(client, userdata, msg):
    print(f"Received: {msg.topic} - {msg.payload.decode()}")

client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json", 
    log_path="log.json",
    mqtt_enabled=True,
    rest_enabled=False,
    message_handler=message_handler
)

# Подключение к MQTT
client.connect_mqtt()

# Публикация сообщений
client.publish_to_topic("output/pepeunit", "Hello from device!")

# Подписка на топики
client.subscribe_to_topics("input/pepeunit")

# Автоматическая отправка состояния системы
client.start_state_publishing()

# Отключение
client.disconnect_mqtt()
```

### 3. Клиент с REST API

Добавляет возможности работы с REST API и Unit Storage:

```python
from pepeunit_client import PepeunitClient, LogLevel

client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json",
    log_path="log.json",
    mqtt_enabled=False,
    rest_enabled=True
)

# Работа с Unit Storage
device_state = {"temperature": 25.5, "humidity": 60}
client.set_state_storage(client.unit_uuid, device_state)

retrieved_state = client.get_state_storage(client.unit_uuid)
print(f"Saved state: {retrieved_state}")

# Скачивание конфигураций
env_path = client.download_env()
client.update_env_file(env_path)

schema_path = client.download_schema()
client.update_schema_file(schema_path)

# Скачивание обновлений
update_path = client.download_update()
client.update_device_program(update_path)
```

### 4. Полная функциональность (MQTT + REST)

Включает все возможности библиотеки с автоматической обработкой команд обновления:

```python
from pepeunit_client import PepeunitClient, LogLevel

def message_handler(client, userdata, msg):
    print(f"Message received: {msg.topic}")
    # Пользовательская обработка сообщений
    # Системные команды обрабатываются автоматически

# Инициализация с полной функциональностью
client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json",
    log_path="log.json", 
    mqtt_enabled=True,
    rest_enabled=True,
    message_handler=message_handler
)

# Использование контекстного менеджера для автоматического управления
with client:
    print("Клиент запущен, автоматически обрабатывает:")
    print("- Команды обновления через MQTT")
    print("- Скачивание файлов через REST API") 
    print("- Периодическую отправку состояния")
    print("- Синхронизацию логов")
    
    # Основная логика приложения
    client.log(LogLevel.INFO, "Application running with full functionality")
    
    # Клиент автоматически остановится при выходе из контекста
```

## Автоматическая обработка команд

При включении обеих опций (MQTT + REST) клиент автоматически обрабатывает следующие команды через MQTT:

- **update/pepeunit** - полный цикл обновления программы
- **env_update/pepeunit** - обновление файла настроек
- **schema_update/pepeunit** - обновление схемы топиков
- **log_sync/pepeunit** - синхронизация логов

## Структура файлов

### env.json
```json
{
  "PEPEUNIT_URL": "api.pepeunit.dev",
  "PEPEUNIT_APP_PREFIX": "/app", 
  "PEPEUNIT_API_ACTUAL_PREFIX": "/api/v1",
  "HTTP_TYPE": "https",
  "MQTT_URL": "mqtt.pepeunit.dev",
  "MQTT_PORT": 1883,
  "PEPEUNIT_TOKEN": "eyJ...",
  "STATE_SEND_INTERVAL": 300
}
```

### schema.json
```json
{
  "input_base_topic": {
    "update/pepeunit": ["device.domain.com/uuid/update"],
    "env_update/pepeunit": ["device.domain.com/uuid/env_update"]
  },
  "output_base_topic": {
    "state/pepeunit": ["device.domain.com/uuid/state"],
    "log/pepeunit": ["device.domain.com/uuid/log"]
  },
  "input_topic": {
    "input/pepeunit": ["device.domain.com/uuid/input"]
  },
  "output_topic": {
    "output/pepeunit": ["device.domain.com/uuid/output"]
  }
}
```

### log.json
```json
[
  {
    "level": "Info",
    "text": "Application started",
    "create_datetime": "2023-01-01T12:00:00.000000Z"
  }
]
```

## Тестирование

```bash
# Установка зависимостей для тестирования
pip install pytest

# Запуск всех тестов
pytest tests/

# Запуск конкретного набора тестов  
pytest tests/test_pepeunit_client.py -v

# Запуск с покрытием
pytest tests/ --cov=pepeunit_client
```

## Требования

- Python 3.8+
- psutil (для системной информации)
- paho-mqtt (опционально, для MQTT)
- httpx (опционально, для REST API)

## Лицензия

AGPL-3.0-or-later