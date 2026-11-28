import base64
import json
from pathlib import Path
from typing import Any

from .file_manager import FileManager


class Settings:
    DEFAULTS = {
        "PU_DOMAIN": "",
        "PU_HTTP_TYPE": "https",
        "PU_APP_PREFIX": "/pepeunit",
        "PU_API_ACTUAL_PREFIX": "/api/v1",
        "PU_MQTT_HOST": "",
        "PU_MQTT_PORT": 1883,
        "PU_MQTT_PING_INTERVAL": 20,
        "PU_MQTT_KEEPALIVE": 60,
        "PU_AUTH_TOKEN": "",
        "PU_SECRET_KEY": "",
        "PU_ENCRYPT_KEY": "",
        "PU_STATE_SEND_INTERVAL": 60,
        "PU_MIN_LOG_LEVEL": "Debug",
        "PU_MAX_LOG_LENGTH": 64,
        "PU_COMMIT_VERSION": "",
    }

    def __init__(self, env_file_path: str) -> None:
        self._env_file = Path(env_file_path)
        self._values: dict[str, Any] = {}
        self.load_from_file()

    def __getattr__(self, name: str) -> Any:
        if name in self._values:
            return self._values[name]
        try:
            return self.DEFAULTS[name]
        except KeyError:
            raise AttributeError(name) from None

    @property
    def unit_uuid(self) -> str:
        token_parts = self.PU_AUTH_TOKEN.split('.')
        if len(token_parts) != 3:
            raise ValueError("Invalid JWT token format")
        
        payload = token_parts[1]
        payload += '=' * (-len(payload) % 4)
        
        decoded_payload = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_payload)
        
        return payload_data['uuid']
    
    def load_from_file(self) -> None:
        if self._env_file.is_file():
            self._apply_values(FileManager.read_env(self._env_file))

    def apply_env_update(self, downloaded: Path) -> None:
        content = downloaded.read_text(encoding="utf-8")
        values = FileManager.parse_env(content)
        version_key = "PU_COMMIT_VERSION"
        try:
            installed_version = FileManager.read_env(self._env_file).get(version_key)
        except (OSError, ValueError):
            installed_version = self._values.get(version_key)

        if (
            isinstance(installed_version, str)
            and installed_version
            and values.get(version_key) != installed_version
        ):
            prefix = f"{version_key}="
            lines = [line for line in content.split("\n") if not line.startswith(prefix)]
            lines.insert(0, prefix + json.dumps(installed_version))
            downloaded.write_text("\n".join(lines), encoding="utf-8")
            values[version_key] = installed_version

        downloaded.replace(self._env_file)
        self._apply_values(values)

    def _apply_values(self, values: dict[str, Any]) -> None:
        env_names = self._values.keys() | values.keys()
        self._values = values
        attributes = vars(self)
        for name in env_names & attributes.keys():
            if not name.startswith("_"):
                del attributes[name]
