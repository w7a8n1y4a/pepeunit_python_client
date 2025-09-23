from typing import Protocol, Dict, Any, Optional, Callable


class MQTTClientProtocol(Protocol):
    def connect(self, host: str, port: int = 1883, keepalive: int = 60, bind_address: str = "") -> int:
        ...
    
    def disconnect(self) -> int:
        ...
    
    def subscribe(self, topic: str, qos: int = 0) -> tuple:
        ...
    
    def unsubscribe(self, topic: str) -> tuple:
        ...
    
    def publish(self, topic: str, payload: Any = None, qos: int = 0, retain: bool = False) -> tuple:
        ...
    
    def loop_start(self) -> None:
        ...
    
    def loop_stop(self, force: bool = False) -> None:
        ...
    
    def username_pw_set(self, username: str, password: Optional[str] = None) -> None:
        ...
    
    def on_connect(self, client: Any, userdata: Any, flags: Dict, rc: int) -> None:
        ...
    
    def on_message(self, client: Any, userdata: Any, message: Any) -> None:
        ...


class RESTClientProtocol(Protocol):
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        ...
    
    def post(self, url: str, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        ...
    
    def put(self, url: str, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        ...
    
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        ...
