import argparse
import sys
import os
import time
from pathlib import Path

# Assurer la compatibilité UTF-8 pour les prints sous Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from core.organizer import FileOrganizer
from core.history import HistoryManager
from core.watcher import FolderWatcher
from core.config import global_config
from core.ai_organizer import DeepSeekEngine
from core.autostart import autostart_mgr

def resolve_target_dir(dir_arg: str) -> Path:
    if not dir_arg or dir_arg.upper() == "DOWNLOADS":
        return Path.home() / "Downloads"
    elif dir_arg.upper() == "DESKTOP":
        return Path.home() / "Desktop"
    elif dir_arg.upper() == "DOCUMENTS":
        return Path.home() / "Documents"
    return Path(os.path.expanduser(dir_arg)).resolve()

def handle_config_command(args):
    print("⚙️  Configuration Smart File Organizer")
    changed = False
    if getattr(args, "provider", None):
        global_config.set("ai_provider", args.provider)
        print(f"🤖 Fournisseur IA sélectionné : {args.provider.upper()}")
        changed = True

    if getattr(args, "key", None) is not None:
        provider = global_config.get("ai_provider", "deepseek")
        key_name = "openai_api_key" if provider == "openai" else "deepseek_api_key"
        global_config.set(key_name, args.key)
        print(f"🔑 Clé API {provider.upper()} enregistrée: {global_config.get_masked_api_key(key_name)}")
        changed = True
        
        # Test de connexion immédiat si clé fournie
        engine = DeepSeekEngine(provider=provider, api_key=args.key)
        ok, msg = engine.test_connection()
        print(f"{'✅' if ok else '❌'} {msg}")

    if getattr(args, "model", None):
        global_config.set("deepseek_model", args.model)
        print(f"🤖 Modèle IA défini : {args.model}")
        changed = True

    if getattr(args, "prompt", None):
        global_config.set("deepseek_custom_prompt", args.prompt)
        print(f"📝 Prompt système IA mis à jour : {args.prompt}")
        changed = True

    if not changed:
        provider = global_config.get("ai_provider", "deepseek")
        print(f" • Fournisseur IA : {provider.upper()}")
        if provider == "ollama":
            print(f" • Serveur Local : {global_config.get('ollama_endpoint')} (100% Offline)")
            print(f" • Modèle Ollama  : {global_config.get('ollama_model')}")
        else:
            print(f" • Clé API ({provider.upper()}) : {global_config.get_masked_api_key('openai_api_key' if provider == 'openai' else 'deepseek_api_key') or '(Non configurée)'}")
            print(f" • Modèle IA actif : {global_config.get('deepseek_model')}")
        print(f" • Content-Aware  : {'Activé' if global_config.get('content_aware_parsing', True) else 'Désactivé'}")
        print(f" • Prompt système : {global_config.get('deepseek_custom_prompt')}")
        print(f" • Dossier par défaut: {global_config.get('default_target_dir')}")

def handle_service_command(args):
    action = args.action.lower() if args.action else "status"
    print("🤖 Gestion du service Daemon au démarrage du système (OS Boot)")

    if action == "install" or action == "enable":
        ok, msg = autostart_mgr.enable()
        print(f"{'✅' if ok else '❌'} {msg}")
    elif action == "uninstall" or action == "disable":
        ok, msg = autostart_mgr.disable()
        print(f"{'✅' if ok else '❌'} {msg}")
    else:
        active, desc = autostart_mgr.get_status()
        print(f"Status Service : {'🟢 ACTIF' if active else '🔴 INACTIF'}")
        print(f"Détails : {desc}")

def handle_history_command(args, target_dir: Path):
    history_mgr = HistoryManager(str(target_dir))
    if args.last_24h:
        digest = history_mgr.get_24h_digest()
        print(f"\n📊 Rapport d'activité des Dernières 24 Heures ({digest['period']})")
        print(f" • Fichiers déplacés : {digest['total_files_moved']}")
        print(f" • Volume réorganisé : {digest['total_size_formatted']}")
        print(" • Catégories :")
        for cat, cnt in digest['categories'].items():
            print(f"    - {cat} : {cnt} fichier(s)")
        print("\n 📜 Fichiers déplacés récemment :")
        for m in digest['recent_moves'][:20]:
            print(f"    [{m['timestamp']}] {m['file_name']} -> {m['category']}")
        if len(digest['recent_moves']) > 20:
            print(f"    ... et {len(digest['recent_moves']) - 20} autre(s) mouvement(s).")
    else:
        hist = history_mgr.get_history()
        print(f"\n📜 Historique complet des lots ({len(hist)} lot(s) enregistré(s)) :")
        for b in hist[:10]:
            print(f" • Lot #{b['batch_id']} [{b['timestamp']}] - {b['count']} fichier(s)")

def run_daemon(target_dir: Path, mode: str):
    print(f"🛡️  Démarrage du Daemon Smart File Organizer sur {target_dir}...")
    print(f" • Mode actif : {mode.upper()}")
    print(" • Surveillance continue en arrière-plan activée.")
    print(" (Appuyez sur Ctrl+C pour quitter le daemon)")
    
    watcher = FolderWatcher(str(target_dir), mode=mode)
    watcher.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        watcher.stop()
        print("\n👋 Daemon arrêté.")

def main():
    parser = argparse.ArgumentParser(
        description="Smart File Organizer CLI - Tri chirurgical Open-Source, IA DeepSeek & Service d'arrière-plan"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Command: scan / organize
    scan_parser = subparsers.add_parser("scan", help="Scanner et afficher les propositions de tri (Dry-Run)")
    scan_parser.add_argument("-d", "--dir", type=str, default="DOWNLOADS", help="Dossier à scanner")
    scan_parser.add_argument("-m", "--mode", choices=["type", "date", "size", "ai"], default="type", help="Mode de tri")
    scan_parser.add_argument("--ai", action="store_true", help="Utiliser l'IA DeepSeek pour la classification sémantique")
    scan_parser.add_argument("--regex", type=str, help="Filtre chirurgical par nom de fichier (Regex)")
    scan_parser.add_argument("--min-size", type=float, help="Taille minimale en Mo")
    scan_parser.add_argument("--max-size", type=float, help="Taille maximale en Mo")
    scan_parser.add_argument("--days", type=int, help="Fichiers modifiés dans les X derniers jours")

    organize_parser = subparsers.add_parser("organize", help="Scanner et exécuter le tri de fichiers")
    organize_parser.add_argument("-d", "--dir", type=str, default="DOWNLOADS", help="Dossier à trier")
    organize_parser.add_argument("-m", "--mode", choices=["type", "date", "size", "ai"], default="type", help="Mode de tri")
    organize_parser.add_argument("--ai", action="store_true", help="Utiliser l'IA DeepSeek")
    organize_parser.add_argument("-y", "--yes", action="store_true", help="Exécuter sans confirmation")

    # Command: daemon
    daemon_parser = subparsers.add_parser("daemon", help="Lancer la surveillance continue en arrière-plan")
    daemon_parser.add_argument("-d", "--dir", type=str, default="DOWNLOADS", help="Dossier à surveiller")
    daemon_parser.add_argument("-m", "--mode", choices=["type", "date", "size", "ai"], default="type", help="Mode de tri")

    # Command: service
    service_parser = subparsers.add_parser("service", help="Gérer le démarrage automatique au boot du système OS")
    service_parser.add_argument("action", choices=["install", "uninstall", "status"], help="Action à exécuter")

    # Command: config
    config_parser = subparsers.add_parser("config", help="Configurer le fournisseur IA et les options")
    config_parser.add_argument("--provider", choices=["deepseek", "ollama", "openai", "custom"], help="Fournisseur IA (deepseek, ollama, openai, custom)")
    config_parser.add_argument("--key", type=str, help="Définir la clé API")
    config_parser.add_argument("--model", type=str, help="Définir le modèle IA (ex: deepseek-chat, gpt-4o-mini, llama3:latest)")
    config_parser.add_argument("--prompt", type=str, help="Définir le prompt système personnalisé pour l'IA")

    # Command: history
    history_parser = subparsers.add_parser("history", help="Consulter l'historique et les rapports 24h")
    history_parser.add_argument("-d", "--dir", type=str, default="DOWNLOADS", help="Dossier cible")
    history_parser.add_argument("--last-24h", action="store_true", help="Afficher le rapport digest des 24 dernières heures")

    # Command: undo
    undo_parser = subparsers.add_parser("undo", help="Annuler un lot de déplacements")
    undo_parser.add_argument("-d", "--dir", type=str, default="DOWNLOADS", help="Dossier cible")
    undo_parser.add_argument("--batch", type=str, help="ID spécifique du lot à annuler")

    # Arguments globaux pour rétrocompatibilité
    parser.add_argument("-d", "--dir", type=str, default=None, help="Dossier cible (mode direct)")
    parser.add_argument("-m", "--mode", choices=["type", "date", "size", "ai"], default="type", help="Mode (mode direct)")
    parser.add_argument("--dry-run", action="store_true", help="Mode aperçu sans déplacer (mode direct)")
    parser.add_argument("--undo", action="store_true", help="Annuler le dernier lot (mode direct)")
    parser.add_argument("-w", "--watch", action="store_true", help="Lancer le watcher (mode direct)")

    args = parser.parse_args()

    # Traitement des sous-commandes
    if args.command == "config":
        handle_config_command(args)
        return
    elif args.command == "service":
        handle_service_command(args)
        return
    elif args.command == "daemon":
        target_dir = resolve_target_dir(args.dir)
        mode = "ai" if getattr(args, "ai", False) else args.mode
        run_daemon(target_dir, mode)
        return
    elif args.command == "history":
        target_dir = resolve_target_dir(args.dir)
        handle_history_command(args, target_dir)
        return
    elif args.command == "undo":
        target_dir = resolve_target_dir(args.dir)
        history_mgr = HistoryManager(str(target_dir))
        success, msg, count = history_mgr.undo_batch(args.batch)
        print(f"{'✅' if success else '⚠️'} {msg}")
        return

    # Gestion de la sous-commande scan ou organize
    if args.command in ["scan", "organize"] or args.dir is not None or args.undo or args.watch:
        dir_val = getattr(args, "dir", None) or "DOWNLOADS"
        target_dir = resolve_target_dir(dir_val)

        if not target_dir.exists():
            print(f"❌ Erreur: Le dossier '{target_dir}' n'existe pas.")
            sys.exit(1)

        if getattr(args, "undo", False):
            history_mgr = HistoryManager(str(target_dir))
            success, msg, count = history_mgr.undo_last_batch()
            print(f"{'✅' if success else '⚠️'} {msg}")
            return

        if getattr(args, "watch", False):
            mode = "ai" if getattr(args, "ai", False) else args.mode
            run_daemon(target_dir, mode)
            return

        mode = getattr(args, "mode", "type")
        if getattr(args, "ai", False):
            mode = "ai"

        surgical_filters = {
            "regex": getattr(args, "regex", "") or "",
            "min_size_mb": getattr(args, "min_size", 0) or 0,
            "max_size_mb": getattr(args, "max_size", 0) or 0,
            "date_days": getattr(args, "days", 0) or 0
        }

        print(f"📁 Dossier cible : {target_dir}")
        print(f"🎯 Mode de tri  : {mode.upper()}")
        if mode == "ai":
            print(f"🔑 Clé DeepSeek : {global_config.get_masked_api_key() or 'ATTENTION: Non configurée !'}")

        organizer = FileOrganizer(str(target_dir))
        actions = organizer.scan(mode=mode, surgical_filters=surgical_filters)

        if not actions:
            print("✨ Aucun fichier ne nécessite de déplacement.")
            return

        print(f"\n📊 {len(actions)} action(s) de tri détectée(s) :")
        for act in actions[:15]:
            explanation_str = f" [{act['explanation']}]" if act.get('explanation') else ""
            print(f"  • {act['file_name']} -> {act['category']}/{act.get('dest_file_name', act['file_name'])} ({act['size_formatted']}){explanation_str}")
        if len(actions) > 15:
            print(f"  ... et {len(actions) - 15} autre(s) action(s).")

        is_dry_run = (args.command == "scan") or getattr(args, "dry_run", False)

        if is_dry_run:
            print("\n🔍 Mode Aperçu (Dry-Run). Aucun fichier n'a été modifié.")
        else:
            if not getattr(args, "yes", False):
                ans = input("\n🚀 Voulez-vous exécuter cette réorganisation ? (y/N) : ")
                if ans.lower() not in ["y", "oui", "o"]:
                    print("Annulé par l'utilisateur.")
                    return

            print("\n⚡ Execution du tri chirurgical en cours...")
            res = organizer.execute(actions)
            print(f"🎉 {res['message']} (ID Lot: {res['batch_id']})")
            print("💡 Annulable à tout moment via: python organizer_cli.py undo")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
