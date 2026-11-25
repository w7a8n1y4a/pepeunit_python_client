import json
import os
import re
import shutil
import tarfile
import tempfile
import zlib
from pathlib import Path
from typing import Any, Dict, List


class FileManager:
    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def parse_env(content: str) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        for line_number, line in enumerate(content.split("\n"), start=1):
            if not line or line.startswith("#"):
                continue
            name, separator, value = line.partition("=")
            if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise ValueError(f"Invalid environment variable on line {line_number}")
            if name in values:
                raise ValueError(f"Duplicate environment variable on line {line_number}")
            try:
                values[name] = FileManager.parse_env_value(value)
            except ValueError:
                raise ValueError(f"Invalid environment value on line {line_number}") from None
        return values

    @staticmethod
    def parse_env_value(value: str) -> Any:
        if value.startswith('"'):
            return json.loads(value)
        if value.startswith("'") and value.endswith("'"):
            content = re.sub(r"\\(['\\])", r"\1", value[1:-1])
            decoded = json.loads(content)
            if not isinstance(decoded, (dict, list)):
                raise ValueError("Expected a JSON object or array")
            return decoded
        if not re.fullmatch(r"[\w@%+:,./=-]*", value):
            raise ValueError("Invalid unquoted environment value")
        try:
            return json.loads(value)
        except ValueError:
            return value

    @staticmethod
    def read_env(file_path: str) -> Dict[str, Any]:
        return FileManager.parse_env(Path(file_path).read_text(encoding="utf-8"))

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
        with open(file_path, "rb") as source, tempfile.TemporaryFile() as archive:
            producer = zlib.decompressobj(wbits=9)
            for chunk in iter(lambda: source.read(65536), b""):
                archive.write(producer.decompress(chunk))
            archive.write(producer.flush())
            if not producer.eof:
                raise ValueError("Incomplete firmware archive")
            archive.seek(0)
            with tarfile.open(fileobj=archive, mode="r:") as tar:
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(extract_path, filter="data")
                else:
                    root = Path(extract_path).resolve()
                    for member in tar.getmembers():
                        (root / member.name).resolve().relative_to(root)
                        if not (member.isfile() or member.isdir()):
                            raise ValueError("Unsupported firmware archive entry")
                    tar.extractall(extract_path)

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
