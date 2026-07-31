import os
import json
import base64
import uuid
import platform
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE_NAME = "organizer_config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ai_provider": "deepseek",          # 'deepseek', 'ollama', 'openai', 'custom'
    "deepseek_api_key": "",
    "deepseek_model": "deepseek-chat",
    "openai_api_key": "",
    "openai_model": "gpt-4o-mini",
    "ollama_endpoint": "http://localhost:11434",
    "ollama_model": "llama3:latest",
    "custom_endpoint": "",
    "deepseek_custom_prompt": "Classer les fichiers par sujet sémantique et type de projet de manière propre et structurée.",
    "content_aware_parsing": True,      # Lire un extrait du contenu des fichiers texte/PDF pour l'IA
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

def _get_machine_key() -> bytes:
    node = str(uuid.getnode()) + platform.node()
    return node.encode('utf-8')

def _obfuscate(text: str) -> str:
    if not text or text.startswith("ENC:"):
        return text
    key = _get_machine_key()
    text_bytes = text.encode('utf-8')
    obf = bytes([b ^ key[i % len(key)] for i, b in enumerate(text_bytes)])
    return "ENC:" + base64.b64encode(obf).decode('ascii')

def _deobfuscate(text: str) -> str:
    if not text or not text.startswith("ENC:"):
        return text
    try:
        raw_b64 = text[4:]
        obf = base64.b64decode(raw_b64.encode('ascii'))
        key = _get_machine_key()
        text_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(obf)])
        return text_bytes.decode('utf-8')
    except Exception:
        return text

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
        """Sauvegarde la configuration dans le fichier JSON avec obfuscation des clés sensibles."""
        if config is not None:
            self.config_data = config

        try:
            to_save = dict(self.config_data)
            # Obfusquer les clés sensibles avant sauvegarde sur disque
            for key_name in ["deepseek_api_key", "openai_api_key"]:
                if key_name in to_save and to_save[key_name]:
                    to_save[key_name] = _obfuscate(to_save[key_name])

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        val = self.config_data.get(key, default)
        if isinstance(val, str) and val.startswith("ENC:"):
            return _deobfuscate(val)
        return val

    def set(self, key: str, value: Any) -> bool:
        self.config_data[key] = value
        return self.save_config()

    def get_masked_api_key(self, key_name: str = "deepseek_api_key") -> str:
        key = self.get(key_name, "")
        if not key:
            return ""
        if len(key) <= 8:
            return "********"
        return f"{key[:4]}...{key[-4:]}"

# Singleton pour accès facile
global_config = ConfigManager()
