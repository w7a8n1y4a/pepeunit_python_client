import json
import uuid
from typing import Any, Callable, Dict, List, Optional

from .interfaces import MQTTClientInterface
from .exceptions import PepeunitClientError
from .enums import LogLevel


try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False


class MQTTClient(MQTTClientInterface):
    """Реализация MQTT клиента на основе paho-mqtt"""
    
    def __init__(self, host: str, port: int, username: str, password: str = ""):
        if not MQTT_AVAILABLE:
            raise PepeunitClientError("paho-mqtt is not installed. Install with: pip install 'pepeunit-client[mqtt]'")
        
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.message_handler: Optional[Callable] = None
        self.is_connected = False
        
    def connect(self) -> None:
        """Подключение к MQTT брокеру"""
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, str(uuid.uuid4()))
            self.client.username_pw_set(self.username, self.password)
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            self.client.connect(self.host, self.port)
            self.is_connected = True
        except Exception as e:
            raise PepeunitClientError(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self) -> None:
        """Отключение от MQTT брокера"""
        if self.client:
            try:
                self.client.disconnect()
                self.is_connected = False
            except Exception as e:
                raise PepeunitClientError(f"Failed to disconnect from MQTT broker: {e}")
    
    def subscribe(self, topics: List[str]) -> None:
        """Подписка на топики"""
        if not self.client or not self.is_connected:
            raise PepeunitClientError("MQTT client is not connected")
        
        try:
            for topic in topics:
                result = self.client.subscribe(topic, qos=0)
                if result[0] != mqtt.MQTT_ERR_SUCCESS:
                    raise PepeunitClientError(f"Failed to subscribe to topic {topic}")
        except Exception as e:
            raise PepeunitClientError(f"Error subscribing to topics: {e}")
    
    def unsubscribe(self, topics: List[str]) -> None:
        """Отписка от топиков"""
        if not self.client or not self.is_connected:
            raise PepeunitClientError("MQTT client is not connected")
        
        try:
            for topic in topics:
                result = self.client.unsubscribe(topic)
                if result[0] != mqtt.MQTT_ERR_SUCCESS:
                    raise PepeunitClientError(f"Failed to unsubscribe from topic {topic}")
        except Exception as e:
            raise PepeunitClientError(f"Error unsubscribing from topics: {e}")
    
    def publish(self, topic: str, message: str) -> bool:
        """Публикация сообщения в топик"""
        if not self.client or not self.is_connected:
            raise PepeunitClientError("MQTT client is not connected")
        
        try:
            result = self.client.publish(topic, message)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            raise PepeunitClientError(f"Error publishing message to topic {topic}: {e}")
    
    def set_message_handler(self, handler: Callable) -> None:
        """Установка обработчика сообщений"""
        self.message_handler = handler
    
    def start_loop(self) -> None:
        """Запуск цикла обработки сообщений"""
        if not self.client:
            raise PepeunitClientError("MQTT client is not initialized")
        
        try:
            self.client.loop_start()
        except Exception as e:
            raise PepeunitClientError(f"Error starting MQTT loop: {e}")
    
    def stop_loop(self) -> None:
        """Остановка цикла обработки сообщений"""
        if self.client:
            try:
                self.client.loop_stop()
            except Exception as e:
                raise PepeunitClientError(f"Error stopping MQTT loop: {e}")
    
    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback при подключении"""
        if rc == 0:
            self.is_connected = True
        else:
            self.is_connected = False
            raise PepeunitClientError(f"Failed to connect to MQTT broker, return code {rc}")
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        """Callback при отключении"""
        self.is_connected = False
    
    def _on_message(self, client, userdata, msg) -> None:
        """Callback при получении сообщения"""
        if self.message_handler:
            try:
                self.message_handler(client, userdata, msg)
            except Exception as e:
                # Логируем ошибку, но не прерываем работу
                pass


class DummyMQTTClient(MQTTClientInterface):
    """Заглушка MQTT клиента для случаев, когда MQTT не используется"""
    
    def __init__(self):
        self.is_connected = False
        self.message_handler: Optional[Callable] = None
        
    def connect(self) -> None:
        raise PepeunitClientError("MQTT client is not available. Install paho-mqtt to use MQTT functionality.")
    
    def disconnect(self) -> None:
        pass
    
    def subscribe(self, topics: List[str]) -> None:
        raise PepeunitClientError("MQTT client is not available. Install paho-mqtt to use MQTT functionality.")
    
    def unsubscribe(self, topics: List[str]) -> None:
        raise PepeunitClientError("MQTT client is not available. Install paho-mqtt to use MQTT functionality.")
    
    def publish(self, topic: str, message: str) -> bool:
        raise PepeunitClientError("MQTT client is not available. Install paho-mqtt to use MQTT functionality.")
    
    def set_message_handler(self, handler: Callable) -> None:
        self.message_handler = handler
    
    def start_loop(self) -> None:
        pass
    
    def stop_loop(self) -> None:
        pass
