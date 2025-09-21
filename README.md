# Pepeunit Python Client

Мультиплатформенная библиотека для работы с Pepeunit Unit Storage.

## Установка

```bash
pip install pepeunit-client
```

## Сценарии использования

### 1. Базовый сценарий (без MQTT и REST)

Работа с конфигурационными файлами и логами:

```python
from pepeunit_client import PepeunitClient, LogLevel

client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json", 
    log_path="log.json"
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
from pepeunit_client import PepeunitClient, LogLevel

# Создание клиента с MQTT (автоматически использует настройки из env.json)
client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json", 
    log_path="log.json",
    use_mqtt=True
)

# Подключение к MQTT брокеру
client.connect_mqtt()

# Отправка через MQTT (на все топики из схемы)
client.send_mqtt_message("output/pepeunit", "Hello World!")
client.send_log_via_mqtt(LogLevel.INFO, "Лог через MQTT")

# Подписка на топики (на все топики из схемы)
client.subscribe_to_topics("input/pepeunit")

# Пользовательский обработчик сообщений
def my_message_handler(topic: str, payload: str):
    print(f"Received: {topic} -> {payload}")

# Установка пользовательского обработчика
client.set_message_handler(my_message_handler)
```

### 3. С REST клиентом

Добавляет возможность работы с REST API:

```python
from pepeunit_client import PepeunitClient

# Создание клиента с REST (автоматически использует настройки из env.json)
client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json",
    log_path="log.json",
    use_rest=True
)

# Скачивание файлов
archive_path = client.download_update()
env_data = client.download_env()
schema_data = client.download_schema()

# Работа с Unit Storage
client.set_state_storage('{"status": "active"}')
state = client.get_state_storage()

# Обновление программы
client.update_device_program(archive_path)
```

### 4. Полный сценарий (MQTT + REST)

Объединяет все возможности:

```python
from pepeunit_client import PepeunitClient, LogLevel

# Создание клиента с обоими клиентами
client = PepeunitClient(
    env_path="env.json",
    schema_path="schema.json",
    log_path="log.json",
    use_mqtt=True,
    use_rest=True
)

# Подключение к MQTT
client.connect_mqtt()

# Пользовательский обработчик сообщений
def my_message_handler(topic: str, payload: str):
    print(f"Received: {topic} -> {payload}")

client.set_message_handler(my_message_handler)

# Полный цикл обновления (MQTT получает команду → REST скачивает → обновляется)
client.perform_update()

# Отправка сообщений
client.send_mqtt_message("output/pepeunit", "Hello World!")

# Работа с Unit Storage
client.set_state_storage('{"status": "active"}')
```

## Тестирование

```bash
# Все тесты
pytest tests/

# Конкретный тест
pytest tests/test_pepeunit_client.py::TestPepeunitClientInitialization::test_init_without_clients

# С подробным выводом
pytest -v tests/
```

## Требования

- Python 3.8+
- psutil (опционально)

### Опциональные зависимости

```bash
# Только MQTT
pip install pepeunit-client[mqtt]

# Только REST
pip install pepeunit-client[rest]

# Все зависимости
pip install pepeunit-client[all]
```

## Лицензия

AGPL-3.0-or-later