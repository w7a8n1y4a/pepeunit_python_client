from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any

import httpx

from .abstract_clients import AbstractPepeunitRestClient
from .file_manager import FileManager
from .io_topics import IOTopic, IOTopics

if TYPE_CHECKING:
    from .settings import Settings


class PepeunitRestClient(AbstractPepeunitRestClient):
    def __init__(self, settings: 'Settings'):
        super().__init__(settings)
        self._httpx_client = httpx

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
        headers["accept"] = "text/plain"
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        content = response.content
        FileManager.parse_env(content.decode("utf-8"))
        destination = Path(file_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
                temp_path = Path(temporary.name)
                temporary.write(content)
            temp_path.replace(destination)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
    
    def get_io_topics(self) -> IOTopics:
        url = f"{self._get_base_url()}/units/io_topics/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()
        headers["accept"] = "application/yaml"
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        return IOTopics.from_yaml(response.content)

    def set_state_storage(self, state: str) -> None:
        url = f"{self._get_base_url()}/units/set_state_storage/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()

        response = self._httpx_client.post(url, headers=headers, json={"state": state})
        response.raise_for_status()
    
    def get_state_storage(self) -> str:
        url = f"{self._get_base_url()}/units/get_state_storage/{self.settings.unit_uuid}"
        headers = self._get_auth_headers()
        
        response = self._httpx_client.get(url, headers=headers)
        response.raise_for_status()
        
        state = response.json()
        if not isinstance(state, str):
            raise TypeError("Expected a JSON string from Pepeunit Unit Storage")
        return state
    
    def get_input_by_output(self, topic: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        output_uuid = IOTopic.uuid_from_topic(topic)
        url = f"{self._get_base_url()}/unit_ios"
        headers = self._get_auth_headers()
        
        params = [
            ('order_by_create_date', 'desc'),
            ('output_uuid', output_uuid),
            ('limit', str(limit)),
            ('offset', str(offset)),
        ]
        
        response = self._httpx_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_units_by_ios(self, unit_io_uuids: list[str], limit: int = 100, offset: int = 0) -> dict[str, Any]:
        if not unit_io_uuids:
            return {'count': 0, 'units': []}
        
        url = f"{self._get_base_url()}/units"
        headers = self._get_auth_headers()
        
        params = [
            ('is_include_output_unit_ios', 'true'),
            ('order_by_unit_name', 'asc'),
            ('order_by_create_date', 'desc'),
            ('order_by_last_update', 'desc'),
            ('limit', str(limit)),
            ('offset', str(offset)),
        ]
        
        for uuid in unit_io_uuids:
            params.append(('unit_io_uuids', uuid))
        
        response = self._httpx_client.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
