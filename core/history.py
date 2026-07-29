import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

HISTORY_FILE_NAME = ".sort_history.json"

class HistoryManager:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir)
        self.history_file = self.target_dir / HISTORY_FILE_NAME

    def _load_history(self) -> list:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_history(self, history_data: list):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {e}")

    def record_batch(self, moves: list) -> str:
        """
        Enregistre un lot de déplacements.
        moves: list de dict {"source": str, "destination": str, "file_name": str}
        Returns: batch_id
        """
        if not moves:
            return None
            
        history = self._load_history()
        batch_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        batch_record = {
            "batch_id": batch_id,
            "timestamp": timestamp,
            "count": len(moves),
            "moves": moves
        }

        history.insert(0, batch_record)  # Dernier lot en premier
        self._save_history(history)
        return batch_id

    def undo_batch(self, batch_id: str = None) -> tuple[bool, str, int]:
        """
        Annule un lot spécifique par son ID (ou le dernier si batch_id est None).
        Returns: (success, message, restored_count)
        """
        history = self._load_history()
        if not history:
            return False, "Aucun historique disponible pour annulation.", 0

        target_index = -1
        if batch_id:
            for idx, batch in enumerate(history):
                if batch.get("batch_id") == batch_id:
                    target_index = idx
                    break
            if target_index == -1:
                return False, f"Lot #{batch_id} introuvable dans l'historique.", 0
        else:
            target_index = 0

        target_batch = history.pop(target_index)
        moves = target_batch.get("moves", [])
        restored_count = 0

        for move in reversed(moves):
            src = Path(move["source"])
            dst = Path(move["destination"])

            if dst.exists():
                # S'assurer que le dossier source parent existe
                src.parent.mkdir(parents=True, exist_ok=True)

                # Gestion anti-écrasement lors du retour
                target_src = src
                counter = 1
                while target_src.exists():
                    target_src = src.parent / f"{src.stem}_restored_{counter}{src.suffix}"
                    counter += 1

                try:
                    shutil.move(str(dst), str(target_src))
                    restored_count += 1
                except Exception as e:
                    print(f"Erreur annulation pour {dst} -> {target_src}: {e}")

        # Nettoyage des dossiers vides éventuellement créés dans la destination
        self._clean_empty_dirs()

        self._save_history(history)
        return True, f"Lot #{target_batch['batch_id']} annulé ({restored_count}/{len(moves)} fichiers restaurés).", restored_count

    def undo_last_batch(self) -> tuple[bool, str, int]:
        """Annule le tout dernier lot de déplacements."""
        return self.undo_batch(None)

    def get_history(self) -> list:
        """Retourne la liste des lots d'historique enregistrés."""
        return self._load_history()

    def _clean_empty_dirs(self):
        """Supprime récursivement les sous-dossiers vides dans le dossier cible (sauf dossiers cachés)."""
        try:
            for root, dirs, files in os.walk(self.target_dir, topdown=False):
                for d in dirs:
                    dir_path = Path(root) / d
                    if dir_path.name.startswith("."):
                        continue
                    if dir_path.exists() and not any(dir_path.iterdir()):
                        try:
                            dir_path.rmdir()
                        except Exception:
                            pass
        except Exception:
            pass
