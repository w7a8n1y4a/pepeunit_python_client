import json
import os
import re
import shutil
import tarfile
import tempfile
import zlib
from collections.abc import Iterator
from itertools import islice
from pathlib import Path
from typing import Any


class FileManager:
    @staticmethod
    def parse_env(content: str) -> dict[str, Any]:
        values: dict[str, Any] = {}
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
    def read_env(file_path: str | Path) -> dict[str, Any]:
        return FileManager.parse_env(Path(file_path).read_text(encoding="utf-8"))

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
                tar.extractall(extract_path, filter="data")

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
    def append_ndjson_with_limit(file_path: str, item: dict[str, Any], max_lines: int) -> None:
        path = Path(file_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as log:
                log.write(json.dumps(item, ensure_ascii=False) + "\n")
            if max_lines > 0:
                FileManager._trim_ndjson(path, max_lines)
        except (OSError, UnicodeError):
            return

    @staticmethod
    def iter_ndjson(file_path: str) -> Iterator[dict[str, Any]]:
        try:
            with open(file_path, encoding="utf-8") as log:
                for line in log:
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(entry, dict):
                        yield entry
        except (OSError, UnicodeDecodeError):
            return

    @staticmethod
    def _trim_ndjson(path: Path, max_lines: int) -> None:
        pending = None
        try:
            with path.open(encoding="utf-8") as source:
                to_skip = sum(1 for _ in source) - max_lines
                if to_skip <= 0:
                    return
                source.seek(0)
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=path.parent, delete=False
                ) as target:
                    pending = Path(target.name)
                    target.writelines(islice(source, to_skip, None))
            shutil.copymode(path, pending)
            pending.replace(path)
        finally:
            if pending is not None:
                pending.unlink(missing_ok=True)
