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
from core.hash_cache import global_hash_cache
from concurrent.futures import ThreadPoolExecutor

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
    """Calcule le hash SHA256 d'un fichier avec cache disque intelligent."""
    return global_hash_cache.get_hash(file_path)

def safe_delete_file(file_path: Path) -> tuple:
    """
    Déplace un fichier vers la Corbeille de l'OS via send2trash.
    Fallback vers un dossier sécurisé .organizer_trash/ si send2trash est indisponible.
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    if not file_path.exists():
        return False, "Le fichier n'existe pas."

    try:
        import send2trash
        send2trash.send2trash(str(file_path))
        return True, "Fichier envoyé vers la Corbeille de l'OS avec succès."
    except Exception:
        try:
            trash_dir = file_path.parent / ".organizer_trash"
            trash_dir.mkdir(parents=True, exist_ok=True)
            dest = trash_dir / file_path.name
            if dest.exists():
                stem = file_path.stem
                ext = file_path.suffix
                dest = trash_dir / f"{stem}_{int(datetime.now().timestamp())}{ext}"
            shutil.move(str(file_path), str(dest))
            return True, f"Fichier déplacé en sécurité dans le dossier corbeille local ({trash_dir.name})."
        except Exception as ex:
            return False, f"Erreur lors de la mise en corbeille sécurisée : {ex}"

class FileOrganizer:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.history_manager = HistoryManager(str(self.target_dir))

    def is_valid_directory(self) -> bool:
        return self.target_dir.exists() and self.target_dir.is_dir()

    def scan(
        self, 
        mode: str = "type", 
        custom_rules: dict = None, 
        recursive: bool = False,
        surgical_filters: dict = None,
        ai_custom_prompt: str = ""
    ) -> list:
        """
        Scanne le dossier et renvoie une liste d'actions proposées (Dry-Run / Aperçu).
        mode: 'type', 'date', 'size', ou 'ai' (DeepSeek IA)
        surgical_filters: {"regex": str, "min_size_mb": float, "max_size_mb": float, "date_days": int}
        """
        if not self.is_valid_directory():
            return []

        import re
        from datetime import datetime, timedelta

        proposed_actions = []
        rules = custom_rules if custom_rules is not None else load_custom_rules(str(self.target_dir))
        known_categories = list(rules.keys()) + ["Autres", "Divers"]
        s_filters = surgical_filters or {}

        # Extraction des filtres chirurgicaux
        regex_pat = s_filters.get("regex", "").strip()
        regex_compiled = None
        if regex_pat:
            try:
                regex_compiled = re.compile(regex_pat, re.IGNORECASE)
            except Exception:
                regex_compiled = None

        min_size_bytes = (s_filters.get("min_size_mb") or 0) * 1024 * 1024
        max_size_bytes = (s_filters.get("max_size_mb") or 0) * 1024 * 1024
        date_days = s_filters.get("date_days") or 0
        cutoff_date = datetime.now() - timedelta(days=date_days) if date_days > 0 else None

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

        # Application des filtres chirurgicaux
        filtered_files = []
        for file_path in files_to_process:
            try:
                stat = file_path.stat()
                sz = stat.st_size
                mtime_dt = datetime.fromtimestamp(stat.st_mtime)
            except Exception:
                sz = 0
                mtime_dt = datetime.now()

            # Filtre Regex
            if regex_compiled and not regex_compiled.search(file_path.name):
                continue

            # Filtre Taille
            if min_size_bytes > 0 and sz < min_size_bytes:
                continue
            if max_size_bytes > 0 and sz > max_size_bytes:
                continue

            # Filtre Date
            if cutoff_date and mtime_dt < cutoff_date:
                continue

            filtered_files.append((file_path, sz, mtime_dt))

        # Mode IA DeepSeek & Multi-Fournisseurs
        ai_recommendations = {}
        if mode == "ai":
            from core.ai_organizer import DeepSeekEngine, extract_file_snippet
            from core.config import global_config
            ai_engine = DeepSeekEngine()
            if ai_engine.is_configured():
                batch_for_ai = []
                for fp, sz, mtime_dt in filtered_files:
                    f_info = {
                        "name": fp.name,
                        "extension": fp.suffix.lstrip("."),
                        "size_formatted": format_size(sz),
                        "mtime": mtime_dt.strftime("%d/%m/%Y")
                    }
                    if global_config.get("content_aware_parsing", True):
                        snip = extract_file_snippet(fp)
                        if snip:
                            f_info["content_snippet"] = snip
                    batch_for_ai.append(f_info)
                
                success, items, msg = ai_engine.categorize_files(batch_for_ai, custom_prompt=ai_custom_prompt)
                if success:
                    for item in items:
                        fn = item.get("file_name")
                        if fn:
                            ai_recommendations[fn] = item

        for file_path, size_bytes, mtime_dt in filtered_files:
            mtime_str = mtime_dt.strftime("%d/%m/%Y %H:%M")
            explanation = ""
            dest_file_name = file_path.name

            if mode == "ai" and file_path.name in ai_recommendations:
                rec = ai_recommendations[file_path.name]
                category = rec.get("category", "Divers")
                if rec.get("suggested_name") and rec.get("suggested_name") != file_path.name:
                    dest_file_name = rec.get("suggested_name")
                explanation = rec.get("explanation", "Suggéré par l'IA DeepSeek")
                dest_dir = self.target_dir / category
            elif mode == "date":
                subfolder = get_date_subfolder(file_path)
                category = f"Date ({subfolder})"
                dest_dir = self.target_dir / subfolder
            elif mode == "size":
                subfolder = get_size_subfolder(file_path)
                category = f"Taille ({subfolder})"
                dest_dir = self.target_dir / subfolder
            else:  # mode == "type" par défaut
                category = get_category_for_extension(file_path.suffix, rules)
                dest_dir = self.target_dir / category

            dest_file_path = dest_dir / dest_file_name

            # Ne pas re-déplacer si le fichier est déjà exactement au bon endroit avec le même nom
            if file_path.parent == dest_dir and file_path.name == dest_file_name:
                continue

            # Détection de collision
            has_collision = dest_file_path.exists() and dest_file_path != file_path
            conflict_action = "auto_rename" if has_collision else "none"

            proposed_actions.append({
                "source": str(file_path),
                "destination": str(dest_file_path),
                "file_name": file_path.name,
                "dest_file_name": dest_file_name,
                "category": category,
                "size_bytes": size_bytes,
                "size_formatted": format_size(size_bytes),
                "mtime": mtime_str,
                "explanation": explanation,
                "has_collision": has_collision,
                "conflict_action": conflict_action
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
                with ThreadPoolExecutor(max_workers=min(16, len(path_list))) as executor:
                    future_to_fp = {executor.submit(calculate_sha256, fp): fp for fp in path_list}
                    for future in future_to_fp:
                        fp = future_to_fp[future]
                        try:
                            h = future.result()
                            if h:
                                hash_map.setdefault(h, []).append(fp)
                        except Exception:
                            pass

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
        """Déplace en toute sécurité les fichiers doublons spécifiés vers la Corbeille."""
        deleted_count = 0
        freed_bytes = 0

        for path_str in file_paths:
            fp = Path(path_str)
            if fp.exists() and fp.is_file() and (self.target_dir in fp.parents or fp.parent == self.target_dir):
                try:
                    sz = fp.stat().st_size
                    ok, msg = safe_delete_file(fp)
                    if ok:
                        deleted_count += 1
                        freed_bytes += sz
                    else:
                        print(f"Échec de la corbeille sécurisée pour {path_str}: {msg}")
                except Exception as e:
                    print(f"Erreur lors de la mise en corbeille de {path_str}: {e}")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "freed_formatted": format_size(freed_bytes),
            "message": f"{deleted_count} fichier(s) doublon(s) placé(s) en Corbeille ({format_size(freed_bytes)} libérés)."
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
