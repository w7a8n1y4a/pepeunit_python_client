import json
import os
import shutil
import tarfile
from typing import Any, Dict, List
from pathlib import Path


class FileManager:
    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any], indent: int = 4) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
    
    @staticmethod
    def copy_file(source_path: str, destination_path: str) -> None:
        shutil.copy2(source_path, destination_path)
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        return os.path.exists(file_path)
    
    @staticmethod
    def create_directory(directory_path: str) -> None:
        os.makedirs(directory_path, exist_ok=True)
    
    @staticmethod
    def extract_tar_gz(archive_path: str, extract_path: str) -> None:
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(extract_path)
    
    @staticmethod
    def append_to_json_list(file_path: str, item: Dict[str, Any]) -> None:
        if not os.path.exists(file_path):
            FileManager.write_json(file_path, [])
        
        data = FileManager.read_json(file_path)
        if not isinstance(data, list):
            data = []
        
        data.append(item)
        FileManager.write_json(file_path, data)
