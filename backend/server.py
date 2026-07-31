import os
import sys
from pathlib import Path

# Assurer la résolution des modules backend/core
BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).parent.resolve()))

# Assurer la compatibilité UTF-8 pour les logs sous Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from flask import Flask, request, jsonify, send_from_directory
from core.organizer import FileOrganizer
from core.history import HistoryManager
from core.watcher import FolderWatcher
from core.rules import load_custom_rules, save_custom_rules
from core.config import global_config
from core.ai_organizer import DeepSeekEngine
from core.autostart import autostart_mgr

USER_HOME = Path.home()
PRESET_PATHS = {
    "DOWNLOADS": USER_HOME / "Downloads",
    "DESKTOP": USER_HOME / "Desktop",
    "DOCUMENTS": USER_HOME / "Documents"
}

def resolve_target_path(path_str: str) -> str:
    if not path_str:
        return str(PRESET_PATHS["DOWNLOADS"])
    
    upper_path = path_str.strip().upper()
    if upper_path in PRESET_PATHS:
        return str(PRESET_PATHS[upper_path])
    
    return os.path.abspath(os.path.expanduser(path_str))

# Flask app pointant sur le dossier web à la racine
WEB_FOLDER = BASE_DIR / "web"
app = Flask(__name__, static_folder=str(WEB_FOLDER))

active_watcher = None

@app.route("/")
def index():
    return send_from_directory(str(WEB_FOLDER), "index.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(str(WEB_FOLDER / "assets"), filename)

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "healthy",
        "app": "Smart File Organizer Pro",
        "version": "2.0.0-OpenSource"
    })

# --------------------------------------------------------------------------
# Endpoints Multi-Fournisseurs IA (DeepSeek, Ollama offline, OpenAI, Custom)
# --------------------------------------------------------------------------
@app.route("/api/ai/config", methods=["GET", "POST"])
def api_ai_config():
    if request.method == "POST":
        data = request.json or {}
        if "ai_provider" in data:
            global_config.set("ai_provider", data["ai_provider"])
        if "deepseek_api_key" in data and data["deepseek_api_key"]:
            global_config.set("deepseek_api_key", data["deepseek_api_key"])
        if "deepseek_model" in data:
            global_config.set("deepseek_model", data["deepseek_model"])
        if "openai_api_key" in data and data["openai_api_key"]:
            global_config.set("openai_api_key", data["openai_api_key"])
        if "openai_model" in data:
            global_config.set("openai_model", data["openai_model"])
        if "ollama_endpoint" in data:
            global_config.set("ollama_endpoint", data["ollama_endpoint"])
        if "ollama_model" in data:
            global_config.set("ollama_model", data["ollama_model"])
        if "deepseek_custom_prompt" in data:
            global_config.set("deepseek_custom_prompt", data["deepseek_custom_prompt"])
        if "content_aware_parsing" in data:
            global_config.set("content_aware_parsing", bool(data["content_aware_parsing"]))

        return jsonify({
            "success": True,
            "message": "Configuration IA sauvegardée avec succès !",
            "ai_provider": global_config.get("ai_provider"),
            "masked_key": global_config.get_masked_api_key("deepseek_api_key"),
            "openai_masked_key": global_config.get_masked_api_key("openai_api_key"),
            "ollama_endpoint": global_config.get("ollama_endpoint"),
            "ollama_model": global_config.get("ollama_model"),
            "content_aware_parsing": global_config.get("content_aware_parsing"),
            "custom_prompt": global_config.get("deepseek_custom_prompt")
        })
    else:
        return jsonify({
            "success": True,
            "ai_provider": global_config.get("ai_provider", "deepseek"),
            "has_key": bool(global_config.get("deepseek_api_key")),
            "masked_key": global_config.get_masked_api_key("deepseek_api_key"),
            "deepseek_model": global_config.get("deepseek_model"),
            "openai_masked_key": global_config.get_masked_api_key("openai_api_key"),
            "openai_model": global_config.get("openai_model"),
            "ollama_endpoint": global_config.get("ollama_endpoint"),
            "ollama_model": global_config.get("ollama_model"),
            "content_aware_parsing": global_config.get("content_aware_parsing", True),
            "custom_prompt": global_config.get("deepseek_custom_prompt")
        })

@app.route("/api/ai/test", methods=["POST"])
def api_ai_test():
    data = request.json or {}
    provider = data.get("provider", global_config.get("ai_provider", "deepseek"))
    test_key = data.get("api_key")
    model = data.get("model")
    endpoint = data.get("endpoint")

    engine = DeepSeekEngine(provider=provider, api_key=test_key, model=model, endpoint=endpoint)
    success, message = engine.test_connection(test_key=test_key)

    return jsonify({"success": success, "message": message})

# --------------------------------------------------------------------------
# Endpoints Autostart Service (OS Boot)
# --------------------------------------------------------------------------
@app.route("/api/service/autostart", methods=["GET", "POST"])
def api_autostart_service():
    if request.method == "POST":
        data = request.json or {}
        enable = bool(data.get("enable", True))

        if enable:
            success, msg = autostart_mgr.enable()
        else:
            success, msg = autostart_mgr.disable()

        active, desc = autostart_mgr.get_status()
        return jsonify({"success": success, "enabled": active, "message": msg, "description": desc})
    else:
        active, desc = autostart_mgr.get_status()
        return jsonify({"enabled": active, "description": desc})

# --------------------------------------------------------------------------
# Endpoints Tri & Organisation
# --------------------------------------------------------------------------
@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    mode = data.get("mode", "type")
    recursive = bool(data.get("recursive", False))
    surgical_filters = data.get("surgical_filters", {})
    ai_custom_prompt = data.get("ai_custom_prompt", "")

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({"success": False, "message": f"Dossier invalide : {resolved_path}"}), 400

    actions = organizer.scan(
        mode=mode, 
        recursive=recursive, 
        surgical_filters=surgical_filters,
        ai_custom_prompt=ai_custom_prompt
    )

    return jsonify({
        "success": True,
        "target_dir": resolved_path,
        "mode": mode,
        "actions_count": len(actions),
        "actions": actions
    })

@app.route("/api/execute", methods=["POST"])
def api_execute():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    actions = data.get("actions", [])

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({"success": False, "message": f"Dossier invalide : {resolved_path}"}), 400

    res = organizer.execute(actions)
    return jsonify(res)

@app.route("/api/stats", methods=["GET"])
def api_stats():
    raw_path = request.args.get("target_dir", "DOWNLOADS")
    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)
    return jsonify(organizer.get_stats())

@app.route("/api/duplicates", methods=["GET"])
def api_duplicates():
    raw_path = request.args.get("target_dir", "DOWNLOADS")
    recursive = request.args.get("recursive", "false").lower() == "true"
    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({"success": False, "message": f"Dossier invalide : {resolved_path}"}), 400

    duplicate_groups = organizer.scan_duplicates(recursive=recursive)
    return jsonify({"success": True, "duplicate_groups": duplicate_groups})

@app.route("/api/duplicates/delete", methods=["POST"])
def api_delete_duplicates():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    file_paths = data.get("file_paths", [])

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({"success": False, "message": f"Dossier invalide : {resolved_path}"}), 400

    if not file_paths:
        return jsonify({"success": False, "message": "Aucun fichier spécifié pour la suppression."}), 400

    res = organizer.delete_duplicates(file_paths)
    return jsonify(res)

@app.route("/api/rename", methods=["POST"])
def api_rename():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    replace_spaces = data.get("replace_spaces", "_")
    lowercase = bool(data.get("lowercase", False))
    add_date_prefix = bool(data.get("add_date_prefix", False))
    recursive = bool(data.get("recursive", False))

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({"success": False, "message": f"Dossier invalide : {resolved_path}"}), 400

    res = organizer.bulk_rename(
        replace_spaces=replace_spaces, 
        lowercase=lowercase, 
        add_date_prefix=add_date_prefix, 
        recursive=recursive
    )
    return jsonify(res)

@app.route("/api/rules", methods=["GET", "POST"])
def api_rules():
    raw_path = request.args.get("target_dir", "DOWNLOADS") if request.method == "GET" else (request.json or {}).get("target_dir", "DOWNLOADS")
    resolved_path = resolve_target_path(raw_path)

    if request.method == "POST":
        data = request.json or {}
        rules = data.get("rules", {})
        saved = save_custom_rules(rules, resolved_path)
        return jsonify({"success": saved, "message": "Règles sauvegardées avec succès !" if saved else "Erreur de sauvegarde."})
    else:
        rules = load_custom_rules(resolved_path)
        return jsonify({"success": True, "rules": rules})

@app.route("/api/undo", methods=["POST"])
def api_undo():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    batch_id = data.get("batch_id")
    resolved_path = resolve_target_path(raw_path)

    history_mgr = HistoryManager(resolved_path)
    success, message, count = history_mgr.undo_batch(batch_id)

    return jsonify({
        "success": success,
        "message": message,
        "restored_count": count
    })

@app.route("/api/history", methods=["GET"])
def api_history():
    raw_path = request.args.get("target_dir", "DOWNLOADS")
    resolved_path = resolve_target_path(raw_path)
    history_mgr = HistoryManager(resolved_path)
    history = history_mgr.get_history()
    return jsonify({"success": True, "history": history})

@app.route("/api/history/24h", methods=["GET"])
def api_history_24h():
    raw_path = request.args.get("target_dir", "DOWNLOADS")
    resolved_path = resolve_target_path(raw_path)
    history_mgr = HistoryManager(resolved_path)
    digest = history_mgr.get_24h_digest()
    return jsonify({"success": True, "digest": digest})

# --------------------------------------------------------------------------
# Endpoints Watcher (Surveillance)
# --------------------------------------------------------------------------
@app.route("/api/watcher/start", methods=["POST"])
def start_watcher():
    global active_watcher
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    mode = data.get("mode", "type")

    resolved_path = resolve_target_path(raw_path)

    if active_watcher and active_watcher.is_running:
        active_watcher.stop()

    active_watcher = FolderWatcher(resolved_path, mode=mode)
    started = active_watcher.start()

    if started:
        return jsonify({"success": True, "is_running": True, "message": f"Surveillance démarrée sur {resolved_path}"})
    else:
        return jsonify({"success": False, "is_running": False, "message": "Impossible de démarrer la surveillance sur ce dossier."}), 400

@app.route("/api/watcher/stop", methods=["POST"])
def stop_watcher():
    global active_watcher
    if active_watcher and active_watcher.is_running:
        active_watcher.stop()
        active_watcher = None
        return jsonify({"success": True, "is_running": False, "message": "Surveillance arrêtée."})
    return jsonify({"success": True, "is_running": False, "message": "Aucune surveillance n'était active."})

@app.route("/api/watcher/status", methods=["GET"])
def watcher_status():
    global active_watcher
    is_running = active_watcher.is_running if active_watcher else False
    target_dir = str(active_watcher.target_dir) if active_watcher else None
    return jsonify({
        "is_running": is_running,
        "target_dir": target_dir
    })

def main():
    print("🚀 Démarrage du serveur web Smart File Organizer Pro...")
    print("🌐 Interface accessible sur: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()
