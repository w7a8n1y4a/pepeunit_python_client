# PepeUnit Python Client

A cross-platform Python library for integrating with the PepeUnit IoT platform. This library provides MQTT and REST client functionality for managing device communications, configurations, and state management.

## Installation

```bash
# Install minimal version (no MQTT/REST dependencies)
pip install pepeunit-client

# Install with MQTT support
pip install pepeunit-client[mqtt]

# Install with REST support
pip install pepeunit-client[rest]

# Install with all features
pip install pepeunit-client[all]
```

## Examples

### Basic Usage

```python
import time
from pepeunit_client import PepeunitClient, RestartMode
from pepeunit_client.enums import SearchTopicType, SearchScope

# Global variable to track last message send time
last_output_send_time = 0


def handle_input_messages(client: PepeunitClient, msg: bytes):
    try:
        topic_parts = msg.topic.split("/")

        # topic with format domain.com/+/pepeunit
        if len(topic_parts) == 3:
            # find topic name in schema, by topic with struct domain.com/+/pepeunit or domain.com/+
            topic_name = client.schema.find_topic_by_unit_node(
                msg.topic, SearchTopicType.FULL_NAME, SearchScope.INPUT
            )

            if topic_name == "input/pepeunit":
                value = msg.payload.decode()
                try:
                    value = int(value)

                    # example logic
                    if value == 0:
                        client.logger.info(f"Get message from input/pepeunit topics {value}")
                    else:
                        # send value to all topic by name
                        client.publish_to_topics("output/pepeunit", str(value))

                except ValueError:
                    client.logger.error(f"Value is not a number: {value}")

    except Exception as e:
        client.logger.error(f"Error in mqtt_input_handler: {e}")


def handle_output_messages(client: PepeunitClient):
    global last_output_send_time
    current_time = time.time()
    
    # Send data every MESSAGE_SEND_INTERVAL seconds, similar to _base_mqtt_output_handler
    if current_time - last_output_send_time >= client.settings.DELAY_PUB_MSG:
        # message example
        message = '12.45'
        
        client.logger.info(f"Send message to output/pepeunit topics: {message}")

        # Try to publish to sensor output topics
        client.publish_to_topics("output/pepeunit", message)
        
        # Update the last message send time
        last_output_send_time = current_time


def main():
    # Initialize the PepeUnit client
    client = PepeunitClient(
        env_file_path="env.json",
        schema_file_path="schema.json",
        log_file_path="log.json",
        enable_mqtt=True,
        enable_rest=True,
        cycle_speed=1.0,  # 1 second cycle
        restart_mode=RestartMode.RESTART_EXEC  # Default restart behavior
    )
    
    # Log startup
    client.logger.debug("PepeUnit client created")
    client.logger.debug(f"Device UUID: {client.unit_uuid}")
    
    # Set up message handlers
    client.set_mqtt_input_handler(handle_input_messages)

    # Connect to mqtt broker, 
    client.mqtt_client.connect()

    # Subscribe to all input topics from schema, be sure to after connecting with the broker
    client.subscribe_all_schema_topics()

    # Run the main cycle with set output handler
    client.run_main_cycle(handle_output_messages)


if __name__ == "__main__":
    main()

```

### Advanced Usage Examples

#### Different Restart Modes

```python
from pepeunit_client import PepeunitClient, RestartMode

# Production environment - fast restart (default)
production_client = PepeunitClient(
    "env.json", "schema.json", "log.json",
    enable_mqtt=True, enable_rest=True,
    restart_mode=RestartMode.RESTART_EXEC
)

# High-reliability system - subprocess restart
reliable_client = PepeunitClient(
    "env.json", "schema.json", "log.json", 
    enable_mqtt=True, enable_rest=True,
    restart_mode=RestartMode.RESTART_POPEN
)

# Configuration-only updates (IoT sensors)
config_client = PepeunitClient(
    "env.json", "schema.json", "log.json",
    enable_mqtt=True, enable_rest=True, 
    restart_mode=RestartMode.ENV_SCHEMA_ONLY
)

# Development/testing environment
dev_client = PepeunitClient(
    "env.json", "schema.json", "log.json",
    enable_mqtt=True, enable_rest=True,
    restart_mode=RestartMode.NO_RESTART
)

# Trigger updates with different behaviors
production_client.update_device_program("update.tar.gz")  # Fast restart (default)
reliable_client.update_device_program("update.tar.gz")    # Subprocess restart  
config_client.update_device_program("config.tar.gz")      # Config only
dev_client.update_device_program("test.tar.gz")           # Extract only
```

#### Conditional Restart Logic

```python
from pepeunit_client import PepeunitClient, RestartMode
import os

def create_adaptive_client(env_path: str) -> PepeunitClient:
    """Create client with restart mode based on environment"""
    
    # Check if running in container or systemd
    if os.path.exists("/.dockerenv"):
        # Container environment - use default fast restart
        restart_mode = RestartMode.RESTART_EXEC
    elif os.environ.get("SYSTEMD_SERVICE"):
        # Systemd service - use subprocess restart for reliability
        restart_mode = RestartMode.RESTART_POPEN
    elif os.environ.get("DEVELOPMENT"):
        # Development mode - manual control
        restart_mode = RestartMode.NO_RESTART
    else:
        # Default production behavior - fast restart
        restart_mode = RestartMode.RESTART_EXEC
    
    return PepeunitClient(
        env_path, "schema.json", "log.json",
        enable_mqtt=True, enable_rest=True,
        restart_mode=restart_mode
    )

# Usage
client = create_adaptive_client("env.json")
```

## API Reference

### PepeunitClient

The main client class providing all functionality for PepeUnit integration.

#### Constructor

```python
PepeunitClient(
    env_file_path: str,
    schema_file_path: str,
    log_file_path: str,
    enable_mqtt: bool = False,
    enable_rest: bool = False,
    mqtt_client: Optional[AbstractPepeunitMqttClient] = None,
    rest_client: Optional[AbstractPepeunitRestClient] = None,
    cycle_speed: float = 0.1,
    restart_mode: RestartMode = RestartMode.RESTART_EXEC
)
```

#### Properties

- **`unit_uuid`** (str): Device UUID extracted from JWT token
- **`settings`** (Settings): Configuration settings manager
- **`schema`** (SchemaManager): MQTT topic schema manager  
- **`logger`** (Logger): Logging system with file and MQTT output
- **`mqtt_client`** (AbstractPepeunitMqttClient): MQTT client instance
- **`rest_client`** (AbstractPepeunitRestClient): REST client instance

#### Core Methods

- **`set_cycle_speed(speed: float)`**: Set main cycle execution speed
- **`get_system_state() -> Dict[str, Any]`**: Get current system status (memory, CPU, etc.)
- **`update_device_program(archive_path: str)`**: Update device program from tar.gz archive
- **`run_main_cycle(output_handler: Optional[Callable] = None)`**: Start main application loop
- **`stop_main_cycle()`**: Stop main application loop
- **`set_output_handler(output_handler: Callable)`**: Set custom output message handler

#### Restart Modes

The `restart_mode` parameter controls how the device behaves when `update_device_program()` is called:

- **`RestartMode.RESTART_POPEN`**: Creates new process via `subprocess.Popen()`, then exits current process
  - ✅ Full process isolation and reliable restart
  - ⚠️ Brief gap between old and new process
  
- **`RestartMode.RESTART_EXEC`** (default): Replaces current process using `os.execv()`
  - ✅ Fast restart, preserves process ID
  - ⚠️ May not release all resources properly
  
- **`RestartMode.ENV_SCHEMA_ONLY`**: Updates configuration without restarting
  - ✅ No downtime, fast configuration updates
  - ⚠️ Code changes not applied, only env.json and schema.json
  
- **`RestartMode.NO_RESTART`**: Only extracts archive, no updates or restarts
  - ✅ Full control over update process
  - ⚠️ Manual intervention required

**Usage Examples:**

```python
from pepeunit_client import PepeunitClient, RestartMode

# Fast restart preserving process ID
client = PepeunitClient(
    "env.json", "schema.json", "log.json",
    restart_mode=RestartMode.RESTART_EXEC
)

# Configuration-only updates (no downtime)
client = PepeunitClient(
    "env.json", "schema.json", "log.json", 
    restart_mode=RestartMode.ENV_SCHEMA_ONLY
)

# Manual update control
client = PepeunitClient(
    "env.json", "schema.json", "log.json",
    restart_mode=RestartMode.NO_RESTART
)
```

#### MQTT Methods (require `enable_mqtt=True`)

- **`set_mqtt_input_handler(handler: Callable)`**: Set custom input message handler
- **`subscribe_all_schema_topics()`**: Subscribe to all schema-defined topics
- **`publish_to_topics(topic_key: str, message: str)`**: Publish message to topic group

#### REST Methods (require `enable_rest=True`)

- **`download_update(archive_path: str)`**: Download firmware update archive
- **`download_env(file_path: str)`**: Download environment configuration
- **`download_schema(file_path: str)`**: Download topic schema configuration
- **`set_state_storage(state: Dict[str, Any])`**: Upload state to PepeUnit storage
- **`get_state_storage() -> Dict[str, Any]`**: Retrieve state from PepeUnit storage

#### Combined Methods (require both MQTT and REST)

- **`perform_update()`**: Complete update cycle: download, extract, and apply

### PepeunitClient.mqtt_client

MQTT client interface implementing `AbstractPepeunitMqttClient`.

#### Methods

- **`connect()`**: Connect to MQTT broker using configuration
- **`disconnect()`**: Disconnect from MQTT broker
- **`subscribe_topics(topics: List[str])`**: Subscribe to specific MQTT topics
- **`publish(topic: str, message: str)`**: Publish message to specific topic
- **`set_input_handler(handler: Callable)`**: Set message handler for incoming messages

### PepeunitClient.rest_client

REST client interface implementing `AbstractPepeunitRestClient`.

#### Methods

- **`download_update(unit_uuid: str, file_path: str)`**: Download firmware update
- **`download_env(unit_uuid: str, file_path: str)`**: Download environment config
- **`download_schema(unit_uuid: str, file_path: str)`**: Download schema config
- **`set_state_storage(unit_uuid: str, state: Dict[str, Any])`**: Store device state
- **`get_state_storage(unit_uuid: str) -> Dict[str, Any]`**: Retrieve device state

### PepeunitClient.settings

Configuration manager for environment variables and settings.

#### Attributes

- **`PEPEUNIT_URL`** (str): PepeUnit server URL
- **`PEPEUNIT_APP_PREFIX`** (str): Application prefix path
- **`PEPEUNIT_API_ACTUAL_PREFIX`** (str): API version prefix
- **`HTTP_TYPE`** (str): HTTP protocol type (http/https)
- **`MQTT_URL`** (str): MQTT broker URL
- **`MQTT_PORT`** (int): MQTT broker port
- **`PEPEUNIT_TOKEN`** (str): Authentication JWT token
- **`SYNC_ENCRYPT_KEY`** (str): Encryption key for synchronization
- **`SECRET_KEY`** (str): Application secret key
- **`COMMIT_VERSION`** (str): Current application version
- **`PING_INTERVAL`** (int): Ping interval in seconds
- **`STATE_SEND_INTERVAL`** (int): State broadcast interval in seconds
- **`DELAY_PUB_MSG`** (int): Message publication delay interval in seconds
- **`MINIMAL_LOG_LEVEL`** (str): Minimum logging level

#### Methods

- **`load_from_file()`**: Reload settings from env.json file
- **`get_env_values() -> Dict[str, Any]`**: Get all environment values as dictionary
- **`update_env_file(new_env_file_path: str)`**: Replace current env file with new one
- **`update(**kwargs)`**: Update specific settings programmatically

### PepeunitClient.schema

Schema manager for MQTT topic configuration.

#### Properties

- **`input_base_topic`** (Dict[str, List[str]]): Base input topics configuration
- **`output_base_topic`** (Dict[str, List[str]]): Base output topics configuration  
- **`input_topic`** (Dict[str, List[str]]): Custom input topics configuration
- **`output_topic`** (Dict[str, List[str]]): Custom output topics configuration

#### Methods

- **`update_from_file()`**: Reload schema from schema.json file
- **`update_schema(schema_dict: Dict[str, Any])`**: Update schema with new configuration
- **`find_topic_by_unit_node(search_value: str, search_type: SearchTopicType, search_scope: SearchScope) -> Optional[str]`**: Find topics by UUID or name

#### Usage Examples

```python
from pepeunit_client.enums import SearchTopicType, SearchScope

# Access topic lists by key
input_topics = client.schema.input_topic["input/pepeunit"]
output_topics = client.schema.output_topic["output/pepeunit"]

# Get base system topics
state_topics = client.schema.output_base_topic["state/pepeunit"]

# Find topic by name or UUID
topic_name = client.schema.find_topic_by_unit_node(
    "domain.com/<uuid>/pepeunit", 
    SearchTopicType.FULL_NAME, 
    SearchScope.INPUT
)
```

### Available Enums

#### RestartMode

Controls device restart behavior during updates:

```python
from pepeunit_client import RestartMode

RestartMode.RESTART_POPEN    # Subprocess restart
RestartMode.RESTART_EXEC     # Default: fast restart with os.execv()
RestartMode.ENV_SCHEMA_ONLY  # Config-only updates
RestartMode.NO_RESTART       # Manual control
```

#### SearchTopicType & SearchScope

For topic discovery in schema:

```python
from pepeunit_client.enums import SearchTopicType, SearchScope

# Search by full topic name or UUID
SearchTopicType.FULL_NAME
SearchTopicType.UNIT_NODE_UUID

# Limit search scope
SearchScope.ALL      # Search both input and output
SearchScope.INPUT    # Input topics only  
SearchScope.OUTPUT   # Output topics only
```

### PepeunitClient.logger

Logging system with file storage and optional MQTT publishing.

#### Log Levels

- **`debug(message: str)`**: Debug level logging
- **`info(message: str)`**: Info level logging  
- **`warning(message: str)`**: Warning level logging
- **`error(message: str)`**: Error level logging
- **`critical(message: str)`**: Critical level logging

#### Methods

- **`get_full_log() -> list`**: Retrieve complete log history from file
- **`reset_log()`**: Clear all log entries

#### Usage Examples

```python
# Log messages at different levels
client.logger.info("Device started successfully")
client.logger.warning("Low battery detected")
client.logger.error("Sensor connection failed")

# Get complete log history
log_history = client.logger.get_full_log()
```

## Error Handling

The library uses standard Python exceptions and does not suppress errors. Key exception types:

- **`ValueError`**: Invalid configuration or parameter values
- **`RuntimeError`**: Feature not enabled (e.g., REST/MQTT not available)
- **`ImportError`**: Missing optional dependencies (paho-mqtt, httpx)

## Dependencies

### Core Dependencies
- `psutil>=5.8.0` (system monitoring, optional on emscripten)

### Optional Dependencies  
- `paho-mqtt>=1.6.0` (MQTT functionality)
- `httpx>=0.24.0` (REST functionality)

## License

GNU Affero General Public License v3 (AGPL-3.0-or-later)

## Links

- [Homepage](https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client)
- [Issues](https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client/-/issues)
- [Documentation](https://git.pepemoss.com/pepe/pepeunit/libs/pepeunit_python_client/-/wikis)