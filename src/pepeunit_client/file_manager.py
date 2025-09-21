import json
import os
import shutil
import tarfile
import zipfile
from typing import Any, Dict, List
from pathlib import Path

from .exceptions import PepeunitClientError


class FileManager:
    
    @staticmethod
    def read_json_file(file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise PepeunitClientError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise PepeunitClientError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise PepeunitClientError(f"Error reading file {file_path}: {e}")
    
    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise PepeunitClientError(f"Error writing file {file_path}: {e}")
    
    @staticmethod
    def append_to_log_file(file_path: str, log_entry: Dict[str, Any]) -> None:
        try:
            if not os.path.exists(file_path):
                FileManager.write_json_file(file_path, [])
            
            logs = FileManager.read_json_file(file_path)
            if not isinstance(logs, list):
                logs = []
            
            logs.append(log_entry)
            FileManager.write_json_file(file_path, logs)
        except Exception as e:
            raise PepeunitClientError(f"Error appending to log file {file_path}: {e}")
    
    @staticmethod
    def extract_archive(archive_path: str, extract_path: str) -> None:
        try:
            os.makedirs(extract_path, exist_ok=True)
            
            if archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(extract_path)
            elif archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    zip_file.extractall(extract_path)
            else:
                raise PepeunitClientError(f"Unsupported archive format: {archive_path}")
        except Exception as e:
            raise PepeunitClientError(f"Error extracting archive {archive_path}: {e}")
    
    @staticmethod
    def copy_directory(source: str, destination: str) -> None:
        try:
            if os.path.exists(destination):
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        except Exception as e:
            raise PepeunitClientError(f"Error copying directory {source} to {destination}: {e}")
    
    @staticmethod
    def remove_file_or_directory(path: str) -> None:
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            raise PepeunitClientError(f"Error removing {path}: {e}")


class PepeunitFileManager:
    
    def __init__(self, env_path: str, schema_path: str, log_path: str):
        self.env_path = env_path
        self.schema_path = schema_path
        self.log_path = log_path
        
        for path in [env_path, schema_path, log_path]:
            dir_path = os.path.dirname(path)
            if dir_path:  # Создаем директорию только если путь не пустой
                os.makedirs(dir_path, exist_ok=True)
    
    def update_env_file(self, new_env_path: str) -> None:
        try:
            shutil.copy2(new_env_path, self.env_path)
        except Exception as e:
            raise PepeunitClientError(f"Error updating env file: {e}")
    
    def get_env_values(self) -> Dict[str, Any]:
        return FileManager.read_json_file(self.env_path)
    
    def update_schema_file(self, new_schema_path: str) -> None:
        try:
            shutil.copy2(new_schema_path, self.schema_path)
        except Exception as e:
            raise PepeunitClientError(f"Error updating schema file: {e}")
    
    def get_schema_values(self) -> Dict[str, Any]:
        return FileManager.read_json_file(self.schema_path)
    
    def update_log_file(self, new_log_path: str) -> None:
        try:
            shutil.copy2(new_log_path, self.log_path)
        except Exception as e:
            raise PepeunitClientError(f"Error updating log file: {e}")
    
    def get_full_log(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.log_path):
                return []
            logs = FileManager.read_json_file(self.log_path)
            return logs if isinstance(logs, list) else []
        except Exception:
            return []
    
    def append_log_entry(self, log_entry: Dict[str, Any]) -> None:
        FileManager.append_to_log_file(self.log_path, log_entry)
    
    def update_device_program(self, archive_path: str) -> None:
        try:
            temp_dir = os.path.join(os.path.dirname(archive_path), 'temp_update')
            FileManager.extract_archive(archive_path, temp_dir)
            
            current_dir = os.path.dirname(self.env_path)
            
            for item in os.listdir(temp_dir):
                source_item = os.path.join(temp_dir, item)
                dest_item = os.path.join(current_dir, item)
                
                if os.path.isfile(source_item):
                    shutil.copy2(source_item, dest_item)
                elif os.path.isdir(source_item):
                    if os.path.exists(dest_item):
                        shutil.rmtree(dest_item)
                    shutil.copytree(source_item, dest_item)
            
            FileManager.remove_file_or_directory(temp_dir)
            
        except Exception as e:
            raise PepeunitClientError(f"Error updating device program: {e}")
