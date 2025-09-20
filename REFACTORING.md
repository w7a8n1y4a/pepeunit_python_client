# Рефакторинг Pepeunit Python Client

## Обзор изменений

Большой файл `pepeunit_client.py` (627 строк) был разделен на отдельные модули для лучшей организации кода и поддержки.

## Новая структура модулей

### 📁 `constants.py`
- `ReservedEnvVariableName` - константы для зарезервированных переменных окружения
- `LogLevel` - перечисление уровней логирования

### 📁 `settings.py`
- `Settings` - класс для типизированной работы с настройками из env.json

### 📁 `file_manager.py`
- `FileManager` - класс для работы с файлами и архивами

### 📁 `interfaces.py`
- `MQTTClientInterface` - абстрактный интерфейс для MQTT клиента
- `RESTClientInterface` - абстрактный интерфейс для REST клиента

### 📁 `mqtt_client.py`
- `PepeunitMQTTClient` - каркас для MQTT клиента с базовой функциональностью

### 📁 `rest_client.py`
- `PepeunitRESTClient` - каркас для REST клиента с базовой функциональностью

### 📁 `pepeunit_client.py` (основной)
- `PepeunitClient` - основной клиент для работы с Pepeunit Unit Storage
- Содержит только основную логику работы с конфигурационными файлами и логированием
- Размер уменьшен с 627 до 307 строк

## Преимущества рефакторинга

1. **Модульность**: Каждый модуль отвечает за свою область функциональности
2. **Читаемость**: Код стал более структурированным и понятным
3. **Поддержка**: Легче вносить изменения в отдельные компоненты
4. **Тестирование**: Можно тестировать каждый модуль независимо
5. **Расширяемость**: Легко добавлять новые реализации клиентов

## Использование

### Импорт всех компонентов
```python
from pepeunit_client import (
    PepeunitClient,
    LogLevel,
    Settings,
    FileManager,
    PepeunitMQTTClient,
    PepeunitRESTClient
)
```

### Импорт отдельных модулей
```python
from pepeunit_client.constants import LogLevel
from pepeunit_client.settings import Settings
from pepeunit_client.mqtt_client import PepeunitMQTTClient
```

## Каркасы клиентов

### MQTT Client
`PepeunitMQTTClient` предоставляет базовый каркас с методами:
- `connect()` / `disconnect()`
- `publish()` / `subscribe()` / `unsubscribe()`
- `set_message_handler()` / `remove_message_handler()`
- `loop_start()` / `loop_stop()`

### REST Client
`PepeunitRESTClient` предоставляет базовый каркас с методами:
- `connect()` / `disconnect()`
- `get()` / `post()` / `put()` / `delete()`
- `download_file()` / `upload_file()`
- `set_auth_token()` / `remove_auth_token()`

## Следующие шаги

1. Реализовать конкретные реализации MQTT клиента (например, на основе paho-mqtt)
2. Реализовать конкретные реализации REST клиента (например, на основе requests)
3. Добавить примеры использования новых модулей
4. Обновить документацию с примерами

## Обратная совместимость

Все публичные API остались неизменными. Существующий код будет работать без изменений.
