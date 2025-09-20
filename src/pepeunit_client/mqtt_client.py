import json
import uuid
from typing import Any, Callable, Dict, List, Optional

from paho.mqtt import client as paho_mqtt_client

from .interfaces import MQTTClientInterface


class MQTTClient(MQTTClientInterface):
    
    def __init__(
        self,
        host: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        keepalive: int = 60,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
        on_publish: Optional[Callable] = None,
        on_subscribe: Optional[Callable] = None,
        on_unsubscribe: Optional[Callable] = None,
        on_log: Optional[Callable] = None
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id or str(uuid.uuid4())
        self.keepalive = keepalive
        
        self.client = paho_mqtt_client.Client(
            paho_mqtt_client.CallbackAPIVersion.VERSION1,
            self.client_id
        )
        
        self._setup_callbacks(
            on_connect, on_disconnect, on_message, on_publish,
            on_subscribe, on_unsubscribe, on_log
        )
        
        self._connected = False
        self._connection_error = None
    
    def _setup_callbacks(
        self,
        on_connect: Optional[Callable],
        on_disconnect: Optional[Callable],
        on_message: Optional[Callable],
        on_publish: Optional[Callable],
        on_subscribe: Optional[Callable],
        on_unsubscribe: Optional[Callable],
        on_log: Optional[Callable]
    ) -> None:
        self.client.on_connect = self._on_connect_wrapper(on_connect)
        self.client.on_disconnect = self._on_disconnect_wrapper(on_disconnect)
        self.client.on_message = self._on_message_wrapper(on_message)
        self.client.on_publish = self._on_publish_wrapper(on_publish)
        self.client.on_subscribe = self._on_subscribe_wrapper(on_subscribe)
        self.client.on_unsubscribe = self._on_unsubscribe_wrapper(on_unsubscribe)
        self.client.on_log = self._on_log_wrapper(on_log)
    
    def _on_connect_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, flags, rc):
            self._connected = (rc == 0)
            if rc != 0:
                self._connection_error = f"Connection failed with code {rc}"
            if user_callback:
                user_callback(client, userdata, flags, rc)
        return wrapper
    
    def _on_disconnect_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, rc):
            self._connected = False
            if user_callback:
                user_callback(client, userdata, rc)
        return wrapper
    
    def _on_message_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, msg):
            if user_callback:
                user_callback(client, userdata, msg)
        return wrapper
    
    def _on_publish_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, mid):
            if user_callback:
                user_callback(client, userdata, mid)
        return wrapper
    
    def _on_subscribe_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, mid, granted_qos):
            if user_callback:
                user_callback(client, userdata, mid, granted_qos)
        return wrapper
    
    def _on_unsubscribe_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, mid):
            if user_callback:
                user_callback(client, userdata, mid)
        return wrapper
    
    def _on_log_wrapper(self, user_callback: Optional[Callable]) -> Callable:
        def wrapper(client, userdata, level, buf):
            if user_callback:
                user_callback(client, userdata, level, buf)
        return wrapper
    
    def connect(self) -> bool:
        try:
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            result = self.client.connect(self.host, self.port, self.keepalive)
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
    
    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        if not self._connected:
            return False
        
        try:
            result = self.client.publish(topic, payload, qos, retain)
            return result.rc == 0
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
    
    def publish_json(self, topic: str, data: Dict[str, Any], qos: int = 0, retain: bool = False) -> bool:
        try:
            payload = json.dumps(data)
            return self.publish(topic, payload, qos, retain)
        except (TypeError, ValueError):
            return False
    
    def get_client_info(self) -> Dict[str, Any]:
        return {
            'client_id': self.client_id,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'connected': self._connected,
            'connection_error': self._connection_error
        }
