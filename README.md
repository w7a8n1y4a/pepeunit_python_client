# Client Framework for Pepeunit

<div align="center">
    <img align="center" src="https://pepeunit.com/pepeunit-og.jpg"  width="640" height="320">
</div>

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

## Usage Example

```python
"""
Basic PepeUnit Client Example

To use this example, simply create a Pepeunit Unit based on the repository https://git.pepemoss.com/pepe/pepeunit/units/universal_test_unit on any instance.

The resulting schema.json and env.json files should be added to the example directory.

This example demonstrates basic usage of the PepeUnit client with both MQTT and REST functionality.
It shows how to:
- Initialize the client with configuration files
- Set up message handlers
- Subscribe to topics
- Run the main application cycle
- Storage api
- Units Nodes api
- Cipher api
"""

import time
from pepeunit_client import PepeunitClient, RestartMode, AesGcmCipher
from pepeunit_client.enums import SearchTopicType, SearchScope

# Global variable to track last message send time
last_output_send_time = 0
inc = 0

def handle_input_messages(client: PepeunitClient, msg):
    try:
        topic_parts = msg.topic.split("/")

        # topic with format domain.com/+/pepeunit
        if len(topic_parts) == 3:
            # find topic name in schema, by topic with struct domain.com/+/pepeunit or domain.com/+
            topic_name = client.schema.find_topic_by_unit_node(
                msg.topic, SearchTopicType.FULL_NAME, SearchScope.INPUT
            )

            if topic_name == "input/pepeunit":
                value = msg.payload
                try:
                    value = int(value)
                    client.logger.debug(f"Get from input/pepeunit: {value}", file_only=True)

                except ValueError:
                    client.logger.error(f"Value is not a number: {value}")

    except Exception as e:
        client.logger.error(f"Input handler error: {e}")


def handle_output_messages(client: PepeunitClient):
    global last_output_send_time
    global inc

    current_time = time.time()
    
    # Send data every MESSAGE_SEND_INTERVAL seconds, similar to _base_mqtt_output_handler
    if current_time - last_output_send_time >= client.settings.DELAY_PUB_MSG:
        # message example
        message = inc
        
        client.logger.debug(f"Send to output/pepeunit: {message}", file_only=True)

        # Try to publish to sensor output topics
        client.publish_to_topics("output/pepeunit", message)
        
        # Update the last message send time
        last_output_send_time = current_time
        inc += 1


def test_set_get_storage(client: PepeunitClient):
    try:
        client.rest_client.set_state_storage('This line is saved in Pepeunit Instance')
        client.logger.info(f"Success set state")
        
        state = client.rest_client.get_state_storage()
        client.logger.info(f"Success get state: {state}")
    except Exception as e:
        client.logger.error(f"Test set get storage failed: {e}")


def test_get_units(client: PepeunitClient):
    try:
        output_topic_urls = client.schema.output_topic.get('output/pepeunit', [])
        if output_topic_urls:
            topic_url = output_topic_urls[0]
            client.logger.info(f"Querying input unit nodes for topic: {topic_url}")
            
            unit_nodes_response = client.rest_client.get_input_by_output(topic_url)
            client.logger.info(f"Found {unit_nodes_response.get('count', 0)} unit nodes")
            
            # Extract UUIDs from response
            unit_node_uuids = [node['uuid'] for node in unit_nodes_response.get('unit_nodes', [])]
            
            if unit_node_uuids:
                # Query units by node UUIDs
                units_response = client.rest_client.get_units_by_nodes(unit_node_uuids)
                client.logger.info(f"Found {units_response.get('count', 0)} units")
                
                for unit in units_response.get('units', []):
                    client.logger.info(f"Unit: {unit.get('name')} (UUID: {unit.get('uuid')})")
    except Exception as e:
        client.logger.warning(f"REST query example failed: {e}")


def test_cipher(client: PepeunitClient):
    try:
        aes_cipher = AesGcmCipher()
        text = "pepeunit cipher test"
        enc = aes_cipher.aes_gcm_encode(text, client.settings.PU_ENCRYPT_KEY)
        client.logger.info(f"Cipher data {enc}")
        dec = aes_cipher.aes_gcm_decode(enc, client.settings.PU_ENCRYPT_KEY)
        client.logger.info(f"Decoded data: {dec}")
    except Exception as e:
        client.logger.error("Cipher test error: {}".format(e))


def main():
    # Initialize the PepeUnit client
    client = PepeunitClient(
        env_file_path="env.json",
        schema_file_path="schema.json",
        log_file_path="log.json",
        enable_mqtt=True,
        enable_rest=True,
        cycle_speed=1.0,  # 1 second cycle
        restart_mode=RestartMode.RESTART_EXEC
    )
    
    # Test work pepeunit storage
    test_set_get_storage(client)

    # Test get edged units by output topic
    test_get_units(client)
    
    # Test AES-GCM cipher
    test_cipher(client)
    
    # Set up message handlers
    client.set_mqtt_input_handler(handle_input_messages)

    # Connect to mqtt broker, 
    client.mqtt_client.connect()

    # Subscribe to all input topics from schema, be sure to after connecting with the broker
    client.subscribe_all_schema_topics()

    # Set output handler
    client.set_output_handler(handle_output_messages)

    # Run the main cycle with set output handler
    client.run_main_cycle()


if __name__ == "__main__":
    main()
```


## API Reference

### PepeunitClient

Main client class for interacting with the PepeUnit platform.

| Method | Description |
|--------|-------------|
| `get_system_state()` | Returns system state information (memory, CPU frequency, timestamp, version) |
| `set_mqtt_input_handler(handler)` | Sets a custom handler for incoming MQTT messages |
| `download_env(file_path)` | Downloads environment configuration from the server |
| `download_schema(file_path)` | Downloads schema configuration from the server |
| `set_state_storage(state)` | Saves state data to the server storage |
| `get_state_storage()` | Retrieves state data from the server storage |
| `update_device_program(archive_path)` | Extracts and applies update archive to the device |
| `subscribe_all_schema_topics()` | Subscribes to all input topics defined in schema |
| `publish_to_topics(topic_key, message)` | Publishes message to topics by topic key |
| `run_main_cycle()` | Runs the main application cycle (blocking) |
| `set_output_handler(output_handler)` | Sets a custom handler for output operations |
| `set_custom_update_handler(custom_update_handler)` | Sets a custom handler for update operations |
| `stop_main_cycle()` | Stops the running main cycle |

### Logger

Logging functionality with file and MQTT output support.

| Method | Description |
|--------|-------------|
| `debug(message, file_only=False)` | Logs a debug-level message |
| `info(message, file_only=False)` | Logs an info-level message |
| `warning(message, file_only=False)` | Logs a warning-level message |
| `error(message, file_only=False)` | Logs an error-level message |
| `critical(message, file_only=False)` | Logs a critical-level message |
| `get_full_log()` | Returns all log entries as a list |
| `iter_log()` | Returns an iterator over log entries |
| `reset_log()` | Clears all log entries |

### SchemaManager

Manages schema data and topic lookups.

| Method | Description |
|--------|-------------|
| `update_from_file()` | Reloads schema data from file |
| `find_topic_by_unit_node(search_value, search_type, search_scope)` | Finds topic name by unit node UUID or full name |

**Properties:**

| Property | Description |
|----------|-------------|
| `input_base_topic` | Returns dictionary of base input topics |
| `output_base_topic` | Returns dictionary of base output topics |
| `input_topic` | Returns dictionary of input topics |
| `output_topic` | Returns dictionary of output topics |

### Settings

Configuration management for PepeUnit client.

| Method | Description |
|--------|-------------|
| `load_from_file()` | Loads settings from the environment file |

**Properties:**

| Property | Description |
|----------|-------------|
| `unit_uuid` | Extracts and returns unit UUID from auth token |

### FileManager

Static utility class for file operations.

| Method | Description |
|--------|-------------|
| `read_json(file_path)` | Reads and parses JSON file |
| `write_json(file_path, data, indent=4)` | Writes data to JSON file |
| `copy_file(source_path, destination_path)` | Copies a file from source to destination |
| `file_exists(file_path)` | Checks if file exists |
| `create_directory(directory_path)` | Creates directory (with parents if needed) |
| `extract_tar_gz(archive_path, extract_path)` | Extracts tar.gz archive |
| `extract_pepeunit_archive(file_path, extract_path)` | Extracts PepeUnit-specific compressed archive |
| `copy_directory_contents(source_path, destination_path)` | Copies all contents from source to destination directory |
| `remove_directory(directory_path)` | Removes directory and all its contents |
| `append_ndjson_with_limit(file_path, item, max_lines)` | Appends item to NDJSON file with line limit |
| `iter_ndjson(file_path)` | Returns iterator over NDJSON file entries |
| `trim_ndjson(file_path, max_lines)` | Trims NDJSON file to maximum number of lines |

### PepeunitMqttClient

MQTT client implementation for PepeUnit.

| Method | Description |
|--------|-------------|
| `connect()` | Connects to MQTT broker and starts message loop |
| `disconnect()` | Disconnects from MQTT broker and stops message loop |
| `set_input_handler(handler)` | Sets handler function for incoming MQTT messages |
| `subscribe_topics(topics)` | Subscribes to a list of MQTT topics |
| `publish(topic, message)` | Publishes message to specified MQTT topic |

### PepeunitRestClient

REST API client for PepeUnit server.

| Method | Description |
|--------|-------------|
| `download_update(file_path)` | Downloads firmware update archive |
| `download_env(file_path)` | Downloads environment configuration file |
| `download_schema(file_path)` | Downloads schema configuration file |
| `set_state_storage(state)` | Saves state to server storage |
| `get_state_storage()` | Retrieves state from server storage |
| `get_input_by_output(topic, limit=100, offset=0)` | Gets input unit nodes connected to output topic |
| `get_units_by_nodes(unit_node_uuids, limit=100, offset=0)` | Gets units by their node UUIDs |

### AesGcmCipher

The key can be 16, 24, or 32 bits long.

Method | Description
--- | ---
`aes_gcm_encode(data: str, key: str) -> str` | Encrypts text and returns `base64(nonce).base64(cipher)`.
`aes_gcm_decode(data: str, key: str) -> str` | Decrypts encoded string back to plaintext.

### Enums

| Entity | Key | Description |
|--------|-----|-------------|
| `LogLevel` | `DEBUG` | Debug level logging |
| `LogLevel` | `INFO` | Information level logging |
| `LogLevel` | `WARNING` | Warning level logging |
| `LogLevel` | `ERROR` | Error level logging |
| `LogLevel` | `CRITICAL` | Critical level logging |
| `SearchTopicType` | `UNIT_NODE_UUID` | Search by unit node UUID |
| `SearchTopicType` | `FULL_NAME` | Search by full topic name |
| `SearchScope` | `ALL` | Search in all topics |
| `SearchScope` | `INPUT` | Search only in input topics |
| `SearchScope` | `OUTPUT` | Search only in output topics |
| `DestinationTopicType` | `INPUT_BASE_TOPIC` | Base input topic type |
| `DestinationTopicType` | `OUTPUT_BASE_TOPIC` | Base output topic type |
| `DestinationTopicType` | `INPUT_TOPIC` | Regular input topic type |
| `DestinationTopicType` | `OUTPUT_TOPIC` | Regular output topic type |
| `BaseInputTopicType` | `UPDATE_PEPEUNIT` | Update command topic |
| `BaseInputTopicType` | `ENV_UPDATE_PEPEUNIT` | Environment update command topic |
| `BaseInputTopicType` | `SCHEMA_UPDATE_PEPEUNIT` | Schema update command topic |
| `BaseInputTopicType` | `LOG_SYNC_PEPEUNIT` | Log synchronization command topic |
| `BaseOutputTopicType` | `LOG_PEPEUNIT` | Log output topic |
| `BaseOutputTopicType` | `STATE_PEPEUNIT` | State output topic |
| `RestartMode` | `RESTART_POPEN` | Restart using subprocess.Popen |
| `RestartMode` | `RESTART_EXEC` | Restart using os.execv (replaces process) |
| `RestartMode` | `ENV_SCHEMA_ONLY` | Update only env and schema without restart |
| `RestartMode` | `NO_RESTART` | Extract archive without restart or updates |
