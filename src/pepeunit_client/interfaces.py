from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MQTTClientInterface(ABC):
    """Interface for MQTT client"""
    
    @abstractmethod
    def publish(self, topic: str, payload: str) -> None:
        """Send message to topic"""
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        """Subscribe to topics"""
        pass


class RESTClientInterface(ABC):
    """Interface for REST client"""
    
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute GET request"""
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute POST request"""
        pass
