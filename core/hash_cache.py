import os
import json
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any

HASH_CACHE_FILE = "hash_cache.json"

class HashCacheManager:
    """Gère un cache disque thread-safe des empreintes SHA256 basées sur (mtime, size)."""

    def __init__(self, base_dir: str = None):
        if base_dir:
            self.cache_dir = Path(base_dir)
        else:
            self.cache_dir = Path.home() / ".smart_file_organizer"

        self.cache_file = self.cache_dir / HASH_CACHE_FILE
        self._lock = threading.Lock()
        self._ensure_cache_dir()
        self.cache_data: Dict[str, Dict[str, Any]] = self.load_cache()

    def _ensure_cache_dir(self):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def load_cache(self) -> Dict[str, Dict[str, Any]]:
        if not self.cache_file.exists():
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_cache(self) -> bool:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_hash(self, file_path: Path) -> str:
        """Retourne l'empreinte SHA256 depuis le cache si le fichier n'a pas changé, sinon la calcule."""
        fp = Path(file_path).resolve()
        if not fp.exists() or not fp.is_file():
            return ""

        try:
            stat = fp.stat()
            size = stat.st_size
            mtime = stat.st_mtime
        except Exception:
            return ""

        path_str = str(fp)

        with self._lock:
            cached = self.cache_data.get(path_str)
            if cached and cached.get("size") == size and cached.get("mtime") == mtime:
                return cached.get("sha256", "")

        # Calcul effectif du SHA256
        hasher = hashlib.sha256()
        try:
            with open(fp, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            digest = hasher.hexdigest()

            with self._lock:
                self.cache_data[path_str] = {
                    "size": size,
                    "mtime": mtime,
                    "sha256": digest
                }
                self.save_cache()

            return digest
        except Exception:
            return ""

# Singleton pour le cache global
global_hash_cache = HashCacheManager()
