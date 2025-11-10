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
from pepeunit_client import PepeunitClient, RestartMode
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
                    
                    # check work set to storage
                    if value < 10:
                        client.rest_client.set_state_storage('This line is saved in Pepeunit Instance')
                        client.logger.info(f"Success set state")
                    
                    # check work get from storage
                    if value > 10 and value < 20:
                        state = client.rest_client.get_state_storage()
                        client.logger.info(f"Success get state: {state}")

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
