import os
import shutil
from pathlib import Path
from datetime import datetime
from core.rules import (
    get_category_for_extension, 
    get_date_subfolder, 
    get_size_subfolder, 
    DEFAULT_CATEGORIES, 
    IGNORED_FILES
)
from core.history import HistoryManager

def format_size(bytes_size: int) -> str:
    """Formate une taille en octets en chaîne lisible (Ko, Mo, Go)."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

class FileOrganizer:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.history_manager = HistoryManager(str(self.target_dir))

    def is_valid_directory(self) -> bool:
        return self.target_dir.exists() and self.target_dir.is_dir()

    def scan(self, mode: str = "type", custom_rules: dict = None, recursive: bool = False) -> list:
        """
        Scanne le dossier et renvoie une liste d'actions proposées (Dry-Run / Aperçu).
        mode: 'type' (par catégorie), 'date' (par Année-Mois), ou 'size' (par taille)
        """
        if not self.is_valid_directory():
            return []

        proposed_actions = []
        known_categories = list((custom_rules or DEFAULT_CATEGORIES).keys()) + ["Autres", "Divers"]

        def _should_skip_item(item_path: Path) -> bool:
            if item_path.name in IGNORED_FILES:
                return True
            if item_path.name.startswith("."):
                return True
            # Ignorer les dossiers de catégories déjà créés à la racine du tri
            if item_path.is_dir() and item_path.parent == self.target_dir and item_path.name in known_categories:
                return True
            return False

        files_to_process = []
        if recursive:
            for root, _, files in os.walk(self.target_dir):
                for f in files:
                    file_path = Path(root) / f
                    if not _should_skip_item(file_path):
                        files_to_process.append(file_path)
        else:
            for item in self.target_dir.iterdir():
                if item.is_file() and not _should_skip_item(item):
                    files_to_process.append(item)

        for file_path in files_to_process:
            category = get_category_for_extension(file_path.suffix, custom_rules)
            
            # Détermination du sous-dossier de destination selon le mode
            if mode == "date":
                subfolder = get_date_subfolder(file_path)
                dest_dir = self.target_dir / subfolder
            elif mode == "size":
                subfolder = get_size_subfolder(file_path)
                dest_dir = self.target_dir / subfolder
            else:  # mode == "type" par défaut
                dest_dir = self.target_dir / category

            dest_file_path = dest_dir / file_path.name

            # Ne pas re-déplacer si le fichier est déjà exactement au bon endroit
            if file_path.parent == dest_dir:
                continue

            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
            except Exception:
                size_bytes = 0
                mtime_str = "Inconnu"

            proposed_actions.append({
                "source": str(file_path),
                "destination": str(dest_file_path),
                "file_name": file_path.name,
                "category": category,
                "size_bytes": size_bytes,
                "size_formatted": format_size(size_bytes),
                "mtime": mtime_str
            })

        return proposed_actions

    def execute(self, actions: list) -> dict:
        """
        Exécute la liste d'actions de déplacement en toute sécurité (anti-écrasement).
        """
        if not actions:
            return {"success": True, "count": 0, "batch_id": None, "message": "Aucune action à effectuer."}

        executed_moves = []
        for action in actions:
            src = Path(action["source"])
            dst = Path(action["destination"])

            if not src.exists():
                continue

            # Créer le dossier parent si nécessaire
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Gestion anti-écrasement des doublons
            final_dst = dst
            counter = 1
            while final_dst.exists():
                final_dst = dst.parent / f"{dst.stem} ({counter}){dst.suffix}"
                counter += 1

            try:
                shutil.move(str(src), str(final_dst))
                executed_moves.append({
                    "source": str(src),
                    "destination": str(final_dst),
                    "file_name": src.name
                })
            except Exception as e:
                print(f"Erreur lors du déplacement de {src} vers {final_dst}: {e}")

        # Enregistrer l'historique pour l'annulation (Undo)
        batch_id = self.history_manager.record_batch(executed_moves)

        return {
            "success": True,
            "count": len(executed_moves),
            "batch_id": batch_id,
            "message": f"{len(executed_moves)} fichier(s) organisé(s) avec succès !"
        }

    def get_stats(self) -> dict:
        """
        Calcule les statistiques actuelles du dossier (répartition par catégorie, taille totale).
        """
        if not self.is_valid_directory():
            return {"total_files": 0, "total_size_formatted": "0 B", "categories": {}}

        total_files = 0
        total_size = 0
        categories_count = {}
        categories_size = {}

        for item in self.target_dir.iterdir():
            if item.name in IGNORED_FILES or item.name.startswith("."):
                continue

            if item.is_file():
                cat = get_category_for_extension(item.suffix)
                try:
                    sz = item.stat().st_size
                except Exception:
                    sz = 0

                total_files += 1
                total_size += sz
                categories_count[cat] = categories_count.get(cat, 0) + 1
                categories_size[cat] = categories_size.get(cat, 0) + sz

            elif item.is_dir():
                # Si c'est un sous-dossier de catégorie
                cat_name = item.name
                dir_files = 0
                dir_size = 0
                for root, _, files in os.walk(item):
                    for f in files:
                        try:
                            fp = Path(root) / f
                            if not fp.name.startswith("."):
                                dir_files += 1
                                dir_size += fp.stat().st_size
                        except Exception:
                            pass
                if dir_files > 0:
                    total_files += dir_files
                    total_size += dir_size
                    categories_count[cat_name] = categories_count.get(cat_name, 0) + dir_files
                    categories_size[cat_name] = categories_size.get(cat_name, 0) + dir_size

        categories_summary = []
        for cat, cnt in categories_count.items():
            categories_summary.append({
                "category": cat,
                "count": cnt,
                "size_bytes": categories_size.get(cat, 0),
                "size_formatted": format_size(categories_size.get(cat, 0))
            })

        return {
            "target_dir": str(self.target_dir),
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_formatted": format_size(total_size),
            "categories": categories_summary
        }
