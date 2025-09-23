from typing import Dict, Any, List

from .file_manager import FileManager


class SchemaManager:
    def __init__(self, schema_file_path: str):
        self.schema_file_path = schema_file_path
        self._schema_data = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        return FileManager.read_json(self.schema_file_path)
    
    def update_from_file(self) -> None:
        self._schema_data = self._load_schema()
    
    def update_schema(self, schema_dict: Dict[str, Any]) -> None:
        self._schema_data = schema_dict
        FileManager.write_json(self.schema_file_path, schema_dict)
    
    @property
    def input_base_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('input_base_topic', {})
    
    @property
    def output_base_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('output_base_topic', {})
    
    @property
    def input_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('input_topic', {})
    
    @property
    def output_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('output_topic', {})
