"""
Тесты для класса SchemaManager
"""
import os
from unittest.mock import patch, Mock

import pytest

from pepeunit_client.schema_manager import SchemaManager
from pepeunit_client.enums import SearchTopicType, SearchScope, DestinationTopicType


class TestSchemaManager:
    """Тесты для класса SchemaManager"""

    def test_init_loads_schema(self, schema_file, sample_schema_data):
        """Тест что инициализация загружает схему"""
        schema_manager = SchemaManager(schema_file)
        
        assert schema_manager.schema_file_path == schema_file
        assert schema_manager._schema_data == sample_schema_data

    @patch('pepeunit_client.file_manager.FileManager.read_json')
    def test_load_schema(self, mock_read_json, sample_schema_data):
        """Тест загрузки схемы"""
        mock_read_json.return_value = sample_schema_data
        
        schema_manager = SchemaManager('test_schema.json')
        result = schema_manager._load_schema()
        
        assert result == sample_schema_data
        mock_read_json.assert_called_with('test_schema.json')

    @patch('pepeunit_client.file_manager.FileManager.read_json')
    def test_update_from_file(self, mock_read_json, mock_schema_manager):
        """Тест обновления схемы из файла"""
        new_schema_data = {'new': 'schema'}
        mock_read_json.return_value = new_schema_data
        
        mock_schema_manager.update_from_file()
        
        assert mock_schema_manager._schema_data == new_schema_data
        mock_read_json.assert_called_with(mock_schema_manager.schema_file_path)

    @patch('pepeunit_client.file_manager.FileManager.write_json')
    def test_update_schema(self, mock_write_json, mock_schema_manager):
        """Тест обновления схемы новыми данными"""
        new_schema_data = {'updated': 'schema'}
        
        mock_schema_manager.update_schema(new_schema_data)
        
        assert mock_schema_manager._schema_data == new_schema_data
        mock_write_json.assert_called_with(mock_schema_manager.schema_file_path, new_schema_data)

    def test_input_base_topic_property(self, mock_schema_manager, sample_schema_data):
        """Тест свойства input_base_topic"""
        result = mock_schema_manager.input_base_topic
        
        expected = sample_schema_data[DestinationTopicType.INPUT_BASE_TOPIC.value]
        assert result == expected

    def test_output_base_topic_property(self, mock_schema_manager, sample_schema_data):
        """Тест свойства output_base_topic"""
        result = mock_schema_manager.output_base_topic
        
        expected = sample_schema_data[DestinationTopicType.OUTPUT_BASE_TOPIC.value]
        assert result == expected

    def test_input_topic_property(self, mock_schema_manager, sample_schema_data):
        """Тест свойства input_topic"""
        result = mock_schema_manager.input_topic
        
        expected = sample_schema_data[DestinationTopicType.INPUT_TOPIC.value]
        assert result == expected

    def test_output_topic_property(self, mock_schema_manager, sample_schema_data):
        """Тест свойства output_topic"""
        result = mock_schema_manager.output_topic
        
        expected = sample_schema_data[DestinationTopicType.OUTPUT_TOPIC.value]
        assert result == expected

    def test_properties_with_missing_keys(self, schema_file):
        """Тест свойств когда ключи отсутствуют в схеме"""
        empty_schema = {}
        
        with patch('pepeunit_client.file_manager.FileManager.read_json', return_value=empty_schema):
            schema_manager = SchemaManager(schema_file)
            
            assert schema_manager.input_base_topic == {}
            assert schema_manager.output_base_topic == {}
            assert schema_manager.input_topic == {}
            assert schema_manager.output_topic == {}

    def test_get_sections_by_scope_all(self, mock_schema_manager):
        """Тест получения секций для области ALL"""
        result = mock_schema_manager._get_sections_by_scope(SearchScope.ALL)
        
        expected = [DestinationTopicType.INPUT_TOPIC.value, DestinationTopicType.OUTPUT_TOPIC.value]
        assert result == expected

    def test_get_sections_by_scope_input(self, mock_schema_manager):
        """Тест получения секций для области INPUT"""
        result = mock_schema_manager._get_sections_by_scope(SearchScope.INPUT)
        
        expected = [DestinationTopicType.INPUT_TOPIC.value]
        assert result == expected

    def test_get_sections_by_scope_output(self, mock_schema_manager):
        """Тест получения секций для области OUTPUT"""
        result = mock_schema_manager._get_sections_by_scope(SearchScope.OUTPUT)
        
        expected = [DestinationTopicType.OUTPUT_TOPIC.value]
        assert result == expected

    def test_get_sections_by_scope_unknown(self, mock_schema_manager):
        """Тест получения секций для неизвестной области"""
        # Создаем фиктивный enum-like объект
        class UnknownScope:
            value = 'unknown'
        
        result = mock_schema_manager._get_sections_by_scope(UnknownScope())
        
        assert result == []

    def test_extract_uuid_from_topic_valid(self, mock_schema_manager):
        """Тест извлечения UUID из топика"""
        topic_url = "test/uuid-123/some/path"
        
        result = mock_schema_manager._extract_uuid_from_topic(topic_url)
        
        assert result == "uuid-123"

    def test_extract_uuid_from_topic_short_path(self, mock_schema_manager):
        """Тест извлечения UUID из короткого пути"""
        topic_url = "test"
        
        result = mock_schema_manager._extract_uuid_from_topic(topic_url)
        
        assert result is None

    def test_extract_uuid_from_topic_single_slash(self, mock_schema_manager):
        """Тест извлечения UUID из пути с одним слешем"""
        topic_url = "test/"
        
        result = mock_schema_manager._extract_uuid_from_topic(topic_url)
        
        assert result == ""

    def test_search_uuid_in_topic_section_found(self, mock_schema_manager):
        """Тест поиска UUID в секции топиков - найден"""
        section = DestinationTopicType.INPUT_TOPIC.value
        test_uuid = "test-uuid"
        
        # Мокаем данные схемы
        mock_schema_manager._schema_data = {
            section: {
                "found_topic": [f"prefix/{test_uuid}/suffix"],
                "other_topic": ["other/different-uuid/path"]
            }
        }
        
        result = mock_schema_manager._search_uuid_in_topic_section(section, test_uuid)
        
        assert result == "found_topic"

    def test_search_uuid_in_topic_section_not_found(self, mock_schema_manager):
        """Тест поиска UUID в секции топиков - не найден"""
        section = DestinationTopicType.INPUT_TOPIC.value
        test_uuid = "nonexistent-uuid"
        
        mock_schema_manager._schema_data = {
            section: {
                "topic1": ["prefix/other-uuid/suffix"],
                "topic2": ["another/different-uuid/path"]
            }
        }
        
        result = mock_schema_manager._search_uuid_in_topic_section(section, test_uuid)
        
        assert result is None

    def test_search_uuid_in_topic_section_empty_section(self, mock_schema_manager):
        """Тест поиска UUID в пустой секции"""
        section = "nonexistent_section"
        test_uuid = "test-uuid"
        
        result = mock_schema_manager._search_uuid_in_topic_section(section, test_uuid)
        
        assert result is None

    def test_search_topic_name_in_section_found(self, mock_schema_manager):
        """Тест поиска имени топика в секции - найден"""
        section = DestinationTopicType.OUTPUT_TOPIC.value
        topic_name = "exact/topic/name"
        
        mock_schema_manager._schema_data = {
            section: {
                "found_key": [topic_name, "other/topic"],
                "other_key": ["different/topic"]
            }
        }
        
        result = mock_schema_manager._search_topic_name_in_section(section, topic_name)
        
        assert result == "found_key"

    def test_search_topic_name_in_section_not_found(self, mock_schema_manager):
        """Тест поиска имени топика в секции - не найден"""
        section = DestinationTopicType.OUTPUT_TOPIC.value
        topic_name = "nonexistent/topic"
        
        mock_schema_manager._schema_data = {
            section: {
                "key1": ["different/topic"],
                "key2": ["another/topic"]
            }
        }
        
        result = mock_schema_manager._search_topic_name_in_section(section, topic_name)
        
        assert result is None

    def test_find_topic_by_unit_node_uuid_found(self, mock_schema_manager):
        """Тест поиска топика по UUID узла - найден"""
        search_uuid = "target-uuid"
        
        with patch.object(mock_schema_manager, '_get_sections_by_scope') as mock_get_sections, \
             patch.object(mock_schema_manager, '_search_uuid_in_topic_section') as mock_search_uuid:
            
            mock_get_sections.return_value = ["section1", "section2"]
            mock_search_uuid.side_effect = [None, "found_topic"]
            
            result = mock_schema_manager.find_topic_by_unit_node(
                search_uuid, SearchTopicType.UNIT_NODE_UUID, SearchScope.ALL
            )
            
            assert result == "found_topic"
            assert mock_search_uuid.call_count == 2

    def test_find_topic_by_unit_node_full_name_found(self, mock_schema_manager):
        """Тест поиска топика по полному имени - найден"""
        topic_name = "full/topic/name"
        
        with patch.object(mock_schema_manager, '_get_sections_by_scope') as mock_get_sections, \
             patch.object(mock_schema_manager, '_search_topic_name_in_section') as mock_search_name:
            
            mock_get_sections.return_value = ["section1"]
            mock_search_name.return_value = "found_topic"
            
            result = mock_schema_manager.find_topic_by_unit_node(
                topic_name, SearchTopicType.FULL_NAME, SearchScope.INPUT
            )
            
            assert result == "found_topic"
            mock_search_name.assert_called_once_with("section1", topic_name)

    def test_find_topic_by_unit_node_not_found(self, mock_schema_manager):
        """Тест поиска топика - не найден"""
        with patch.object(mock_schema_manager, '_get_sections_by_scope') as mock_get_sections, \
             patch.object(mock_schema_manager, '_search_uuid_in_topic_section') as mock_search_uuid:
            
            mock_get_sections.return_value = ["section1", "section2"]
            mock_search_uuid.return_value = None
            
            result = mock_schema_manager.find_topic_by_unit_node(
                "nonexistent", SearchTopicType.UNIT_NODE_UUID, SearchScope.ALL
            )
            
            assert result is None

    def test_find_topic_by_unit_node_unknown_search_type(self, mock_schema_manager):
        """Тест поиска топика с неизвестным типом поиска"""
        class UnknownSearchType:
            value = 'unknown'
        
        with patch.object(mock_schema_manager, '_get_sections_by_scope') as mock_get_sections:
            mock_get_sections.return_value = ["section1"]
            
            result = mock_schema_manager.find_topic_by_unit_node(
                "test", UnknownSearchType(), SearchScope.ALL
            )
            
            assert result is None

    def test_integration_real_schema_search(self, temp_dir):
        """Интеграционный тест с реальной схемой"""
        schema_data = {
            "input_topic": {
                "sensor_data": ["sensors/unit-123/data", "sensors/unit-456/data"],
                "commands": ["commands/unit-123/execute"]
            },
            "output_topic": {
                "alerts": ["alerts/unit-123/critical"],
                "status": ["status/unit-789/report"]
            }
        }
        
        schema_file = os.path.join(temp_dir, 'integration_schema.json')
        
        import json
        with open(schema_file, 'w') as f:
            json.dump(schema_data, f)
        
        schema_manager = SchemaManager(schema_file)
        
        # Поиск по UUID
        result = schema_manager.find_topic_by_unit_node(
            "unit-123", SearchTopicType.UNIT_NODE_UUID, SearchScope.ALL
        )
        assert result == "sensor_data"  # Первое совпадение
        
        # Поиск по полному имени
        result = schema_manager.find_topic_by_unit_node(
            "commands/unit-123/execute", SearchTopicType.FULL_NAME, SearchScope.INPUT
        )
        assert result == "commands"
        
        # Поиск в конкретной области
        result = schema_manager.find_topic_by_unit_node(
            "unit-789", SearchTopicType.UNIT_NODE_UUID, SearchScope.OUTPUT
        )
        assert result == "status"

    def test_schema_properties_integration(self, temp_dir):
        """Интеграционный тест свойств схемы"""
        complex_schema = {
            "input_base_topic": {
                "base_input1": ["topic1", "topic2"],
                "base_input2": ["topic3"]
            },
            "output_base_topic": {
                "base_output1": ["topic4"]
            },
            "input_topic": {
                "user_input1": ["topic5", "topic6"]
            },
            "output_topic": {
                "user_output1": ["topic7"],
                "user_output2": ["topic8", "topic9"]
            }
        }
        
        schema_file = os.path.join(temp_dir, 'complex_schema.json')
        
        import json
        with open(schema_file, 'w') as f:
            json.dump(complex_schema, f)
        
        schema_manager = SchemaManager(schema_file)
        
        # Проверяем все свойства
        assert schema_manager.input_base_topic == complex_schema["input_base_topic"]
        assert schema_manager.output_base_topic == complex_schema["output_base_topic"]
        assert schema_manager.input_topic == complex_schema["input_topic"]
        assert schema_manager.output_topic == complex_schema["output_topic"]
        
        # Проверяем что изменения в исходных данных не влияют на схему
        complex_schema["input_base_topic"]["new_key"] = ["new_topic"]
        assert "new_key" not in schema_manager.input_base_topic
