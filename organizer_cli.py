import argparse
import sys
import os
from pathlib import Path

# Assurer la compatibilité UTF-8 pour les prints d'emojis sous Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from core.organizer import FileOrganizer
from core.history import HistoryManager
from core.watcher import FolderWatcher

def main():
    parser = argparse.ArgumentParser(description="Smart File Organizer - Outil d'automatisation et tri de fichiers")
    parser.add_argument("-d", "--dir", type=str, default="~/Downloads", help="Chemin du dossier à trier (par défaut: Downloads)")
    parser.add_argument("-m", "--mode", choices=["type", "date", "size"], default="type", help="Mode de tri (type, date, size)")
    parser.add_argument("--dry-run", action="store_true", help="Afficher un aperçu sans déplacer les fichiers")
    parser.add_argument("--undo", action="store_true", help="Annuler le dernier lot de tri")
    parser.add_argument("-w", "--watch", action="store_true", help="Lancer en mode surveillance temps réel")

    args = parser.parse_args()

    target_dir = Path(os.path.expanduser(args.dir)).resolve()

    if not target_dir.exists():
        print(f"❌ Erreur: Le dossier {target_dir} n'existe pas.")
        sys.exit(1)

    print(f"📁 Dossier cible : {target_dir}")

    # Mode Annulation (Undo)
    if args.undo:
        history_mgr = HistoryManager(str(target_dir))
        success, msg, count = history_mgr.undo_last_batch()
        print(f"{'✅' if success else '⚠️'} {msg}")
        return

    # Mode Surveillance (Watch)
    if args.watch:
        print(f"👀 Démarrage de la surveillance temps réel sur {target_dir}...")
        watcher = FolderWatcher(str(target_dir), mode=args.mode)
        watcher.start()
        print("Appuyez sur Ctrl+C pour arrêter.")
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            print("\n👋 Surveillance arrêtée.")
            return

    # Mode Scan / Tri
    organizer = FileOrganizer(str(target_dir))
    actions = organizer.scan(mode=args.mode)

    if not actions:
        print("✨ Le dossier est déjà parfaitement propre et trié !")
        return

    print(f"\n📊 {len(actions)} action(s) détectée(s) :")
    for act in actions[:15]:
        print(f"  • {act['file_name']} -> [{act['category']}] ({act['size_formatted']})")
    if len(actions) > 15:
        print(f"  ... et {len(actions) - 15} autre(s) fichier(s).")

    if args.dry_run:
        print("\n🔍 Mode Aperçu (Dry-Run). Aucun fichier n'a été déplacé.")
    else:
        print("\n🚀 Exécution du tri...")
        res = organizer.execute(actions)
        print(f"🎉 {res['message']} (ID Lot: {res['batch_id']})")
        print("💡 Vous pouvez annuler ce tri à tout moment avec la commande: python organizer_cli.py --undo")

if __name__ == "__main__":
    main()
