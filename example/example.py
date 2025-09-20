#!/usr/bin/env python3

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
        """Handle environment update messages (как в old_client.py)"""
        print("Handling environment update message")
        if isinstance(data, dict):
            self.pepeunit_client.update_env(data)
            self.pepeunit_client.save_log(LogLevel.INFO, "Environment updated from MQTT")
        else:
            # Если данные не в MQTT, скачиваем с Backend как в old_client.py
            self._download_and_update_env()
    
    def _handle_schema_update_message(self, data):
        """Handle schema update messages (как в old_client.py)"""
        print("Handling schema update message")
        if isinstance(data, dict):
            self.pepeunit_client.update_schema(data)
            self.pepeunit_client.save_log(LogLevel.INFO, "Schema updated from MQTT")
        else:
            # Если данные не в MQTT, скачиваем с Backend как в old_client.py
            self._download_and_update_schema()
    
    def _download_and_update_env(self):
        """Download and update env from Backend (как в old_client.py)"""
        if not self.rest_client:
            self.pepeunit_client.save_log(LogLevel.WARNING, "REST client not available for env update")
            return
        
        try:
            # Получаем URL для env как в old_client.py
            base_url = f"{self.pepeunit_client.get_env_value('HTTP_TYPE', 'https')}://{self.pepeunit_client.get_env_value('PEPEUNIT_URL', 'localhost')}"
            api_prefix = self.pepeunit_client.get_env_value('PEPEUNIT_API_ACTUAL_PREFIX', '/api/v1')
            unit_uuid = "374d41e4-153b-4d3e-aba0-a088374ecd2d"  # Из schema.json
            
            url = f"{base_url}{api_prefix}/units/env/{unit_uuid}"
            headers = {
                'accept': 'application/json',
                'x-auth-token': self.pepeunit_client.get_env_value('PEPEUNIT_TOKEN', '')
            }
            
            response = self.rest_client.get(url, headers=headers)
            if response.get('success') and 'data' in response:
                self.pepeunit_client.update_env(response['data'])
                self.pepeunit_client.save_log(LogLevel.INFO, "Environment updated from Backend")
            else:
                self.pepeunit_client.save_log(LogLevel.ERROR, f"Failed to download env: {response}")
        except Exception as e:
            self.pepeunit_client.save_log(LogLevel.ERROR, f"Error downloading env: {e}")
    
    def _download_and_update_schema(self):
        """Download and update schema from Backend (как в old_client.py)"""
        if not self.rest_client:
            self.pepeunit_client.save_log(LogLevel.WARNING, "REST client not available for schema update")
            return
        
        try:
            # Получаем URL для schema как в old_client.py
            base_url = f"{self.pepeunit_client.get_env_value('HTTP_TYPE', 'https')}://{self.pepeunit_client.get_env_value('PEPEUNIT_URL', 'localhost')}"
            api_prefix = self.pepeunit_client.get_env_value('PEPEUNIT_API_ACTUAL_PREFIX', '/api/v1')
            unit_uuid = "374d41e4-153b-4d3e-aba0-a088374ecd2d"  # Из schema.json
            
            url = f"{base_url}{api_prefix}/units/get_current_schema/{unit_uuid}"
            headers = {
                'accept': 'application/json',
                'x-auth-token': self.pepeunit_client.get_env_value('PEPEUNIT_TOKEN', '')
            }
            
            response = self.rest_client.get(url, headers=headers)
            if response.get('success') and 'data' in response:
                self.pepeunit_client.update_schema(response['data'])
                # Переподписываемся на новые топики как в old_client.py
                if self.mqtt_client:
                    input_topics = self.pepeunit_client.get_input_topics()
                    if input_topics:
                        self.pepeunit_client.subscribe_to_topics(input_topics)
                self.pepeunit_client.save_log(LogLevel.INFO, "Schema updated from Backend")
            else:
                self.pepeunit_client.save_log(LogLevel.ERROR, f"Failed to download schema: {response}")
        except Exception as e:
            self.pepeunit_client.save_log(LogLevel.ERROR, f"Error downloading schema: {e}")
    
    def _handle_log_sync_message(self, data):
        """Handle log sync messages (как в old_client.py)"""
        print("Handling log sync message")
        self.pepeunit_client.save_log(LogLevel.INFO, "Log sync message received")
        
        # Отправляем все логи как в old_client.py
        if not self.mqtt_client:
            return
        
        topic = self.pepeunit_client.get_topic_by_key('log/pepeunit')
        if topic:
            try:
                all_logs = self.pepeunit_client.get_all_logs()
                log_message = json.dumps(all_logs, indent=4)
                success = self.pepeunit_client.send_mqtt_message(topic, log_message)
                if success:
                    print(f"Log sync sent to {topic}: {len(all_logs)} log entries")
                else:
                    print(f"Failed to send log sync to {topic}")
            except Exception as e:
                error_msg = json.dumps({'level': 'Debug', 'message': str(e)})
                success = self.pepeunit_client.send_mqtt_message(topic, error_msg)
                if success:
                    print(f"Log sync error sent to {topic}: {str(e)}")
                else:
                    print(f"Failed to send log sync error to {topic}")
        else:
            print("Log topic not found in schema")
    
    def _handle_input_message(self, data):
        """Handle input messages (как в old_client.py)"""
        print("Handling input message")
        self.pepeunit_client.save_log(LogLevel.INFO, f"Input message received: {data}")
        
        # Обработка как в old_client.py
        try:
            value = int(data) if isinstance(data, str) else data
            if value == 0:
                # Отправляем ответ в output/pepeunit как в old_client.py
                self._send_output_message(str(value))
                self.pepeunit_client.save_log(LogLevel.INFO, f"Processed input value: {value}")
        except (ValueError, TypeError):
            self.pepeunit_client.save_log(LogLevel.WARNING, f"Invalid input value: {data}")
    
    def _send_output_message(self, message: str):
        """Send message to output/pepeunit topic (как в old_client.py)"""
        if not self.mqtt_client:
            return
        
        topic = self.pepeunit_client.get_topic_by_key('output/pepeunit')
        if topic:
            success = self.pepeunit_client.send_mqtt_message(topic, message)
            if success:
                print(f"Output message sent to {topic}: {message}")
            else:
                print(f"Failed to send output message to {topic}")
        else:
            print("Output topic not found in schema")
    
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
        """Main execution loop - аналогично old_client.py"""
        state_interval = self.pepeunit_client.get_env_value("STATE_SEND_INTERVAL", 300)
        delay_pub_msg = self.pepeunit_client.get_env_value("DELAY_PUB_MSG", 1)
        
        last_state_send = 0
        last_pub_msg = 0
        msg_count = 1
        
        print("Unit is running. Press Ctrl+C to stop.")
        
        while self.running:
            current_time = time.time()
            
            # Send periodic messages to output_topic (как в old_client.py)
            if current_time - last_pub_msg >= delay_pub_msg:
                self._send_periodic_messages(msg_count)
                last_pub_msg = current_time
                msg_count += 1
            
            # Send device state periodically (как в old_client.py)
            if current_time - last_state_send >= state_interval:
                self._send_device_state()
                last_state_send = current_time
            
            # Send test log message
            if int(current_time) % 10 == 0:  # Every 10 seconds
                self.pepeunit_client.save_log(LogLevel.INFO, f"Unit heartbeat - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(0.25)  # Как в old_client.py
        
        self._shutdown()
    
    def _send_periodic_messages(self, msg_count: int):
        """Send periodic messages to output_topic (как в old_client.py)"""
        if not self.mqtt_client:
            return
        
        # Получаем все output_topic из schema
        schema_data = self.pepeunit_client.get_schema_data()
        output_topics = schema_data.get('output_topic', {})
        
        for topic_name in output_topics.keys():
            # Формируем сообщение как в old_client.py: msg_count // 10
            message = str(msg_count // 10)
            
            # Получаем полный топик из schema
            topics = output_topics[topic_name]
            if isinstance(topics, list) and topics:
                for topic in topics:
                    success = self.pepeunit_client.send_mqtt_message(topic, message)
                    if success:
                        print(f"Periodic message sent to {topic}: {message}")
                    else:
                        print(f"Failed to send periodic message to {topic}")
            elif isinstance(topics, str):
                success = self.pepeunit_client.send_mqtt_message(topics, message)
                if success:
                    print(f"Periodic message sent to {topics}: {message}")
                else:
                    print(f"Failed to send periodic message to {topics}")

    def _send_device_state(self):
        """Send device state via MQTT (как в old_client.py)"""
        if not self.mqtt_client:
            return
        
        # Генерируем состояние как в old_client.py
        state = self._generate_system_state()
        topic = self.pepeunit_client.get_topic_by_key('state/pepeunit')
        
        if topic:
            success = self.pepeunit_client.send_mqtt_message(topic, json.dumps(state))
            if success:
                print(f"Device state sent: {state}")
            else:
                print("Failed to send device state")
        else:
            print("State topic not found in schema")
    
    def _generate_system_state(self):
        """Generate system state exactly like old_client.py"""
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            cpu_freq = psutil.cpu_freq()
            
            return {
                'millis': round(time.time() * 1000),
                'mem_free': memory_info.available,
                'mem_alloc': memory_info.total - memory_info.available,
                'freq': cpu_freq.current if cpu_freq else 0,
                'commit_version': self.pepeunit_client.get_env_value('COMMIT_VERSION', 'unknown'),
            }
        except ImportError:
            return {
                'millis': round(time.time() * 1000),
                'mem_free': 0,
                'mem_alloc': 0,
                'freq': 0,
                'commit_version': self.pepeunit_client.get_env_value('COMMIT_VERSION', 'unknown'),
            }
    
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
