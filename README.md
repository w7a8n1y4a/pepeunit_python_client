# Pepeunit Python Client

Multi-platform library for working with Pepeunit Unit Storage. Supports configuration files, MQTT, REST API and logging.

## Features

- ✅ Working with `env.json` - configuration settings
- ✅ Working with `schema.json` - MQTT topics schema
- ✅ Working with `log.json` - logging
- ✅ Device state generation
- ✅ Optional MQTT client support
- ✅ Optional REST client support
- ✅ Multi-platform (Python 3.8+)

## Installation

### Basic installation
```bash
pip install pepeunit-client
```

### With MQTT support
```bash
pip install pepeunit-client[mqtt]
```

### With REST support
```bash
pip install pepeunit-client[rest]
```

### Full installation
```bash
pip install pepeunit-client[all]
```

## Quick Start

### Basic usage

```python
from pepeunit_client import PepeunitClient, LogLevel

# Create client
client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json", 
    log_path="logs/log.json"
)

# Working with configuration
client.update_env({"COMMIT_VERSION": "1.0.0"})
version = client.get_env_value("COMMIT_VERSION")

# Working with logs
client.save_log(LogLevel.INFO, "Application started")

# Generate device state
state = client.generate_device_state()
```

### With MQTT support

```python
from pepeunit_client import PepeunitClient, LogLevel, MQTTClientInterface
import paho.mqtt.client as mqtt

class MyMQTTClient(MQTTClientInterface):
    def __init__(self):
        self.client = mqtt.Client()
        # setup connection...
    
    def publish(self, topic: str, payload: str) -> None:
        self.client.publish(topic, payload)
    
    def subscribe(self, topics: list) -> None:
        for topic in topics:
            self.client.subscribe(topic)

# Create client with MQTT
mqtt_client = MyMQTTClient()
client = PepeunitClient(
    env_path="config/env.json",
    schema_path="config/schema.json",
    log_path="logs/log.json",
    mqtt_client=mqtt_client
)

# Send via MQTT
client.send_mqtt_message("test/topic", "Hello!")
client.send_log_via_mqtt(LogLevel.INFO, "Log via MQTT")
```

## API Documentation

### PepeunitClient

#### Initialization
```python
PepeunitClient(
    env_path: str,                    # Path to env.json
    schema_path: str,                 # Path to schema.json
    log_path: str,                    # Path to log.json
    mqtt_client: MQTTClientInterface = None,  # Optional MQTT client
    rest_client: RESTClientInterface = None   # Optional REST client
)
```

#### Working with env.json
- `update_env(env_dict)` - update from dictionary
- `update_env_from_file(file_path)` - update from file
- `get_env_value(key, default)` - get value by key
- `get_env_data()` - get all data

#### Working with schema.json
- `update_schema(schema_dict)` - update from dictionary
- `update_schema_from_file(file_path)` - update from file
- `get_schema_value(key, default)` - get value by key
- `get_schema_data()` - get all data

#### Working with topics
- `get_input_topics()` - get list of input topics
- `get_topic_by_key(key)` - get topic by key
- `search_topic_in_schema(node_uuid)` - find topic by node_uuid

#### Logging
- `save_log(level, message)` - save log
- `get_all_logs()` - get all logs
- `clear_logs()` - clear logs

#### MQTT functions (if client provided)
- `send_mqtt_message(topic, message)` - send message
- `subscribe_to_topics(topics)` - subscribe to topics
- `send_log_via_mqtt(level, message, save_to_file)` - send log via MQTT

#### Other functions
- `generate_device_state()` - generate device state

### LogLevel

```python
LogLevel.DEBUG
LogLevel.INFO
LogLevel.WARNING
LogLevel.ERROR
LogLevel.CRITICAL
```

### Settings

Class for typed work with settings from env.json:

```python
# Create settings
settings = Settings(
    PEPEUNIT_URL="api.example.com",
    MQTT_PORT=1883,
    CUSTOM_DEBUG=True
)

# Access to reserved settings
print(settings.PEPEUNIT_URL)  # "api.example.com"
print(settings.MQTT_PORT)     # 1883

# Access to custom settings
print(settings.CUSTOM_DEBUG)  # True

# Get only reserved settings
reserved = settings.get_reserved_variables()

# Get only custom settings
custom = settings.get_custom_variables()

# Update settings
settings.update(PING_INTERVAL=60, CUSTOM_NEW_VALUE=42)
```

## Requirements

- Python 3.8+
- psutil (optional, for device state generation)

### Optional dependencies

- `paho-mqtt` - for MQTT support
- `httpx` - for REST API support

## License

AGPL-3.0-or-later

## Support

- Homepage: https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client
- Issues: https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client/-/issues