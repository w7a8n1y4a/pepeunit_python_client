from typing import Any, Dict, List, Optional


class Schema:
    
    def __init__(self, schema_data: Dict[str, Any]):
        self._schema_data = schema_data
    
    def update(self, schema_data: Dict[str, Any]) -> None:
        self._schema_data = schema_data
    
    @property
    def input_base_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('input_base_topic', {})
    
    @property
    def output_base_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('output_base_topic', {})
    
    @property
    def input_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('input_topic', {})
    
    @property
    def output_topic(self) -> Dict[str, List[str]]:
        return self._schema_data.get('output_topic', {})
    
    def get_topic_by_key(self, key: str) -> Optional[str]:
        for topic_type in ['output_base_topic', 'input_base_topic']:
            if key in self._schema_data.get(topic_type, {}):
                topics = self._schema_data[topic_type][key]
                if isinstance(topics, list) and topics:
                    return topics[0]
                elif isinstance(topics, str):
                    return topics
        return None
    
    def get_input_topics(self) -> List[str]:
        input_topics = []
        for topic_type in self._schema_data.keys():
            if 'input' in topic_type:
                for topic in self._schema_data[topic_type].keys():
                    topics = self._schema_data[topic_type][topic]
                    if isinstance(topics, list):
                        input_topics.extend(topics)
                    elif isinstance(topics, str):
                        input_topics.append(topics)
        return input_topics
    
    def search_topic_in_schema(self, node_uuid: str) -> Optional[tuple[str, str]]:
        for topic_type in self._schema_data.keys():
            for topic_name in self._schema_data[topic_type].keys():
                topics = self._schema_data[topic_type][topic_name]
                if isinstance(topics, list):
                    for topic in topics:
                        if node_uuid in topic:
                            return topic_type, topic_name
                elif isinstance(topics, str) and node_uuid in topics:
                    return topic_type, topic_name
        return None
