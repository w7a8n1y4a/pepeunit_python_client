import json
import os
import shutil
import zlib
from pathlib import Path
from typing import Any, Dict, List, Union

from .exceptions import PepeunitClientError


class FileManager:
    
    @staticmethod
    def load_json_file(file_path: Path) -> Union[Dict[str, Any], List[Any]]:
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                raise PepeunitClientError("File not found: {}".format(file_path))
        except Exception as e:
            raise PepeunitClientError("File not found: {}".format(file_path))
    
    @staticmethod
    def save_json_file(file_path: Path, data: Union[Dict[str, Any], List[Any]]) -> None:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise PepeunitClientError("File not found: {}".format(file_path))
