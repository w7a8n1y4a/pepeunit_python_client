from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MQTTClientInterface(ABC):
    """Интерфейс для MQTT клиента"""
    
    @abstractmethod
    def publish(self, topic: str, payload: str) -> None:
        """Отправить сообщение в топик"""
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        """Подписаться на топики"""
        pass


class RESTClientInterface(ABC):
    """Интерфейс для REST клиента"""
    
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Выполнить GET запрос"""
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Выполнить POST запрос"""
        pass
