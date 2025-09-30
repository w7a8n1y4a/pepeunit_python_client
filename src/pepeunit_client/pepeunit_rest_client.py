import json
from typing import Dict, Any, TYPE_CHECKING

from .file_manager import FileManager
from .abstract_clients import AbstractPepeunitRestClient

# Import for mocking in tests
try:
    import httpx
except ImportError:
    httpx = None

if TYPE_CHECKING:
    from .settings import Settings


class PepeunitRestClient(AbstractPepeunitRestClient):
    def __init__(self, settings: 'Settings'):
        super().__init__(settings)
        self._httpx_client = self._get_httpx_client()
    
    def _get_httpx_client(self):
        if httpx is None:
            raise ImportError("httpx is required for REST functionality")
        return httpx
    
    
    def download_update(self, unit_uuid: str, file_path: str) -> None:
        wbits = 9
        level = 9
        url = f"{self._get_base_url()}/units/firmware/tgz/{unit_uuid}?wbits={wbits}&level={level}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
    
    def download_env(self, unit_uuid: str, file_path: str) -> None:
        url = f"{self._get_base_url()}/units/env/{unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        env_data = response.json()
        
        if isinstance(env_data, str):
            env_data = json.loads(env_data)
        
        FileManager.write_json(file_path, env_data)
    
    def download_schema(self, unit_uuid: str, file_path: str) -> None:
        url = f"{self._get_base_url()}/units/get_current_schema/{unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        schema_data = response.json()
        
        if isinstance(schema_data, str):
            schema_data = json.loads(schema_data)
        
        FileManager.write_json(file_path, schema_data)
    
    def set_state_storage(self, unit_uuid: str, state: Dict[str, Any]) -> None:
        url = f"{self._get_base_url()}/unit/{unit_uuid}"
        headers = self._get_auth_headers()
        headers['content-type'] = 'application/json'
        
        response = self._httpx_client.put(url, headers=headers, json=state)
        response.raise_for_status()
    
    def get_state_storage(self, unit_uuid: str) -> Dict[str, Any]:
        url = f"{self._get_base_url()}/unit/{unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
