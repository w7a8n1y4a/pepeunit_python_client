# Pepeunit Python Client

Мультиплатформенная библиотека для работы с Pepeunit Unit Storage. Поддерживает конфигурационные файлы, MQTT, REST API и логирование.

## Установка

```bash
pip install pepeunit-client
```

## Сценарии использования

### 1. Базовый сценарий (без MQTT и REST)

Основной функционал работы с файлами конфигурации и логами:

```python
from pepeunit_client import PepeunitClient, LogLevel

client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json", 
    log_path="logs/log.json"
)

# Работа с конфигурацией
client.update_env({"COMMIT_VERSION": "1.0.0"})
version = client.get_env_value("COMMIT_VERSION")

# Работа с логами
client.save_log(LogLevel.INFO, "Приложение запущено")

# Генерация состояния устройства
state = client.generate_device_state()
```

### 2. С MQTT клиентом

Добавляет возможность отправки сообщений и подписки на топики:

```python
from pepeunit_client import PepeunitClient, LogLevel, MQTTClient

# Создание MQTT клиента на основе paho-mqtt
mqtt_client = MQTTClient(
    host="mqtt.example.com",
    port=1883,
    username="your-token"
)

client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    mqtt_client=mqtt_client
)

# Подключение к MQTT брокеру
mqtt_client.connect()

# Отправка через MQTT
client.send_mqtt_message("test/topic", "Hello!")
client.send_log_via_mqtt(LogLevel.INFO, "Лог через MQTT")

# Подписка на топики
topics = client.get_input_topics()
client.subscribe_to_topics(topics)
```

### 3. С REST клиентом

Добавляет возможность работы с REST API:

```python
from pepeunit_client import PepeunitClient, RESTClient

# Создание REST клиента на основе httpx
rest_client = RESTClient(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer your-token"},
    timeout=30.0
)

client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    rest_client=rest_client
)

# Выполнение HTTP запросов
response = rest_client.get("/api/data")
response = rest_client.post("/api/data", json_data={"key": "value"})
response = rest_client.put("/api/data/1", json_data={"key": "updated"})
response = rest_client.delete("/api/data/1")
```

### 4. Полный сценарий (MQTT + REST)

Объединяет все возможности:

```python
from pepeunit_client import PepeunitClient, LogLevel, MQTTClient, RESTClient

# Создание клиентов
mqtt_client = MQTTClient(
    host="mqtt.example.com",
    port=1883,
    username="your-token"
)

rest_client = RESTClient(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer your-token"}
)

# Создание PepeunitClient с обоими клиентами
client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    mqtt_client=mqtt_client,
    rest_client=rest_client
)

# Подключение к MQTT
mqtt_client.connect()

# Полный функционал доступен
client.send_mqtt_message("test/topic", "Hello!")
client.send_log_via_mqtt(LogLevel.INFO, "Лог через MQTT")
response = rest_client.get("/api/status")
```

## Тестирование

Запуск всех тестов:
```bash
pytest tests/
```

Запуск конкретного теста:
```bash
pytest tests/test_pepeunit_client.py::TestPepeunitClientInitialization::test_init_without_clients
```

Запуск с подробным выводом:
```bash
pytest -v tests/
```

## Требования

- Python 3.8+
- psutil (опционально, для генерации состояния устройства)

### Опциональные зависимости

- `paho-mqtt>=1.6.0` - для поддержки MQTT клиента
- `httpx>=0.24.0` - для поддержки REST клиента

### Установка с зависимостями

```bash
# Только MQTT
pip install pepeunit-client[mqtt]

# Только REST
pip install pepeunit-client[rest]

# Все зависимости
pip install pepeunit-client[all]
```

## Встроенные клиенты

Библиотека включает готовые реализации клиентов:

- **MQTTClient** - MQTT клиент на основе paho-mqtt
- **RESTClient** - REST клиент на основе httpx

Эти клиенты реализуют соответствующие интерфейсы и готовы к использованию без дополнительной настройки.

## Лицензия

AGPL-3.0-or-later