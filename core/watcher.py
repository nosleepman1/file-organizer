import time
import threading
from pathlib import Path
from core.organizer import FileOrganizer

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class FolderWatcher:
    def __init__(self, target_dir: str, mode: str = "type", debounce_seconds: int = 3):
        self.target_dir = Path(target_dir).resolve()
        self.mode = mode
        self.debounce_seconds = debounce_seconds
        self.is_running = False
        self.observer = None
        self.thread = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        if self.is_running:
            return True
        if not self.target_dir.exists() or not self.target_dir.is_dir():
            return False

        self.is_running = True
        self._stop_event.clear()

        if HAS_WATCHDOG:
            self._start_watchdog()
        else:
            self._start_fallback_polling()
        return True

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()

        if HAS_WATCHDOG and self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception:
                pass
            self.observer = None

    def _trigger_auto_organize(self):
        try:
            organizer = FileOrganizer(str(self.target_dir))
            actions = organizer.scan(mode=self.mode)
            if actions:
                organizer.execute(actions)
        except Exception as e:
            print(f"[Watcher] Erreur d'auto-organisation: {e}")

    def _start_watchdog(self):
        watcher_self = self

        class Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    # Attendre que l'écriture du fichier se termine
                    time.sleep(watcher_self.debounce_seconds)
                    watcher_self._trigger_auto_organize()

            def on_moved(self, event):
                if not event.is_directory:
                    time.sleep(watcher_self.debounce_seconds)
                    watcher_self._trigger_auto_organize()

        self.observer = Observer()
        self.observer.schedule(Handler(), str(self.target_dir), recursive=False)
        self.observer.start()

    def _start_fallback_polling(self):
        """Si watchdog n'est pas installé, scrutation simple toutes les 5 secondes."""
        def poll_loop():
            while not self._stop_event.is_set():
                self._trigger_auto_organize()
                self._stop_event.wait(5.0)

        self.thread = threading.Thread(target=poll_loop, daemon=True)
        self.thread.start()
