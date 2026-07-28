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

# Résolution automatique des répertoires systèmes
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

# Instance globale pour le watcher
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

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    mode = data.get("mode", "type")

    resolved_path = resolve_target_path(raw_path)
    organizer = FileOrganizer(resolved_path)

    if not organizer.is_valid_directory():
        return jsonify({
            "success": False, 
            "message": f"Dossier introuvable ou invalide : {resolved_path}"
        }), 400

    actions = organizer.scan(mode=mode)
    stats = organizer.get_stats()

    return jsonify({
        "success": True,
        "target_dir": resolved_path,
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

@app.route("/api/undo", methods=["POST"])
def api_undo():
    data = request.json or {}
    raw_path = data.get("target_dir", "DOWNLOADS")
    resolved_path = resolve_target_path(raw_path)

    history_mgr = HistoryManager(resolved_path)
    success, message, count = history_mgr.undo_last_batch()

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
    port = 5000
    print(f"🚀 Serveur Smart File Organizer démarré sur http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
