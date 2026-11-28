# Client Framework for Pepeunit

<div align="center">
    <img align="center" src="https://pepeunit.com/images/pepeunit-og.jpg"  width="640" height="320">
</div>

A cross-platform Python library for integrating with the PepeUnit IoT platform. This library provides MQTT and REST client functionality for managing device communications, configurations, and state management.

## Installation

Requires Python 3.12 or newer. The package includes the REST and MQTT clients and installs HTTPX and Paho MQTT as dependencies.

```bash
pip install pepeunit-client
```

## Usage Example

Create a Unit from the [universal test Unit](https://git.pepemoss.com/pepe/pepeunit/units/universal_test_unit) repository and copy its `.env` from the firmware archive into `example/`. Run the example from a checkout with the package installed.

```bash
cd example
python basic.py
```

The example fetches `io_topics.yml` on connect, exchanges MQTT counter messages, and writes logs to `log.ndjson`. It also demonstrates Unit Storage, linked UnitIO queries, and AES-GCM.

## API Reference

### PepeunitClient

Main client class for interacting with the PepeUnit platform.

| Method | Description |
|--------|-------------|
| `get_system_state()` | Returns system state information (memory, CPU frequency, timestamp, version) |
| `set_mqtt_input_handler(handler)` | Sets a custom handler for incoming MQTT messages |
| `download_env(file_path)` | Downloads the device `.env` and applies it when saved to the client's active settings file |
| `connect()` | Fetches IO topics and connects to the MQTT broker |
| `refresh_io_topics()` | Fetches `io_topics.yml` and replaces MQTT subscriptions |
| `set_state_storage(state)` | Saves a string to Unit Storage |
| `get_state_storage()` | Returns the stored string |
| `update_device_program(archive_path)` | Extracts and applies update archive to the device |
| `publish_to_topics(topic_key, message)` | Publishes message to topics by topic key |
| `run_main_cycle()` | Runs the main application cycle (blocking) |
| `set_output_handler(output_handler)` | Sets a custom handler for output operations |
| `set_custom_update_handler(custom_update_handler)` | Sets a handler called with `(client, payload)` for firmware updates |
| `stop_main_cycle()` | Stops the running main cycle |

The server sends commands as JSON objects with a `command` field (`Update`, `EnvUpdate`, `SchemaUpdate`, `LogSync`, or `Reset`). `Update` also carries `pu_commit_version`. For compiled firmware, install a custom update handler to use the `compiled_firmware_link` in the payload.

`SchemaUpdate` fetches `io_topics.yml` and updates the MQTT subscriptions and output addresses. The client reapplies the latest input subscriptions on reconnect.

`EnvUpdate` applies the typed values to `client.settings` and keeps the installed `PU_COMMIT_VERSION` until firmware is applied. REST requests use the updated settings on the next call. MQTT reads the current token on each connection attempt. Broker host, port, and keepalive are read when `connect()` is called.

### Logger

The logger writes one JSON object per line to its NDJSON file and publishes JSON batches on the `log` output.

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

### IOTopics

`client.io_topics` provides the Unit's MQTT addresses in `domain/uuid` format and their QoS levels.

| Method | Description |
|--------|-------------|
| `input_name(topic)` | Returns the name for an input MQTT address |

**Properties**

| Property | Description |
|----------|-------------|
| `input` | Maps input names to entries with `topic` and `qos` |
| `output` | Maps output names to entries with `topic` and `qos` |

### Settings

Configuration management for PepeUnit client.

| Method | Description |
|--------|-------------|
| `load_from_file()` | Loads settings from the environment file |

**Properties**

| Property | Description |
|----------|-------------|
| `unit_uuid` | Extracts and returns unit UUID from auth token |

### FileManager

Parses the typed `.env` supplied by Pepeunit.

| Method | Description |
|--------|-------------|
| `read_env(file_path)` | Reads the device `.env` and decodes settings into their original types |
| `parse_env(content)` | Decodes the contents of a device `.env` file |

### PepeunitMqttClient

MQTT client implementation for PepeUnit.

| Method | Description |
|--------|-------------|
| `connect()` | Connects to MQTT broker and starts message loop |
| `disconnect()` | Disconnects from MQTT broker and stops message loop |
| `set_input_handler(handler)` | Sets handler function for incoming MQTT messages |
| `set_subscriptions(topics)` | Applies a mapping of input MQTT addresses to QoS levels |
| `publish(topic, message, qos=0)` | Publishes a message with the specified QoS |

### PepeunitRestClient

REST API client for PepeUnit server.

| Method | Description |
|--------|-------------|
| `download_update(file_path)` | Downloads firmware update archive |
| `download_env(file_path)` | Downloads the device `.env` from `GET /units/env/{uuid}` |
| `get_io_topics()` | Fetches and decodes `GET /units/io_topics/{uuid}` |
| `set_state_storage(state)` | Saves a string to Unit Storage |
| `get_state_storage()` | Returns the stored string |
| `get_input_by_output(topic, limit=100, offset=0)` | Returns the linked inputs in `unit_ios` |
| `get_units_by_ios(unit_io_uuids, limit=100, offset=0)` | Returns units filtered by UnitIO UUIDs |

### AesGcmCipher

Use a Base64-encoded key of 16, 24, or 32 bytes.

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
| `BaseInputTopicType` | `UPDATE` | Update command topic |
| `BaseInputTopicType` | `ENV_UPDATE` | Environment update command topic |
| `BaseInputTopicType` | `SCHEMA_UPDATE` | IO topics update command topic |
| `BaseInputTopicType` | `LOG_SYNC` | Log synchronization command topic |
| `BaseInputTopicType` | `RESET` | Restart command topic |
| `BaseOutputTopicType` | `LOG` | Log output topic |
| `BaseOutputTopicType` | `STATE` | State output topic |
| `RestartMode` | `RESTART_EXEC` | Restart using os.execv (replaces process) |
| `RestartMode` | `ENV_TOPICS_ONLY` | Reload env and IO topics without restart |
| `RestartMode` | `NO_RESTART` | Extract archive without restarting the process |
