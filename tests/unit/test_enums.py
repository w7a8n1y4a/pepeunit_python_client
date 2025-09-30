"""
Тесты для модуля enums.py
"""
import pytest
from pepeunit_client.enums import (
    LogLevel, SearchTopicType, SearchScope, 
    DestinationTopicType, BaseInputTopicType, BaseOutputTopicType, RestartMode
)


class TestLogLevel:
    """Тесты для перечисления LogLevel"""
    
    def test_log_level_values(self):
        """Тест корректности значений уровней логирования"""
        assert LogLevel.DEBUG.value == 'Debug'
        assert LogLevel.INFO.value == 'Info'
        assert LogLevel.WARNING.value == 'Warning'
        assert LogLevel.ERROR.value == 'Error'
        assert LogLevel.CRITICAL.value == 'Critical'
    
    def test_get_int_level_mapping(self):
        """Тест преобразования уровней в числовые значения"""
        assert LogLevel.DEBUG.get_int_level() == 0
        assert LogLevel.INFO.get_int_level() == 1
        assert LogLevel.WARNING.get_int_level() == 2
        assert LogLevel.ERROR.get_int_level() == 3
        assert LogLevel.CRITICAL.get_int_level() == 4
    
    def test_log_level_ordering(self):
        """Тест правильного порядка уровней логирования"""
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        int_levels = [level.get_int_level() for level in levels]
        assert int_levels == sorted(int_levels)
    
    def test_all_levels_have_int_mapping(self):
        """Тест что для всех уровней есть числовое представление"""
        for level in LogLevel:
            assert isinstance(level.get_int_level(), int)
            assert level.get_int_level() >= 0


class TestSearchTopicType:
    """Тесты для перечисления SearchTopicType"""
    
    def test_search_topic_type_values(self):
        """Тест корректности значений типов поиска топиков"""
        assert SearchTopicType.UNIT_NODE_UUID.value == 'unit_node_uuid'
        assert SearchTopicType.FULL_NAME.value == 'full_name'
    
    def test_search_topic_type_count(self):
        """Тест количества типов поиска"""
        assert len(SearchTopicType) == 2


class TestSearchScope:
    """Тесты для перечисления SearchScope"""
    
    def test_search_scope_values(self):
        """Тест корректности значений области поиска"""
        assert SearchScope.ALL.value == 'all'
        assert SearchScope.INPUT.value == 'input'
        assert SearchScope.OUTPUT.value == 'output'
    
    def test_search_scope_count(self):
        """Тест количества областей поиска"""
        assert len(SearchScope) == 3


class TestDestinationTopicType:
    """Тесты для перечисления DestinationTopicType"""
    
    def test_destination_topic_type_values(self):
        """Тест корректности значений типов назначения топиков"""
        assert DestinationTopicType.INPUT_BASE_TOPIC.value == 'input_base_topic'
        assert DestinationTopicType.OUTPUT_BASE_TOPIC.value == 'output_base_topic'
        assert DestinationTopicType.INPUT_TOPIC.value == 'input_topic'
        assert DestinationTopicType.OUTPUT_TOPIC.value == 'output_topic'
    
    def test_destination_topic_type_count(self):
        """Тест количества типов назначения"""
        assert len(DestinationTopicType) == 4


class TestBaseInputTopicType:
    """Тесты для перечисления BaseInputTopicType"""
    
    def test_base_input_topic_type_values(self):
        """Тест корректности значений базовых входящих топиков"""
        assert BaseInputTopicType.UPDATE_PEPEUNIT.value == 'update/pepeunit'
        assert BaseInputTopicType.ENV_UPDATE_PEPEUNIT.value == 'env_update/pepeunit'
        assert BaseInputTopicType.SCHEMA_UPDATE_PEPEUNIT.value == 'schema_update/pepeunit'
        assert BaseInputTopicType.LOG_SYNC_PEPEUNIT.value == 'log_sync/pepeunit'
    
    def test_base_input_topic_type_count(self):
        """Тест количества базовых входящих топиков"""
        assert len(BaseInputTopicType) == 4
    
    def test_all_values_contain_pepeunit(self):
        """Тест что все базовые входящие топики содержат 'pepeunit'"""
        for topic_type in BaseInputTopicType:
            assert 'pepeunit' in topic_type.value


class TestBaseOutputTopicType:
    """Тесты для перечисления BaseOutputTopicType"""
    
    def test_base_output_topic_type_values(self):
        """Тест корректности значений базовых исходящих топиков"""
        assert BaseOutputTopicType.LOG_PEPEUNIT.value == 'log/pepeunit'
        assert BaseOutputTopicType.STATE_PEPEUNIT.value == 'state/pepeunit'
    
    def test_base_output_topic_type_count(self):
        """Тест количества базовых исходящих топиков"""
        assert len(BaseOutputTopicType) == 2
    
    def test_all_values_contain_pepeunit(self):
        """Тест что все базовые исходящие топики содержат 'pepeunit'"""
        for topic_type in BaseOutputTopicType:
            assert 'pepeunit' in topic_type.value


class TestRestartMode:
    """Тесты для перечисления RestartMode"""
    
    def test_restart_mode_values(self):
        """Тест корректности значений режимов перезапуска"""
        assert RestartMode.RESTART_POPEN.value == 'restart_popen'
        assert RestartMode.RESTART_EXEC.value == 'restart_exec'
        assert RestartMode.ENV_SCHEMA_ONLY.value == 'env_schema_only'
        assert RestartMode.NO_RESTART.value == 'no_restart'
    
    def test_restart_mode_count(self):
        """Тест количества режимов перезапуска"""
        assert len(RestartMode) == 4
    
    def test_restart_mode_uniqueness(self):
        """Тест уникальности значений режимов перезапуска"""
        values = [mode.value for mode in RestartMode]
        assert len(values) == len(set(values))


class TestEnumIntegration:
    """Интеграционные тесты перечислений"""
    
    def test_enum_uniqueness(self):
        """Тест уникальности значений в каждом перечислении"""
        enums_to_test = [
            LogLevel, SearchTopicType, SearchScope, 
            DestinationTopicType, BaseInputTopicType, BaseOutputTopicType, RestartMode
        ]
        
        for enum_class in enums_to_test:
            values = [item.value for item in enum_class]
            assert len(values) == len(set(values)), f"Duplicate values found in {enum_class.__name__}"
    
    def test_enum_string_representation(self):
        """Тест строкового представления перечислений"""
        # Проверяем что все enum элементы имеют корректное строковое представление
        test_cases = [
            (LogLevel.DEBUG, "LogLevel.DEBUG"),
            (SearchTopicType.UNIT_NODE_UUID, "SearchTopicType.UNIT_NODE_UUID"),
            (SearchScope.ALL, "SearchScope.ALL"),
            (DestinationTopicType.INPUT_BASE_TOPIC, "DestinationTopicType.INPUT_BASE_TOPIC"),
            (BaseInputTopicType.UPDATE_PEPEUNIT, "BaseInputTopicType.UPDATE_PEPEUNIT"),
            (BaseOutputTopicType.LOG_PEPEUNIT, "BaseOutputTopicType.LOG_PEPEUNIT"),
            (RestartMode.RESTART_POPEN, "RestartMode.RESTART_POPEN")
        ]
        
        for enum_item, expected_repr in test_cases:
            assert str(enum_item) == expected_repr
