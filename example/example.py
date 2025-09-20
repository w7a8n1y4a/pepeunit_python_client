#!/usr/bin/env python3
"""
Temporary example for running a real unit with PepeunitClient.
This example demonstrates all four configuration scenarios:
1. Without MQTT and without REST
2. With MQTT but without REST  
3. With REST but without MQTT
4. With both MQTT and REST
"""

import json
import time
import signal
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pepeunit_client import PepeunitClient
from pepeunit_client.mqtt_client import MQTTClient
from pepeunit_client.rest_client import RESTClient
from pepeunit_client.enums import LogLevel


class UnitExample:
    def __init__(self, use_mqtt: bool = True, use_rest: bool = True):
        self.use_mqtt = use_mqtt
        self.use_rest = use_rest
        self.running = True
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize clients
        self.mqtt_client = None
        self.rest_client = None
        
        if use_mqtt:
            self.mqtt_client = self._setup_mqtt_client()
        
        if use_rest:
            self.rest_client = self._setup_rest_client()
        
        # Initialize PepeunitClient
        self.pepeunit_client = PepeunitClient(
            env_path="../env.json",
            schema_path="../schema.json", 
            log_path="../log.json",
            mqtt_client=self.mqtt_client,
            rest_client=self.rest_client
        )
        
        print(f"Unit initialized with MQTT: {use_mqtt}, REST: {use_rest}")
    
    def _setup_mqtt_client(self) -> MQTTClient:
        """Setup MQTT client with callbacks"""
        # Get environment values from the temporary client
        temp_client = PepeunitClient(
            env_path="../env.json",
            schema_path="../schema.json", 
            log_path="../log.json"
        )
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("MQTT connected successfully")
                # Subscribe to input topics
                input_topics = temp_client.get_input_topics()
                if input_topics:
                    temp_client.subscribe_to_topics(input_topics)
            else:
                print(f"MQTT connection failed with code {rc}")
        
        def on_disconnect(client, userdata, rc):
            print(f"MQTT disconnected with code {rc}")
        
        def on_message(client, userdata, msg):
            print(f"MQTT message received on {msg.topic}: {msg.payload.decode()}")
            # Process incoming messages here
            self._process_mqtt_message(msg.topic, msg.payload.decode())
        
        def on_log(client, userdata, level, buf):
            print(f"MQTT log: {buf}")
        
        mqtt_client = MQTTClient(
            host=temp_client.get_env_value("MQTT_URL", "localhost"),
            port=temp_client.get_env_value("MQTT_PORT", 1883),
            on_connect=on_connect,
            on_disconnect=on_disconnect,
            on_message=on_message,
            on_log=on_log
        )
        
        return mqtt_client
    
    def _setup_rest_client(self) -> RESTClient:
        """Setup REST client"""
        # Get environment values from the temporary client
        temp_client = PepeunitClient(
            env_path="../env.json",
            schema_path="../schema.json", 
            log_path="../log.json"
        )
        
        base_url = f"{temp_client.get_env_value('HTTP_TYPE', 'https')}://{temp_client.get_env_value('PEPEUNIT_URL', 'localhost')}"
        api_prefix = temp_client.get_env_value('PEPEUNIT_API_ACTUAL_PREFIX', '/api/v1')
        full_url = f"{base_url}{api_prefix}"
        
        headers = {
            'Authorization': f"Bearer {temp_client.get_env_value('PEPEUNIT_TOKEN', '')}",
            'Content-Type': 'application/json'
        }
        
        rest_client = RESTClient(
            base_url=full_url,
            headers=headers,
            timeout=30.0
        )
        
        return rest_client
    
    def _process_mqtt_message(self, topic: str, payload: str):
        """Process incoming MQTT messages"""
        try:
            data = json.loads(payload)
            print(f"Processing MQTT message: {data}")
            
            # Log the received message
            self.pepeunit_client.save_log(LogLevel.INFO, f"Received MQTT message on {topic}: {data}")
            
            # Process different message types based on topic
            if "update/pepeunit" in topic:
                self._handle_update_message(data)
            elif "env_update/pepeunit" in topic:
                self._handle_env_update_message(data)
            elif "schema_update/pepeunit" in topic:
                self._handle_schema_update_message(data)
            elif "log_sync/pepeunit" in topic:
                self._handle_log_sync_message(data)
            elif "input/pepeunit" in topic:
                self._handle_input_message(data)
                
        except json.JSONDecodeError:
            print(f"Invalid JSON in MQTT message: {payload}")
            self.pepeunit_client.save_log(LogLevel.ERROR, f"Invalid JSON in MQTT message: {payload}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
            self.pepeunit_client.save_log(LogLevel.ERROR, f"Error processing MQTT message: {e}")
    
    def _handle_update_message(self, data):
        """Handle update messages"""
        print("Handling update message")
        self.pepeunit_client.save_log(LogLevel.INFO, "Processing update message")
    
    def _handle_env_update_message(self, data):
        """Handle environment update messages"""
        print("Handling environment update message")
        if isinstance(data, dict):
            self.pepeunit_client.update_env(data)
        self.pepeunit_client.save_log(LogLevel.INFO, "Environment updated from MQTT")
    
    def _handle_schema_update_message(self, data):
        """Handle schema update messages"""
        print("Handling schema update message")
        if isinstance(data, dict):
            self.pepeunit_client.update_schema(data)
        self.pepeunit_client.save_log(LogLevel.INFO, "Schema updated from MQTT")
    
    def _handle_log_sync_message(self, data):
        """Handle log sync messages"""
        print("Handling log sync message")
        self.pepeunit_client.save_log(LogLevel.INFO, "Log sync message received")
    
    def _handle_input_message(self, data):
        """Handle input messages"""
        print("Handling input message")
        self.pepeunit_client.save_log(LogLevel.INFO, f"Input message received: {data}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """Start the unit"""
        print("Starting unit...")
        
        # Connect MQTT if enabled
        if self.mqtt_client:
            if not self.mqtt_client.connect():
                print(f"Failed to connect to MQTT: {self.mqtt_client.get_connection_error()}")
                return False
            print("MQTT client connected")
        
        # Test REST connection if enabled
        if self.rest_client:
            print("Testing REST connection...")
            # You can add REST API calls here
            print("REST client ready")
        
        # Log startup
        self.pepeunit_client.save_log(LogLevel.INFO, "Unit started successfully")
        
        # Main loop
        self._main_loop()
        
        return True
    
    def _main_loop(self):
        """Main execution loop"""
        state_interval = self.pepeunit_client.get_env_value("STATE_SEND_INTERVAL", 2)
        last_state_send = 0
        
        print("Unit is running. Press Ctrl+C to stop.")
        
        while self.running:
            current_time = time.time()
            
            # Send device state periodically
            if current_time - last_state_send >= state_interval:
                self._send_device_state()
                last_state_send = current_time
            
            # Send test log message
            if int(current_time) % 10 == 0:  # Every 10 seconds
                self.pepeunit_client.save_log(LogLevel.INFO, f"Unit heartbeat - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(1)
        
        self._shutdown()
    
    def _send_device_state(self):
        """Send device state via MQTT"""
        if not self.mqtt_client:
            return
        
        state = self.pepeunit_client.generate_device_state()
        topic = self.pepeunit_client.get_topic_by_key('state/pepeunit')
        
        if topic:
            success = self.pepeunit_client.send_mqtt_message(topic, json.dumps(state))
            if success:
                print(f"Device state sent: {state}")
            else:
                print("Failed to send device state")
        else:
            print("State topic not found in schema")
    
    def _shutdown(self):
        """Graceful shutdown"""
        print("Shutting down unit...")
        
        # Disconnect MQTT
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            print("MQTT client disconnected")
        
        # Close REST client
        if self.rest_client:
            self.rest_client.close()
            print("REST client closed")
        
        # Log shutdown
        self.pepeunit_client.save_log(LogLevel.INFO, "Unit stopped")
        
        print("Unit stopped successfully")


def main():
    """Main function with different configuration options"""
    print("Pepeunit Unit Example")
    print("====================")
    print("Available configurations:")
    print("1. Without MQTT and without REST")
    print("2. With MQTT but without REST")
    print("3. With REST but without MQTT")
    print("4. With both MQTT and REST")
    print()
    
    # You can change these flags to test different configurations
    use_mqtt = True   # Set to False to disable MQTT
    use_rest = True   # Set to False to disable REST
    
    print(f"Starting with MQTT: {use_mqtt}, REST: {use_rest}")
    print()
    
    try:
        unit = UnitExample(use_mqtt=use_mqtt, use_rest=use_rest)
        unit.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
