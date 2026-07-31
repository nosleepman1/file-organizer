import os
import sys
from pathlib import Path

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

app = Flask(__name__, static_folder="web")

active_watcher = None

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory("web/css", filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("web/js", filename)

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "healthy",
        "app": "Smart File Organizer Pro",
        "version": "2.0.0-OpenSource"
    })

# --------------------------------------------------------------------------
# Endpoints DeepSeek IA
# --------------------------------------------------------------------------
@app.route("/api/ai/config", methods=["GET", "POST"])
def api_ai_config():
    if request.method == "POST":
        data = request.json or {}
        if "deepseek_api_key" in data and data["deepseek_api_key"]:
            global_config.set("deepseek_api_key", data["deepseek_api_key"])
        if "deepseek_model" in data:
            global_config.set("deepseek_model", data["deepseek_model"])
        if "deepseek_custom_prompt" in data:
            global_config.set("deepseek_custom_prompt", data["deepseek_custom_prompt"])

        return jsonify({
            "success": True,
            "message": "Configuration IA sauvegardée avec succès !",
            "masked_key": global_config.get_masked_api_key(),
            "model": global_config.get("deepseek_model"),
            "custom_prompt": global_config.get("deepseek_custom_prompt")
        })
    else:
        return jsonify({
            "success": True,
            "has_key": bool(global_config.get("deepseek_api_key")),
            "masked_key": global_config.get_masked_api_key(),
            "model": global_config.get("deepseek_model"),
            "custom_prompt": global_config.get("deepseek_custom_prompt")
        })

@app.route("/api/ai/test", methods=["POST"])
def api_ai_test():
    data = request.json or {}
    test_key = data.get("api_key")
    model = data.get("model", "deepseek-chat")

    engine = DeepSeekEngine(api_key=test_key, model=model)
    success, message = engine.test_connection(test_key=test_key)

    return jsonify({"success": success, "message": message})

# --------------------------------------------------------------------------
# Endpoints Autostart Service (OS Boot)
# --------------------------------------------------------------------------
@app.route("/api/service/autostart", methods=["GET", "POST"])
def api_autostart_service():
    if request.method == "POST":
        data = request.json or {}
        enable = bool(data.get("enable", False))
        if enable:
            success, msg = autostart_mgr.enable()
        else:
            success, msg = autostart_mgr.disable()
        return jsonify({"success": success, "message": msg, "enabled": enable})
    else:
        is_enabled, desc = autostart_mgr.get_status()
        return jsonify({"success": True, "enabled": is_enabled, "description": desc})

# --------------------------------------------------------------------------
# Endpoints Tri & Operations
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
        return jsonify({
            "success": False, 
            "message": f"Dossier introuvable ou invalide : {resolved_path}"
        }), 400

    actions = organizer.scan(
        mode=mode, 
        recursive=recursive, 
        surgical_filters=surgical_filters,
        ai_custom_prompt=ai_custom_prompt
    )
    stats = organizer.get_stats()

    return jsonify({
        "success": True,
        "target_dir": resolved_path,
        "mode": mode,
        "actions": actions,
        "stats": stats
    })

@app.route("/api/organize", methods=["POST"])
def api_organize():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    actions = data.get("actions", [])

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not actions:
        return jsonify({"success": False, "message": "Aucune action fournie à exécuter."}), 400

    result = organizer.execute(actions)
    return jsonify(result)

@app.route("/api/duplicates", methods=["POST"])
def api_duplicates():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    recursive = bool(data.get("recursive", False))

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({"success": False, "message": f"Dossier invalide : {resolved_path}"}), 400

    groups = organizer.scan_duplicates(recursive=recursive)
    return jsonify({
        "success": True,
        "target_dir": resolved_path,
        "groups": groups
    })

@app.route("/api/duplicates/delete", methods=["POST"])
def api_delete_duplicates():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    file_paths = data.get("file_paths", [])

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

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
    if active_watcher:
        active_watcher.stop()
        active_watcher = None
    return jsonify({"success": True, "is_running": False, "message": "Surveillance en arrière-plan arrêtée."})

@app.route("/api/watcher/status", methods=["GET"])
def watcher_status():
    global active_watcher
    is_running = active_watcher.is_running if active_watcher else False
    return jsonify({"is_running": is_running})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 Serveur Smart File Organizer Pro en ligne sur http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
