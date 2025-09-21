import json
import uuid
from typing import Any, Callable, Dict, List, Optional

from paho.mqtt import client as paho_mqtt_client

from .interfaces import MQTTClientInterface
from .settings import Settings


class MQTTClient(MQTTClientInterface):
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client_id = str(uuid.uuid4())
        self._message_handler: Optional[Callable[[str, str], None]] = None
        
        self.client = paho_mqtt_client.Client(
            paho_mqtt_client.CallbackAPIVersion.VERSION1,
            self.client_id
        )
        
        self._setup_callbacks()
        self._connected = False
        self._connection_error = None
    
    def _setup_callbacks(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        self.client.on_log = self._on_log
    
    def set_message_handler(self, handler: Callable[[str, str], None]) -> None:
        """Установка обработчика сообщений"""
        self._message_handler = handler
    
    def _on_connect(self, client, userdata, flags, rc):
        self._connected = (rc == 0)
        if rc != 0:
            self._connection_error = f"Connection failed with code {rc}"
    
    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
    
    def _on_message(self, client, userdata, msg):
        if self._message_handler:
            self._message_handler(msg.topic, msg.payload.decode('utf-8'))
    
    def _on_publish(self, client, userdata, mid):
        pass
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        pass
    
    def _on_unsubscribe(self, client, userdata, mid):
        pass
    
    def _on_log(self, client, userdata, level, buf):
        pass
    
    def connect(self) -> bool:
        try:
            # Используем настройки из settings
            if self.settings.PEPEUNIT_TOKEN:
                self.client.username_pw_set(self.settings.PEPEUNIT_TOKEN, '')
            
            result = self.client.connect(
                self.settings.MQTT_URL, 
                self.settings.MQTT_PORT, 
                self.settings.PING_INTERVAL
            )
            if result == 0:
                self._connected = True
                self.client.loop_start()
                return True
            else:
                self._connection_error = f"Connection failed with result {result}"
                return False
        except Exception as e:
            self._connection_error = str(e)
            return False
    
    def disconnect(self) -> None:
        if self._connected:
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False
    
    def is_connected(self) -> bool:
        return self._connected
    
    def get_connection_error(self) -> Optional[str]:
        return self._connection_error
    
    def publish(self, topics: List[str], payload: str, qos: int = 0, retain: bool = False) -> bool:
        if not self._connected:
            return False
        
        try:
            success = True
            for topic in topics:
                result = self.client.publish(topic, payload, qos, retain)
                if result.rc != 0:
                    success = False
            return success
        except Exception:
            return False
    
    def subscribe(self, topics: List[str], qos: int = 0) -> bool:
        if not self._connected:
            return False
        
        try:
            if isinstance(topics, str):
                topics = [topics]
            
            topic_list = [(topic, qos) for topic in topics]
            result, mid = self.client.subscribe(topic_list)
            return result == 0
        except Exception:
            return False
    
    def unsubscribe(self, topics: List[str]) -> bool:
        if not self._connected:
            return False
        
        try:
            if isinstance(topics, str):
                topics = [topics]
            
            result, mid = self.client.unsubscribe(topics)
            return result == 0
        except Exception:
            return False
    
    def get_client_info(self) -> Dict[str, Any]:
        return {
            'client_id': self.client_id,
            'host': self.settings.MQTT_URL,
            'port': self.settings.MQTT_PORT,
            'username': self.settings.PEPEUNIT_TOKEN,
            'connected': self._connected,
            'connection_error': self._connection_error
        }
