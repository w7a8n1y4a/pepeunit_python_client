from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class MQTTClientInterface(ABC):
    
    @abstractmethod
    def connect(self) -> None:
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        pass
    
    @abstractmethod
    def unsubscribe(self, topics: List[str]) -> None:
        pass
    
    @abstractmethod
    def publish(self, topic: str, message: str) -> bool:
        pass
    
    @abstractmethod
    def set_message_handler(self, handler: Callable) -> None:
        pass
    
    @abstractmethod
    def start_loop(self) -> None:
        pass
    
    @abstractmethod
    def stop_loop(self) -> None:
        pass


class RESTClientInterface(ABC):
    
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def put(self, url: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def download_file(self, url: str, file_path: str, 
                     headers: Optional[Dict[str, str]] = None) -> None:
        pass
