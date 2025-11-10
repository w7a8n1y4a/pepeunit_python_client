import json
import os
import shutil
import tarfile
import zlib
from typing import Any, Dict, List
from pathlib import Path


class FileManager:
    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any], indent: int = 4) -> None:
        directory = os.path.dirname(file_path)
        
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    
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
        FileManager.extract_pepeunit_archive(archive_path, extract_path)
    
    @staticmethod
    def extract_pepeunit_archive(file_path: str, extract_path: str) -> None:
        with open(file_path, 'rb') as f:
            producer = zlib.decompressobj(wbits=9)
            tar_data = producer.decompress(f.read()) + producer.flush()
            tar_filepath = f'{os.path.dirname(file_path)}/temp_update.tar'
            with open(tar_filepath, 'wb') as tar_file:
                tar_file.write(tar_data)
            try:
                # Use tarfile directly with filter for security (Python 3.12+)
                with tarfile.open(tar_filepath, 'r') as tar:
                    # Check if filter parameter is supported
                    try:
                        tar.extractall(extract_path, filter='data')
                    except TypeError:
                        # Fallback for older Python versions
                        tar.extractall(extract_path)
            finally:
                if os.path.exists(tar_filepath):
                    os.remove(tar_filepath)
    
    @staticmethod
    def copy_directory_contents(source_path: str, destination_path: str) -> None:
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source directory does not exist: {source_path}")
        
        os.makedirs(destination_path, exist_ok=True)
        
        for item in os.listdir(source_path):
            source_item = os.path.join(source_path, item)
            destination_item = os.path.join(destination_path, item)
            
            if os.path.isdir(source_item):
                shutil.copytree(source_item, destination_item, dirs_exist_ok=True)
            else:
                shutil.copy2(source_item, destination_item)
    
    @staticmethod
    def remove_directory(directory_path: str) -> None:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
    
    @staticmethod
    def append_ndjson_with_limit(file_path: str, item: Dict[str, Any], max_lines: int = None) -> None:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                first_char = f.read(1)
                if first_char == '[':
                    try:
                        f.seek(0)
                        data = json.load(f)
                        if isinstance(data, list):
                            with open(file_path, 'w', encoding='utf-8') as fw:
                                for it in data:
                                    json.dump(it, fw, ensure_ascii=False)
                                    fw.write('\n')
                    except Exception:
                        pass
        
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
        except Exception:
            pass
        
        if max_lines is not None and max_lines > 0:
            FileManager.trim_ndjson(file_path, max_lines)
    
    @staticmethod
    def iter_ndjson(file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except Exception:
                        continue
        except Exception:
            return
    
    @staticmethod
    def trim_ndjson(file_path: str, max_lines: int) -> None:
        if max_lines <= 0:
            return
        
        try:
            total = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                for _ in f:
                    total += 1
            
            if total <= max_lines:
                return
            
            to_skip = total - max_lines
            tmp_path = file_path + '.tmp'
            
            with open(file_path, 'r', encoding='utf-8') as src, open(tmp_path, 'w', encoding='utf-8') as dst:
                for line in src:
                    if to_skip > 0:
                        to_skip -= 1
                        continue
                    dst.write(line)
            
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
