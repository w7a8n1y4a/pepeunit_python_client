"""
Тесты для класса FileManager
"""
import json
import os
import tarfile
import tempfile
import zlib
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest

from pepeunit_client.file_manager import FileManager


class TestFileManager:
    """Тесты для класса FileManager"""

    def test_read_json_success(self, temp_dir):
        """Тест успешного чтения JSON файла"""
        test_data = {"key": "value", "number": 42}
        json_file = os.path.join(temp_dir, "test.json")
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        result = FileManager.read_json(json_file)
        assert result == test_data

    def test_read_json_file_not_found(self):
        """Тест исключения при отсутствии файла"""
        with pytest.raises(FileNotFoundError):
            FileManager.read_json("nonexistent_file.json")

    def test_read_json_invalid_json(self, temp_dir):
        """Тест исключения при невалидном JSON"""
        invalid_json_file = os.path.join(temp_dir, "invalid.json")
        
        with open(invalid_json_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            FileManager.read_json(invalid_json_file)

    def test_write_json_success(self, temp_dir):
        """Тест успешной записи JSON файла"""
        test_data = {"test": "data", "nested": {"key": "value"}}
        json_file = os.path.join(temp_dir, "output.json")
        
        FileManager.write_json(json_file, test_data, indent=2)
        
        assert os.path.exists(json_file)
        with open(json_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        assert result == test_data

    def test_write_json_creates_directory(self, temp_dir):
        """Тест создания директории при записи JSON"""
        nested_dir = os.path.join(temp_dir, "nested", "path")
        json_file = os.path.join(nested_dir, "test.json")
        test_data = {"test": "data"}
        
        FileManager.write_json(json_file, test_data)
        
        assert os.path.exists(json_file)
        assert os.path.exists(nested_dir)

    def test_write_json_custom_indent(self, temp_dir):
        """Тест записи JSON с пользовательским отступом"""
        test_data = {"key": "value"}
        json_file = os.path.join(temp_dir, "indented.json")
        
        FileManager.write_json(json_file, test_data, indent=4)
        
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "    " in content  # Проверяем наличие 4-символьных отступов

    def test_copy_file_success(self, temp_dir):
        """Тест успешного копирования файла"""
        source_file = os.path.join(temp_dir, "source.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        test_content = "Test content"
        
        with open(source_file, 'w') as f:
            f.write(test_content)
        
        FileManager.copy_file(source_file, dest_file)
        
        assert os.path.exists(dest_file)
        with open(dest_file, 'r') as f:
            assert f.read() == test_content

    def test_copy_file_source_not_found(self, temp_dir):
        """Тест исключения при отсутствии исходного файла"""
        source_file = os.path.join(temp_dir, "nonexistent.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        
        with pytest.raises(FileNotFoundError):
            FileManager.copy_file(source_file, dest_file)

    def test_file_exists_true(self, temp_dir):
        """Тест проверки существования файла - файл существует"""
        test_file = os.path.join(temp_dir, "exists.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        assert FileManager.file_exists(test_file) is True

    def test_file_exists_false(self, temp_dir):
        """Тест проверки существования файла - файл не существует"""
        test_file = os.path.join(temp_dir, "nonexistent.txt")
        assert FileManager.file_exists(test_file) is False

    def test_create_directory_success(self, temp_dir):
        """Тест успешного создания директории"""
        new_dir = os.path.join(temp_dir, "new_directory")
        
        FileManager.create_directory(new_dir)
        
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

    def test_create_directory_nested(self, temp_dir):
        """Тест создания вложенных директорий"""
        nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
        
        FileManager.create_directory(nested_dir)
        
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)

    def test_create_directory_already_exists(self, temp_dir):
        """Тест создания уже существующей директории"""
        existing_dir = os.path.join(temp_dir, "existing")
        os.makedirs(existing_dir)
        
        # Не должно вызывать исключение
        FileManager.create_directory(existing_dir)
        assert os.path.exists(existing_dir)

    def test_extract_tar_gz_calls_extract_pepeunit_archive(self, temp_dir):
        """Тест что extract_tar_gz вызывает extract_pepeunit_archive"""
        archive_path = os.path.join(temp_dir, "test.tar.gz")
        extract_path = os.path.join(temp_dir, "extract")
        
        with patch.object(FileManager, 'extract_pepeunit_archive') as mock_extract:
            FileManager.extract_tar_gz(archive_path, extract_path)
            mock_extract.assert_called_once_with(archive_path, extract_path)

    def test_extract_pepeunit_archive_success(self, temp_dir):
        """Тест успешной распаковки pepeunit архива"""
        import io
        # Создаем тестовый tar архив
        tar_content = b"test file content"
        tar_path = os.path.join(temp_dir, "test.tar")
        
        with tarfile.open(tar_path, 'w') as tar:
            info = tarfile.TarInfo("test.txt")
            info.size = len(tar_content)
            tar.addfile(info, io.BytesIO(tar_content))
        
        # Компрессируем с zlib
        with open(tar_path, 'rb') as f:
            tar_data = f.read()
        
        # Создаем сжатие, совместимое с wbits=9 в декомпрессоре
        compressor = zlib.compressobj(level=9, wbits=9)
        compressed_data = compressor.compress(tar_data) + compressor.flush()
        archive_path = os.path.join(temp_dir, "compressed.tar.gz")
        
        with open(archive_path, 'wb') as f:
            f.write(compressed_data)
        
        extract_path = os.path.join(temp_dir, "extracted")
        
        FileManager.extract_pepeunit_archive(archive_path, extract_path)
        
        # Проверяем что файл был извлечен
        extracted_file = os.path.join(extract_path, "test.txt")
        assert os.path.exists(extracted_file)

    @patch('shutil.unpack_archive')
    @patch('os.remove')
    def test_extract_pepeunit_archive_cleanup_temp_file(self, mock_remove, mock_unpack, temp_dir):
        """Тест что временный tar файл удаляется после извлечения"""
        # Мокаем данные
        # Создаем сжатие, совместимое с wbits=9 в декомпрессоре
        compressor = zlib.compressobj(level=9, wbits=9)
        compressed_data = compressor.compress(b"test tar data") + compressor.flush()
        archive_path = os.path.join(temp_dir, "test.tar.gz")
        
        with open(archive_path, 'wb') as f:
            f.write(compressed_data)
        
        extract_path = os.path.join(temp_dir, "extract")
        
        FileManager.extract_pepeunit_archive(archive_path, extract_path)
        
        # Проверяем что временный файл удален
        temp_tar_path = f'{os.path.dirname(archive_path)}/temp_update.tar'
        mock_remove.assert_called_once_with(temp_tar_path)

    def test_copy_directory_contents_success(self, temp_dir):
        """Тест успешного копирования содержимого директории"""
        source_dir = os.path.join(temp_dir, "source")
        dest_dir = os.path.join(temp_dir, "dest")
        
        # Создаем исходную структуру
        os.makedirs(source_dir)
        with open(os.path.join(source_dir, "file1.txt"), 'w') as f:
            f.write("content1")
        
        subdir = os.path.join(source_dir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "file2.txt"), 'w') as f:
            f.write("content2")
        
        FileManager.copy_directory_contents(source_dir, dest_dir)
        
        # Проверяем что все скопировалось
        assert os.path.exists(os.path.join(dest_dir, "file1.txt"))
        assert os.path.exists(os.path.join(dest_dir, "subdir", "file2.txt"))
        
        with open(os.path.join(dest_dir, "file1.txt"), 'r') as f:
            assert f.read() == "content1"

    def test_copy_directory_contents_source_not_found(self, temp_dir):
        """Тест исключения при отсутствии исходной директории"""
        source_dir = os.path.join(temp_dir, "nonexistent")
        dest_dir = os.path.join(temp_dir, "dest")
        
        with pytest.raises(FileNotFoundError):
            FileManager.copy_directory_contents(source_dir, dest_dir)

    def test_copy_directory_contents_creates_destination(self, temp_dir):
        """Тест создания целевой директории при копировании"""
        source_dir = os.path.join(temp_dir, "source")
        dest_dir = os.path.join(temp_dir, "nested", "dest")
        
        os.makedirs(source_dir)
        with open(os.path.join(source_dir, "test.txt"), 'w') as f:
            f.write("test")
        
        FileManager.copy_directory_contents(source_dir, dest_dir)
        
        assert os.path.exists(dest_dir)
        assert os.path.exists(os.path.join(dest_dir, "test.txt"))

    def test_remove_directory_success(self, temp_dir):
        """Тест успешного удаления директории"""
        target_dir = os.path.join(temp_dir, "to_remove")
        os.makedirs(target_dir)
        
        # Создаем файлы в директории
        with open(os.path.join(target_dir, "file.txt"), 'w') as f:
            f.write("test")
        
        assert os.path.exists(target_dir)
        
        FileManager.remove_directory(target_dir)
        
        assert not os.path.exists(target_dir)

    def test_remove_directory_not_exists(self, temp_dir):
        """Тест удаления несуществующей директории"""
        target_dir = os.path.join(temp_dir, "nonexistent")
        
        # Не должно вызывать исключение
        FileManager.remove_directory(target_dir)

    def test_append_to_json_list_new_file(self, temp_dir):
        """Тест добавления в новый JSON файл-список"""
        json_file = os.path.join(temp_dir, "list.json")
        test_item = {"id": 1, "name": "test"}
        
        FileManager.append_to_json_list(json_file, test_item)
        
        assert os.path.exists(json_file)
        result = FileManager.read_json(json_file)
        assert result == [test_item]

    def test_append_to_json_list_existing_file(self, temp_dir):
        """Тест добавления в существующий JSON файл-список"""
        json_file = os.path.join(temp_dir, "list.json")
        initial_data = [{"id": 1, "name": "first"}]
        new_item = {"id": 2, "name": "second"}
        
        FileManager.write_json(json_file, initial_data)
        FileManager.append_to_json_list(json_file, new_item)
        
        result = FileManager.read_json(json_file)
        assert result == initial_data + [new_item]

    def test_append_to_json_list_invalid_existing_data(self, temp_dir):
        """Тест добавления когда существующие данные не список"""
        json_file = os.path.join(temp_dir, "invalid.json")
        invalid_data = {"not": "a list"}
        new_item = {"id": 1, "name": "test"}
        
        FileManager.write_json(json_file, invalid_data)
        FileManager.append_to_json_list(json_file, new_item)
        
        result = FileManager.read_json(json_file)
        assert result == [new_item]  # Должно создать новый список
