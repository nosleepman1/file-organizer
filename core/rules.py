import os
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
    "desktop.ini", ".DS_Store", "thumbs.db", "sort_history.json", ".git", ".gitignore"
}

def get_category_for_extension(ext: str, custom_rules: dict = None) -> str:
    """
    Détermine la catégorie d'un fichier en fonction de son extension.
    """
    ext = ext.lower().lstrip(".")
    if not ext:
        return "Divers"
    
    rules = custom_rules if custom_rules else DEFAULT_CATEGORIES
    
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
