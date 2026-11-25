from threading import RLock
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from .abstract_clients import AbstractPepeunitMqttClient

try:
    from paho.mqtt import client as mqtt_client_paho
except ImportError:
    mqtt_client_paho = None

if TYPE_CHECKING:
    from .logger import Logger
    from .settings import Settings


class PepeunitMqttClient(AbstractPepeunitMqttClient):
    def __init__(self, settings: "Settings", logger: "Logger"):
        super().__init__(settings, logger)
        self._client: Optional[Any] = None
        self._input_handler: Optional[Callable] = None
        self._subscriptions: Dict[str, int] = {}
        self._subscription_lock = RLock()

    def _get_client(self) -> Any:
        if mqtt_client_paho is None:
            raise ImportError("paho-mqtt is required for MQTT functionality")
        options = {"client_id": self.settings.unit_uuid}
        if hasattr(mqtt_client_paho, "CallbackAPIVersion"):
            options["callback_api_version"] = (
                mqtt_client_paho.CallbackAPIVersion.VERSION1
            )
        client = mqtt_client_paho.Client(**options)
        client.username_pw_set(self.settings.PU_AUTH_TOKEN, "")
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        return client

    def connect(self) -> None:
        if self._client is None:
            self._client = self._get_client()
        self._client.connect(
            self.settings.PU_MQTT_HOST,
            self.settings.PU_MQTT_PORT,
            keepalive=self.settings.PU_MQTT_KEEPALIVE,
        )
        self._client.loop_start()

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.disconnect()
            self._client.loop_stop()
            self.logger.info("Disconnected from MQTT broker", file_only=True)

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc != 0:
            self.logger.error(f"MQTT connection failed: {rc}", file_only=True)
            return
        with self._subscription_lock:
            self._subscribe(client, list(self._subscriptions.items()))
        self.logger.info("Connected to MQTT broker")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            if self._input_handler is not None:
                self._input_handler(msg)
        except Exception as error:
            self.logger.error(f"Error processing MQTT message: {error}")

    def set_input_handler(self, handler: Callable) -> None:
        self._input_handler = handler

    def set_subscriptions(self, topics: Dict[str, int]) -> None:
        with self._subscription_lock:
            client = self._client
            if client is not None and client.is_connected():
                self._subscribe(
                    client,
                    [
                        (topic, qos)
                        for topic, qos in topics.items()
                        if self._subscriptions.get(topic) != qos
                    ],
                )
                removed = list(self._subscriptions.keys() - topics.keys())
                if removed:
                    rc, _ = client.unsubscribe(removed)
                    if rc != mqtt_client_paho.MQTT_ERR_SUCCESS:
                        raise RuntimeError(f"MQTT unsubscribe failed: {rc}")
            self._subscriptions = dict(topics)

    @staticmethod
    def _subscribe(client, topics) -> None:
        if topics:
            rc, _ = client.subscribe(topics)
            if rc != mqtt_client_paho.MQTT_ERR_SUCCESS:
                raise RuntimeError(f"MQTT subscribe failed: {rc}")

    def publish(self, topic: str, message: Any, qos: int = 0) -> Any:
        if self._client is not None:
            return self._client.publish(topic, message, qos=qos)
        return None
