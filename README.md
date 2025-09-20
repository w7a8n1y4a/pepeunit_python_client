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
from pepeunit_client import PepeunitClient, LogLevel, MQTTClientInterface
import paho.mqtt.client as mqtt

class MyMQTTClient(MQTTClientInterface):
    def publish(self, topic: str, payload: str) -> None:
        # реализация публикации
    
    def subscribe(self, topics: list) -> None:
        # реализация подписки

client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    mqtt_client=MyMQTTClient()
)

# Отправка через MQTT
client.send_mqtt_message("test/topic", "Hello!")
client.send_log_via_mqtt(LogLevel.INFO, "Лог через MQTT")
```

### 3. С REST клиентом

Добавляет возможность работы с REST API:

```python
from pepeunit_client import PepeunitClient, RESTClientInterface

class MyRESTClient(RESTClientInterface):
    def get(self, url: str, headers: dict = None) -> dict:
        # реализация GET запроса
    
    def post(self, url: str, data: dict = None, headers: dict = None) -> dict:
        # реализация POST запроса

client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    rest_client=MyRESTClient()
)
```

### 4. Полный сценарий (MQTT + REST)

Объединяет все возможности:

```python
client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    mqtt_client=MyMQTTClient(),
    rest_client=MyRESTClient()
)
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

- `paho-mqtt` - для поддержки MQTT
- `httpx` - для поддержки REST API

## Лицензия

AGPL-3.0-or-later