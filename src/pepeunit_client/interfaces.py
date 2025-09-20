from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MQTTClientInterface(ABC):
    
    @abstractmethod
    def publish(self, topic: str, payload: str) -> None:
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        pass


class RESTClientInterface(ABC):
    
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        pass
