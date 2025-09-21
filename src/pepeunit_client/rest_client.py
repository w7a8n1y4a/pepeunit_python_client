import json
import os
from typing import Any, Dict, Optional

import httpx

from .interfaces import RESTClientInterface
from .settings import Settings


class RESTClient(RESTClientInterface):
    
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            # Строим базовый URL из настроек
            base_url = f"{self.settings.HTTP_TYPE}://{self.settings.PEPEUNIT_URL}{self.settings.PEPEUNIT_APP_PREFIX}{self.settings.PEPEUNIT_API_ACTUAL_PREFIX}"
            
            headers = {
                'accept': 'application/json',
                'x-auth-token': self.settings.PEPEUNIT_TOKEN
            }
            
            self._client = httpx.Client(
                base_url=base_url,
                timeout=30.0,
                headers=headers,
                verify=True,
                follow_redirects=True
            )
        return self._client
    
    def _build_url(self, endpoint: str) -> str:
        """Построение URL для API endpoint"""
        return f"/{endpoint.lstrip('/')}"
    
    def download_update(self, unit_uuid: str) -> str:
        """Скачивание архива обновления"""
        try:
            client = self._get_client()
            url = self._build_url(f"units/firmware/tgz/{unit_uuid}")
            
            response = client.get(url)
            response.raise_for_status()
            
            # Сохраняем файл
            archive_path = f"update_{unit_uuid}.tar.gz"
            with open(archive_path, 'wb') as f:
                f.write(response.content)
            
            return archive_path
        except Exception as e:
            raise Exception(f"Failed to download update: {e}")
    
    def download_env(self, unit_uuid: str) -> Dict[str, Any]:
        """Скачивание env.json"""
        try:
            client = self._get_client()
            url = self._build_url(f"units/env/{unit_uuid}")
            
            response = client.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to download env: {e}")
    
    def download_schema(self, unit_uuid: str) -> Dict[str, Any]:
        """Скачивание schema.json"""
        try:
            client = self._get_client()
            url = self._build_url(f"units/get_current_schema/{unit_uuid}")
            
            response = client.get(url)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to download schema: {e}")
    
    def set_state_storage(self, unit_uuid: str, state: str) -> None:
        """Загрузка состояния в Unit Storage"""
        try:
            client = self._get_client()
            url = self._build_url(f"set_state_storage/{unit_uuid}")
            
            data = {"state": state}
            response = client.post(url, json=data)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to set state storage: {e}")
    
    def get_state_storage(self, unit_uuid: str) -> str:
        """Получение состояния из Unit Storage"""
        try:
            client = self._get_client()
            url = self._build_url(f"get_state_storage/{unit_uuid}")
            
            response = client.get(url)
            response.raise_for_status()
            
            return response.text
        except Exception as e:
            raise Exception(f"Failed to get state storage: {e}")
    
    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
