# Pepeunit Python Client

Мультиплатформенная библиотека для работы с Pepeunit Unit Storage. Поддерживает работу с конфигурационными файлами, MQTT, REST API и логированием.

## Возможности

- ✅ Работа с `env.json` - конфигурационные настройки
- ✅ Работа с `schema.json` - схема топиков MQTT
- ✅ Работа с `log.json` - логирование
- ✅ Обновление прошивки устройства
- ✅ Генерация состояния устройства
- ✅ Опциональная поддержка MQTT клиента
- ✅ Опциональная поддержка REST клиента
- ✅ Мультиплатформенность (Python 3.8+)

## Установка

### Базовая установка
```bash
pip install pepeunit-client
```

### С MQTT поддержкой
```bash
pip install pepeunit-client[mqtt]
```

### С REST поддержкой
```bash
pip install pepeunit-client[rest]
```

### Полная установка
```bash
pip install pepeunit-client[all]
```

## Быстрый старт

### Базовое использование

```python
from pepeunit_client import PepeunitClient, LogLevel

# Создаем клиент
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

### С MQTT поддержкой

```python
from pepeunit_client import PepeunitClient, LogLevel, MQTTClientInterface
import paho.mqtt.client as mqtt

class MyMQTTClient(MQTTClientInterface):
    def __init__(self):
        self.client = mqtt.Client()
        # настройка подключения...
    
    def publish(self, topic: str, payload: str) -> None:
        self.client.publish(topic, payload)
    
    def subscribe(self, topics: list) -> None:
        for topic in topics:
            self.client.subscribe(topic)

# Создаем клиент с MQTT
mqtt_client = MyMQTTClient()
client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    mqtt_client=mqtt_client
)

# Отправка через MQTT
client.send_mqtt_message("test/topic", "Hello!")
client.send_log_via_mqtt(LogLevel.INFO, "Лог через MQTT")
```

### С REST поддержкой

```python
from pepeunit_client import PepeunitClient, RESTClientInterface
import httpx

class MyRESTClient(RESTClientInterface):
    def get(self, url: str, headers: dict = None) -> dict:
        response = httpx.get(url, headers=headers)
        return response.json()
    
    def post(self, url: str, data: dict = None, headers: dict = None) -> dict:
        response = httpx.post(url, json=data, headers=headers)
        return response.json()

# Создаем клиент с REST
rest_client = MyRESTClient()
client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    rest_client=rest_client
)

# Скачивание и обновление
client.download_and_update_env("https://api.example.com/env")
client.download_and_update_schema("https://api.example.com/schema")
client.download_and_update_firmware("https://api.example.com/firmware")
```

## API Документация

### PepeunitClient

#### Инициализация
```python
PepeunitClient(
    env_path: str,                    # Путь до env.json
    schema_path: str,                 # Путь до schema.json
    log_path: str,                    # Путь до log.json
    mqtt_client: MQTTClientInterface = None,  # Опциональный MQTT клиент
    rest_client: RESTClientInterface = None   # Опциональный REST клиент
)
```

#### Работа с env.json
- `update_env(env_dict)` - обновить из словаря
- `update_env_from_file(file_path)` - обновить из файла
- `get_env_value(key, default)` - получить значение по ключу
- `get_env_data()` - получить все данные

#### Работа с schema.json
- `update_schema(schema_dict)` - обновить из словаря
- `update_schema_from_file(file_path)` - обновить из файла
- `get_schema_value(key, default)` - получить значение по ключу
- `get_schema_data()` - получить все данные

#### Работа с топиками
- `get_input_topics()` - получить список входных топиков
- `get_topic_by_key(key)` - получить топик по ключу
- `search_topic_in_schema(node_uuid)` - найти топик по node_uuid

#### Логирование
- `save_log(level, message)` - сохранить лог
- `get_all_logs()` - получить все логи
- `clear_logs()` - очистить логи

#### MQTT функции (если клиент передан)
- `send_mqtt_message(topic, message)` - отправить сообщение
- `subscribe_to_topics(topics)` - подписаться на топики
- `send_log_via_mqtt(level, message, save_to_file)` - отправить лог через MQTT

#### REST функции (если клиент передан)
- `download_and_update_env(url, headers)` - скачать и обновить env.json
- `download_and_update_schema(url, headers)` - скачать и обновить schema.json
- `download_and_update_firmware(url, headers)` - скачать и обновить прошивку

#### Другие функции
- `update_firmware(archive_path)` - обновить прошивку из архива
- `generate_device_state()` - сгенерировать состояние устройства

### LogLevel

```python
LogLevel.DEBUG
LogLevel.INFO
LogLevel.WARNING
LogLevel.ERROR
LogLevel.CRITICAL
```

## Примеры

Смотрите папку `examples/` для подробных примеров использования:

- `basic_usage.py` - базовое использование
- `mqtt_usage.py` - использование с MQTT
- `rest_usage.py` - использование с REST API

## Требования

- Python 3.8+
- psutil (опционально, для генерации состояния устройства)

### Опциональные зависимости

- `paho-mqtt` - для MQTT поддержки
- `httpx` - для REST API поддержки

## Лицензия

AGPL-3.0-or-later

## Поддержка

- Домашняя страница: https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client
- Issues: https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client/-/issues
