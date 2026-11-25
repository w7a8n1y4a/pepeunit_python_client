"""
Basic PepeUnit Client Example

To use this example, simply create a Pepeunit Unit based on the repository https://git.pepemoss.com/pepe/pepeunit/units/universal_test_unit on any instance.

Copy .env from the firmware archive into the example directory. The SDK fetches IO topics when it connects.

This example demonstrates basic usage of the PepeUnit client with both MQTT and REST functionality.
It shows how to:
- Initialize the client with configuration files
- Set up message handlers
- Subscribe to topics
- Run the main application cycle
- Storage api
- UnitIO API
- Cipher api
"""

import time
from pepeunit_client import PepeunitClient, RestartMode, AesGcmCipher

# Global variable to track last message send time
last_output_send_time = 0
inc = 0

def handle_input_messages(client: PepeunitClient, msg):
    if client.io_topics.input_name(msg.topic) != "input_counter":
        return
    try:
        value = int(msg.payload)
    except ValueError:
        client.logger.error(f"Value is not a number: {msg.payload!r}")
        return
    client.logger.debug(f"Get from input_counter: {value}", file_only=True)


def handle_output_messages(client: PepeunitClient):
    global last_output_send_time
    global inc

    current_time = time.time()
    
    # Send data every MESSAGE_SEND_INTERVAL seconds, similar to _base_mqtt_output_handler
    if current_time - last_output_send_time >= client.settings.DELAY_PUB_MSG:
        # message example
        message = inc
        
        client.logger.debug(f"Send to output_counter: {message}", file_only=True)

        # Try to publish to sensor output topics
        client.publish_to_topics("output_counter", message)
        
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
        output = client.io_topics.output.get("output_counter")
        if output is None:
            return
        response = client.rest_client.get_input_by_output(output.topic)
        input_uuids = [io["uuid"] for io in response["unit_ios"]]
        for unit in client.rest_client.get_units_by_ios(input_uuids)["units"]:
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
        env_file_path=".env",
        log_file_path="log.json",
        enable_mqtt=True,
        enable_rest=True,
        cycle_speed=1.0,  # 1 second cycle
        restart_mode=RestartMode.RESTART_EXEC
    )
    
    # Test work pepeunit storage
    test_set_get_storage(client)

    # Test AES-GCM cipher
    test_cipher(client)
    
    # Set up message handlers
    client.set_mqtt_input_handler(handle_input_messages)

    client.connect()
    test_get_units(client)

    # Set output handler
    client.set_output_handler(handle_output_messages)

    # Run the main cycle with set output handler
    client.run_main_cycle()


if __name__ == "__main__":
    main()
