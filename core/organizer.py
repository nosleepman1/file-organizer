import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from core.rules import (
    get_category_for_extension, 
    get_date_subfolder, 
    get_size_subfolder, 
    DEFAULT_CATEGORIES, 
    IGNORED_FILES,
    is_temp_or_ignored,
    load_custom_rules
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

def calculate_sha256(file_path: Path) -> str:
    """Calcule le hash SHA256 d'un fichier."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""

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
        rules = custom_rules if custom_rules is not None else load_custom_rules(str(self.target_dir))
        known_categories = list(rules.keys()) + ["Autres", "Divers"]

        def _should_skip_item(item_path: Path) -> bool:
            if is_temp_or_ignored(item_path):
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
            category = get_category_for_extension(file_path.suffix, rules)
            
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

    def scan_duplicates(self, recursive: bool = False) -> list:
        """
        Recherche les doublons exacts par hash SHA256.
        Returns: liste de groupes de doublons
        """
        if not self.is_valid_directory():
            return []

        size_map = {}
        files_to_check = []

        if recursive:
            for root, _, files in os.walk(self.target_dir):
                for f in files:
                    fp = Path(root) / f
                    if not is_temp_or_ignored(fp):
                        files_to_check.append(fp)
        else:
            for item in self.target_dir.iterdir():
                if item.is_file() and not is_temp_or_ignored(item):
                    files_to_check.append(item)

        for fp in files_to_check:
            try:
                sz = fp.stat().st_size
                if sz > 0:
                    size_map.setdefault(sz, []).append(fp)
            except Exception:
                pass

        hash_map = {}
        for sz, path_list in size_map.items():
            if len(path_list) > 1:
                for fp in path_list:
                    h = calculate_sha256(fp)
                    if h:
                        hash_map.setdefault(h, []).append(fp)

        duplicate_groups = []
        for h, fp_list in hash_map.items():
            if len(fp_list) > 1:
                group_files = []
                total_size = 0
                for fp in fp_list:
                    try:
                        stat = fp.stat()
                        sz = stat.st_size
                        total_size = sz
                        mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        sz = 0
                        mtime_str = "Inconnu"
                    group_files.append({
                        "path": str(fp),
                        "file_name": fp.name,
                        "size_bytes": sz,
                        "size_formatted": format_size(sz),
                        "mtime": mtime_str
                    })

                duplicate_groups.append({
                    "hash": h[:12],
                    "count": len(fp_list),
                    "size_formatted": format_size(total_size),
                    "wasted_bytes": total_size * (len(fp_list) - 1),
                    "wasted_formatted": format_size(total_size * (len(fp_list) - 1)),
                    "files": group_files
                })

        return duplicate_groups

    def delete_duplicates(self, file_paths: list) -> dict:
        """Supprime en toute sécurité les fichiers doublons spécifiés."""
        deleted_count = 0
        freed_bytes = 0

        for path_str in file_paths:
            fp = Path(path_str)
            if fp.exists() and fp.is_file() and self.target_dir in fp.parents:
                try:
                    sz = fp.stat().st_size
                    fp.unlink()
                    deleted_count += 1
                    freed_bytes += sz
                except Exception as e:
                    print(f"Erreur lors de la suppression de {path_str}: {e}")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "freed_formatted": format_size(freed_bytes),
            "message": f"{deleted_count} fichier(s) doublon(s) supprimé(s) ({format_size(freed_bytes)} libérés)."
        }

    def bulk_rename(self, replace_spaces: str = "_", lowercase: bool = False, add_date_prefix: bool = False, recursive: bool = False) -> dict:
        """
        Renomme les fichiers selon les règles choisies.
        """
        if not self.is_valid_directory():
            return {"success": False, "message": "Dossier cible invalide."}

        renamed_count = 0
        files_to_rename = []

        if recursive:
            for root, _, files in os.walk(self.target_dir):
                for f in files:
                    fp = Path(root) / f
                    if not is_temp_or_ignored(fp):
                        files_to_rename.append(fp)
        else:
            for item in self.target_dir.iterdir():
                if item.is_file() and not is_temp_or_ignored(item):
                    files_to_rename.append(item)

        for fp in files_to_rename:
            stem = fp.stem
            suffix = fp.suffix

            new_stem = stem
            if replace_spaces:
                new_stem = new_stem.replace(" ", replace_spaces)
            if lowercase:
                new_stem = new_stem.lower()
                suffix = suffix.lower()

            if add_date_prefix:
                try:
                    mtime = fp.stat().st_mtime
                    dt_prefix = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                    if not new_stem.startswith(dt_prefix):
                        new_stem = f"{dt_prefix}_{new_stem}"
                except Exception:
                    pass

            new_file_name = f"{new_stem}{suffix}"
            if new_file_name != fp.name:
                new_path = fp.parent / new_file_name
                counter = 1
                while new_path.exists() and new_path != fp:
                    new_path = fp.parent / f"{new_stem}_{counter}{suffix}"
                    counter += 1

                try:
                    fp.rename(new_path)
                    renamed_count += 1
                except Exception as e:
                    print(f"Erreur renommage {fp} -> {new_path}: {e}")

        return {
            "success": True,
            "renamed_count": renamed_count,
            "message": f"{renamed_count} fichier(s) renommé(s) avec succès."
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

        rules = load_custom_rules(str(self.target_dir))

        for item in self.target_dir.iterdir():
            if is_temp_or_ignored(item):
                continue

            if item.is_file():
                cat = get_category_for_extension(item.suffix, rules)
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
                            if not is_temp_or_ignored(fp):
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

