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
"""

import time
from pepeunit_client.client import PepeunitClient
from pepeunit_client.enums import SearchTopicType, SearchScope


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
                        client.logger.info(f"PepeUnit is offline {value}")
                    else:
                        # send value to all topic by name
                        client.publish_to_topics("output/pepeunit", str(value))

                except ValueError:
                    client.logger.error(f"Value is not a number: {value}")

    except Exception as e:
        client.logger.error(f"Error in mqtt_input_handler: {e}")


def handle_output_messages(client: PepeunitClient):
    current_time = time.time()
    
    # Send data every DELAY_PUB_MSG seconds, DELAY_PUB_MSG this is a user variable
    if current_time - client.previous_cycle_time >= client.settings.DELAY_PUB_MSG:
        # message example
        message = '12.45'
        
        # Try to publish to sensor output topics
        client.publish_to_topics("output/pepeunit", message)


def main():
    # Initialize the PepeUnit client
    client = PepeunitClient(
        env_file_path="env.json",
        schema_file_path="schema.json",
        log_file_path="log.json",
        enable_mqtt=True,
        enable_rest=True,
        cycle_speed=1.0  # 1 second cycle
    )
    
    # Log startup
    client.logger.debug("PepeUnit client created")
    client.logger.debug("Device UUID: {client.unit_uuid}")
    
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
