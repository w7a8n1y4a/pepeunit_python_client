import json
import os
import shutil
import zlib
from pathlib import Path
from typing import Any, Dict, List, Union


class FileManager:
    """Класс для работы с файлами и архивами"""
    
    @staticmethod
    def load_json_file(file_path: Path) -> Union[Dict[str, Any], List[Any]]:
        """Загружает JSON файл"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {} if file_path.suffix == '.json' else []
        except Exception as e:
            print(f"Ошибка загрузки файла {file_path}: {e}")
            return {} if file_path.suffix == '.json' else []
    
    @staticmethod
    def save_json_file(file_path: Path, data: Union[Dict[str, Any], List[Any]]) -> None:
        """Сохраняет данные в JSON файл"""
        try:
            # Создаем директорию если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения файла {file_path}: {e}")
    
    @staticmethod
    def get_archive_format(file_path: str) -> str:
        """Определяет формат архива по расширению"""
        file_path_lower = file_path.lower()
        
        # Проверяем двойные расширения сначала
        if file_path_lower.endswith('.tar.gz'):
            return 'tgz'
        elif file_path_lower.endswith('.tgz'):
            return 'tgz'
        elif file_path_lower.endswith('.zip'):
            return 'zip'
        elif file_path_lower.endswith('.tar'):
            return 'tar'
        elif file_path_lower.endswith('.gz'):
            return 'gztar'
        else:
            return 'zip'
    
    @staticmethod
    def extract_archive(file_path: str, extract_path: str, archive_format: str) -> None:
        """Распаковывает архив"""
        if archive_format == 'tgz':
            # Специальная обработка для tgz с zlib
            with open(file_path, 'rb') as f:
                producer = zlib.decompressobj(wbits=9)
                tar_data = producer.decompress(f.read()) + producer.flush()
                tar_filepath = f'{os.path.dirname(file_path)}/update.tar'
                with open(tar_filepath, 'wb') as tar_file:
                    tar_file.write(tar_data)
                shutil.unpack_archive(tar_filepath, extract_path, 'tar')
                os.remove(tar_filepath)
        else:
            shutil.unpack_archive(file_path, extract_path, archive_format)
    
    @staticmethod
    def prepare_update_directory(unit_uuid: str) -> str:
        """Подготавливает директорию для обновления"""
        new_version_path = f'tmp/test_units/{unit_uuid}/update'
        shutil.rmtree(new_version_path, ignore_errors=True)
        os.makedirs(new_version_path, exist_ok=True)
        return new_version_path
    
    @staticmethod
    def copy_update_files(source_path: str, destination_path: str) -> None:
        """Копирует файлы обновления"""
        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
