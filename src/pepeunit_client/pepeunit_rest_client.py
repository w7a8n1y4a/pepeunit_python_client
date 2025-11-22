import json
from typing import Dict, Any, List, TYPE_CHECKING

from .file_manager import FileManager
from .abstract_clients import AbstractPepeunitRestClient

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
    
    
    def download_update(self, file_path: str) -> None:
        wbits = 9
        level = 9
        url = f"{self._get_base_url()}/units/firmware/tgz/{self.settings.unit_uuid}?wbits={wbits}&level={level}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
    
    def download_env(self, file_path: str) -> None:
        url = f"{self._get_base_url()}/units/env/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        env_data = response.json()
        
        if isinstance(env_data, str):
            env_data = json.loads(env_data)
        
        FileManager.write_json(file_path, env_data)
    
    def download_schema(self, file_path: str) -> None:
        url = f"{self._get_base_url()}/units/get_current_schema/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        schema_data = response.json()
        
        if isinstance(schema_data, str):
            schema_data = json.loads(schema_data)
        
        FileManager.write_json(file_path, schema_data)
    
    def set_state_storage(self, state: Dict[str, Any]) -> None:
        url = f"{self._get_base_url()}/units/set_state_storage/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()
        headers['content-type'] = 'application/json'
        
        response = self._httpx_client.post(url, headers=headers, data=json.dumps({'state':state}))
        response.raise_for_status()
    
    def get_state_storage(self) -> str:
        url = f"{self._get_base_url()}/units/get_state_storage/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        return response.text
    
    def get_input_by_output(self, topic: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        parts = topic.split('/')
        
        if len(parts) < 2:
            raise ValueError(f"Invalid topic URL format: '{topic}'")
        
        uuid = parts[1]
        
        url = f"{self._get_base_url()}/unit_nodes"
        headers = self._get_auth_headers()
        
        params = [
            ('order_by_create_date', 'desc'),
            ('output_uuid', uuid),
            ('limit', str(limit)),
            ('offset', str(offset)),
        ]
        
        response = self._httpx_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_units_by_nodes(self, unit_node_uuids: List[str], limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        if not unit_node_uuids:
            return {'count': 0, 'units': []}
        
        url = f"{self._get_base_url()}/units"
        headers = self._get_auth_headers()
        
        params = [
            ('is_include_output_unit_nodes', 'true'),
            ('order_by_unit_name', 'asc'),
            ('order_by_create_date', 'desc'),
            ('order_by_last_update', 'desc'),
            ('limit', str(limit)),
            ('offset', str(offset)),
        ]
        
        for uuid in unit_node_uuids:
            params.append(('unit_node_uuids', uuid))
        
        response = self._httpx_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
