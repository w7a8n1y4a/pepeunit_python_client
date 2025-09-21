from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class MQTTClientInterface(ABC):
    """Абстрактный интерфейс для MQTT клиента"""
    
    @abstractmethod
    def connect(self) -> None:
        """Подключение к MQTT брокеру"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Отключение от MQTT брокера"""
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        """Подписка на топики"""
        pass
    
    @abstractmethod
    def unsubscribe(self, topics: List[str]) -> None:
        """Отписка от топиков"""
        pass
    
    @abstractmethod
    def publish(self, topic: str, message: str) -> bool:
        """Публикация сообщения в топик"""
        pass
    
    @abstractmethod
    def set_message_handler(self, handler: Callable) -> None:
        """Установка обработчика сообщений"""
        pass
    
    @abstractmethod
    def start_loop(self) -> None:
        """Запуск цикла обработки сообщений"""
        pass
    
    @abstractmethod
    def stop_loop(self) -> None:
        """Остановка цикла обработки сообщений"""
        pass


class RESTClientInterface(ABC):
    """Абстрактный интерфейс для REST клиента"""
    
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET запрос"""
        pass
    
    @abstractmethod
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """POST запрос"""
        pass
    
    @abstractmethod
    def put(self, url: str, data: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """PUT запрос"""
        pass
    
    @abstractmethod
    def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """DELETE запрос"""
        pass
    
    @abstractmethod
    def download_file(self, url: str, file_path: str, 
                     headers: Optional[Dict[str, str]] = None) -> None:
        """Скачивание файла"""
        pass
