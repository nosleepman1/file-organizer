import os
import json
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE_NAME = "organizer_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "deepseek_api_key": "",
    "deepseek_model": "deepseek-chat",
    "deepseek_custom_prompt": "Classer les fichiers par sujet sémantique et type de projet de manière propre et structurée.",
    "auto_organize_on_watch": False,
    "watcher_mode": "type",
    "autostart_enabled": False,
    "default_target_dir": "DOWNLOADS",
    "surgical_filters": {
        "regex": "",
        "min_size_mb": 0,
        "max_size_mb": 0,
        "date_days": 0
    }
}

class ConfigManager:
    def __init__(self, base_dir: str = None):
        if base_dir:
            self.config_dir = Path(base_dir)
        else:
            self.config_dir = Path.home() / ".smart_file_organizer"
        
        self.config_file = self.config_dir / CONFIG_FILE_NAME
        self._ensure_config_dir()
        self.config_data = self.load_config()

    def _ensure_config_dir(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Erreur création dossier de config: {e}")

    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier JSON ou initialise avec les valeurs par défaut."""
        if not self.config_file.exists():
            self.save_config(DEFAULT_CONFIG)
            return dict(DEFAULT_CONFIG)

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config = dict(DEFAULT_CONFIG)
                config.update(loaded)
                return config
        except Exception as e:
            print(f"Erreur chargement config: {e}")
            return dict(DEFAULT_CONFIG)

    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Sauvegarde la configuration dans le fichier JSON."""
        if config is not None:
            self.config_data = config

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        self.config_data[key] = value
        return self.save_config()

    def get_masked_api_key(self) -> str:
        key = self.get("deepseek_api_key", "")
        if not key:
            return ""
        if len(key) <= 8:
            return "********"
        return f"{key[:4]}...{key[-4:]}"

# Singleton pour accès facile
global_config = ConfigManager()
