from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class MQTTClientInterface(ABC):
    
    @abstractmethod
    def publish(self, topics: List[str], payload: str) -> None:
        """Отправка сообщения на список топиков"""
        pass
    
    @abstractmethod
    def subscribe(self, topics: List[str]) -> None:
        """Подписка на список топиков"""
        pass
    
    @abstractmethod
    def set_message_handler(self, handler: Callable[[str, str], None]) -> None:
        """Установка обработчика сообщений"""
        pass


class RESTClientInterface(ABC):
    
    @abstractmethod
    def download_update(self, unit_uuid: str) -> str:
        """Скачивание архива обновления, возвращает путь к файлу"""
        pass
    
    @abstractmethod
    def download_env(self, unit_uuid: str) -> Dict[str, Any]:
        """Скачивание env.json, возвращает данные"""
        pass
    
    @abstractmethod
    def download_schema(self, unit_uuid: str) -> Dict[str, Any]:
        """Скачивание schema.json, возвращает данные"""
        pass
    
    @abstractmethod
    def set_state_storage(self, unit_uuid: str, state: str) -> None:
        """Загрузка состояния в Unit Storage"""
        pass
    
    @abstractmethod
    def get_state_storage(self, unit_uuid: str) -> str:
        """Получение состояния из Unit Storage"""
        pass
