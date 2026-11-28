"""Run a Pepeunit Unit using the .env from its firmware archive."""

import time
from pathlib import Path

from paho.mqtt.client import MQTTMessage

from pepeunit_client import AesGcmCipher, PepeunitClient


def handle_input(client: PepeunitClient, message: MQTTMessage) -> None:
    if client.io_topics.input_name(message.topic) != "input_counter":
        return
    try:
        value = int(message.payload)
    except ValueError:
        client.logger.error(f"Expected an integer from input_counter: {message.payload!r}")
        return
    client.logger.debug(f"Received input_counter: {value}", file_only=True)


def show_linked_units(client: PepeunitClient) -> None:
    output = client.io_topics.output.get("output_counter")
    rest = client.rest_client
    if output is None or rest is None:
        return
    inputs = rest.get_input_by_output(output.topic)["unit_ios"]
    units = rest.get_units_by_ios([item["uuid"] for item in inputs])["units"]
    for unit in units:
        client.logger.info(f"Linked Unit {unit['name']} ({unit['uuid']})")


def main() -> None:
    directory = Path(__file__).resolve().parent
    client = PepeunitClient(
        env_file_path=str(directory / ".env"),
        log_file_path=str(directory / "log.ndjson"),
        enable_mqtt=True,
        cycle_speed=1.0,
    )
    last_sent_at: float | None = None
    counter = 0

    def publish_counter(unit: PepeunitClient) -> None:
        nonlocal last_sent_at, counter
        now = time.monotonic()
        interval = unit.settings.DELAY_PUB_MSG
        if last_sent_at is not None and now - last_sent_at < interval:
            return
        unit.publish_to_topics("output_counter", counter)
        unit.logger.debug(f"Sent output_counter: {counter}", file_only=True)
        last_sent_at = now
        counter += 1

    client.set_mqtt_input_handler(handle_input)
    client.set_output_handler(publish_counter)

    client.connect()
    try:
        client.set_state_storage("Pepeunit client example")
        client.logger.info(f"Stored state: {client.get_state_storage()}")
        show_linked_units(client)

        if key := client.settings.PU_ENCRYPT_KEY:
            cipher = AesGcmCipher()
            encrypted = cipher.aes_gcm_encode("Pepeunit cipher example", key)
            decoded = cipher.aes_gcm_decode(encrypted, key)
            client.logger.info(f"Decoded message: {decoded}")

        client.run_main_cycle()
    finally:
        if client.mqtt_client is not None:
            client.mqtt_client.disconnect()


if __name__ == "__main__":
    main()
