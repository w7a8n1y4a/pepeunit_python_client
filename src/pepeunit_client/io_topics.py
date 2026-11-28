from dataclasses import dataclass, field
from uuid import UUID

import yaml


@dataclass(frozen=True)
class IOTopic:
    topic: str
    qos: int = 0

    def __post_init__(self) -> None:
        self.uuid_from_topic(self.topic)
        if type(self.qos) is not int or self.qos not in (0, 1):
            raise ValueError("IO topic QoS must be 0 or 1")

    @staticmethod
    def uuid_from_topic(topic: str) -> str:
        if not isinstance(topic, str):
            raise ValueError("IO topic must be a string")
        domain, _, io_uuid = topic.partition("/")
        if not domain or any(char in domain for char in "+#\0"):
            raise ValueError("IO topic must have the form domain/uuid")
        try:
            if str(UUID(io_uuid)) == io_uuid:
                return io_uuid
        except ValueError:
            pass
        raise ValueError("IO topic must have the form domain/uuid")


@dataclass(frozen=True)
class IOTopics:
    input: dict[str, IOTopic] = field(default_factory=dict)
    output: dict[str, IOTopic] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, content: bytes) -> "IOTopics":
        document = yaml.safe_load(content)
        if (
            not isinstance(document, dict)
            or type(document.get("version")) is not int
            or document["version"] != 1
        ):
            raise ValueError("Unsupported io_topics.yml version")
        return cls(
            cls.read_topics(document, "input"), cls.read_topics(document, "output")
        )

    @staticmethod
    def read_topics(document: dict, direction: str) -> dict[str, IOTopic]:
        entries = document.get(direction)
        if not isinstance(entries, dict):
            raise ValueError(f"io_topics.yml must contain a {direction} mapping")
        topics = {}
        for name, entry in entries.items():
            if (
                not isinstance(name, str)
                or not isinstance(entry, dict)
                or "topic" not in entry
            ):
                raise ValueError(f"Invalid {direction} entry in io_topics.yml")
            topics[name] = IOTopic(entry["topic"], entry.get("qos", 0))
        return topics

    def input_name(self, topic: str) -> str | None:
        return next(
            (name for name, io in self.input.items() if io.topic == topic), None
        )
