import os
import json
from pathlib import Path

# Catégories de tri par défaut avec leurs extensions associées
DEFAULT_CATEGORIES = {
    "Documents": [
        "pdf", "doc", "docx", "txt", "rtf", "odt", "xls", "xlsx", 
        "ppt", "pptx", "csv", "md", "epub", "pages", "numbers", "key"
    ],
    "Images": [
        "jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico", 
        "tiff", "raw", "psd", "ai", "heic"
    ],
    "Vidéos": [
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "3gp"
    ],
    "Audio": [
        "mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "mid"
    ],
    "Archives": [
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso", "tgz"
    ],
    "Code & Dev": [
        "py", "js", "ts", "jsx", "tsx", "html", "css", "scss", "json", 
        "xml", "cpp", "c", "h", "cs", "java", "php", "rb", "sql", "sh", 
        "bat", "ps1", "yaml", "yml", "env", "toml"
    ],
    "Exécutables & Installeurs": [
        "exe", "msi", "apk", "appimage", "dmg", "deb", "rpm"
    ]
}

# Fichiers à toujours ignorer (fichiers système ou de configuration)
IGNORED_FILES = {
    "desktop.ini", ".DS_Store", "thumbs.db", "sort_history.json", ".sort_history.json", ".git", ".gitignore", "custom_rules.json"
}

# Extensions temporaires à ignorer (ex: téléchargements en cours)
TEMP_EXTENSIONS = {
    "crdownload", "part", "tmp", "download", "partial"
}

CUSTOM_RULES_FILE = "custom_rules.json"

def load_custom_rules(base_dir: str = None) -> dict:
    """Charge les règles personnalisées depuis custom_rules.json s'il existe, sinon retourne DEFAULT_CATEGORIES."""
    rule_file = Path(base_dir) / CUSTOM_RULES_FILE if base_dir else Path.cwd() / CUSTOM_RULES_FILE
    if rule_file.exists():
        try:
            with open(rule_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
                if isinstance(rules, dict) and rules:
                    return rules
        except Exception:
            pass
    return dict(DEFAULT_CATEGORIES)

def save_custom_rules(rules: dict, base_dir: str = None) -> bool:
    """Enregistre les règles personnalisées dans custom_rules.json."""
    rule_file = Path(base_dir) / CUSTOM_RULES_FILE if base_dir else Path.cwd() / CUSTOM_RULES_FILE
    try:
        with open(rule_file, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des règles : {e}")
        return False

def is_temp_or_ignored(file_path: Path) -> bool:
    """Vérifie si un fichier est temporaire ou doit être ignoré."""
    name = file_path.name
    if name in IGNORED_FILES or name.startswith("."):
        return True
    if name.startswith("~$") or name.startswith(".~"):
        return True
    ext = file_path.suffix.lower().lstrip(".")
    if ext in TEMP_EXTENSIONS:
        return True
    return False

def get_category_for_extension(ext: str, custom_rules: dict = None) -> str:
    """
    Détermine la catégorie d'un fichier en fonction de son extension.
    """
    ext = ext.lower().lstrip(".")
    if not ext:
        return "Divers"
    
    rules = custom_rules if custom_rules is not None else load_custom_rules()
    
    for category, extensions in rules.items():
        if ext in [e.lower() for e in extensions]:
            return category
            
    return "Autres"

def get_date_subfolder(file_path: Path) -> str:
    """
    Retourne un sous-dossier au format Année-Mois basé sur la date de modification.
    Ex: 2026-07
    """
    try:
        mtime = file_path.stat().st_mtime
        from datetime import datetime
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m")
    except Exception:
        return "Inconnu"

def get_size_subfolder(file_path: Path) -> str:
    """
    Retourne une catégorie basée sur la taille du fichier.
    """
    try:
        size_bytes = file_path.stat().st_size
        mb = size_bytes / (1024 * 1024)
        if mb < 1:
            return "Petits (< 1Mo)"
        elif mb < 100:
            return "Moyens (1Mo - 100Mo)"
        elif mb < 1000:
            return "Grands (100Mo - 1Go)"
        else:
            return "Très Grands (> 1Go)"
    except Exception:
        return "Taille Inconnue"
