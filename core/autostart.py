import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Tuple

APP_NAME = "SmartFileOrganizer"

class AutostartManager:
    """Gère le démarrage automatique au boot de l'ordinateur de façon transparente et cross-platform."""

    def __init__(self):
        self.os_type = platform.system()  # 'Windows', 'Linux', 'Darwin'
        self.project_dir = Path(__file__).parent.parent.resolve()
        self.python_exec = sys.executable

    def get_status(self) -> Tuple[bool, str]:
        """Retourne (is_enabled, description_str)."""
        if self.os_type == "Windows":
            return self._status_windows()
        elif self.os_type == "Linux":
            return self._status_linux()
        elif self.os_type == "Darwin":
            return self._status_macos()
        else:
            return False, "Système d'exploitation non supporté."

    def enable(self) -> Tuple[bool, str]:
        """Active le démarrage automatique au boot de l'ordinateur."""
        if self.os_type == "Windows":
            return self._enable_windows()
        elif self.os_type == "Linux":
            return self._enable_linux()
        elif self.os_type == "Darwin":
            return self._enable_macos()
        else:
            return False, f"Démarrage au boot non supporté sur {self.os_type}"

    def disable(self) -> Tuple[bool, str]:
        """Désactive le démarrage automatique au boot."""
        if self.os_type == "Windows":
            return self._disable_windows()
        elif self.os_type == "Linux":
            return self._disable_linux()
        elif self.os_type == "Darwin":
            return self._disable_macos()
        else:
            return False, f"Démarrage au boot non supporté sur {self.os_type}"

    # --------------------------------------------------------------------------
    # Implementation Windows
    # --------------------------------------------------------------------------
    def _get_windows_startup_bat(self) -> Path:
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "smart_file_organizer_autostart.bat"
        return Path.home() / "smart_file_organizer_autostart.bat"

    def _status_windows(self) -> Tuple[bool, str]:
        bat_file = self._get_windows_startup_bat()
        if bat_file.exists():
            return True, f"Service actif (Script Startup Windows présent : {bat_file.name})"
        return False, "Démarrage automatique inactif."

    def _enable_windows(self) -> Tuple[bool, str]:
        bat_file = self._get_windows_startup_bat()
        try:
            bat_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Utilisation de pythonw si disponible pour ne pas ouvrir de fenêtre de console noire
            pythonw = Path(self.python_exec).parent / "pythonw.exe"
            py_bin = str(pythonw) if pythonw.exists() else str(self.python_exec)
            
            cli_script = self.project_dir / "organizer_cli.py"

            content = f'@echo off\nstart "" "{py_bin}" "{cli_script}" daemon\n'
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write(content)

            return True, f"Démarrage automatique Windows configuré dans le dossier Startup ({bat_file.name})."
        except Exception as e:
            return False, f"Erreur lors de la configuration du démarrage Windows : {e}"

    def _disable_windows(self) -> Tuple[bool, str]:
        bat_file = self._get_windows_startup_bat()
        try:
            if bat_file.exists():
                bat_file.unlink()
                return True, "Démarrage automatique Windows désactivé avec succès."
            return True, "Le démarrage automatique était déjà désactivé."
        except Exception as e:
            return False, f"Erreur lors de la désactivation Windows : {e}"

    # --------------------------------------------------------------------------
    # Implementation Linux (Systemd User Unit)
    # --------------------------------------------------------------------------
    def _get_linux_systemd_path(self) -> Path:
        return Path.home() / ".config" / "systemd" / "user" / "smart-file-organizer.service"

    def _status_linux(self) -> Tuple[bool, str]:
        service_file = self._get_linux_systemd_path()
        if service_file.exists():
            return True, "Service systemd utilisateur configuré."
        return False, "Démarrage automatique inactif."

    def _enable_linux(self) -> Tuple[bool, str]:
        service_file = self._get_linux_systemd_path()
        try:
            service_file.parent.mkdir(parents=True, exist_ok=True)
            cli_script = self.project_dir / "organizer_cli.py"

            content = f"""[Unit]
Description=Smart File Organizer Daemon (DeepSeek & Auto-Sort)
After=network.target

[Service]
Type=simple
ExecStart={self.python_exec} {cli_script} daemon
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
            with open(service_file, "w", encoding="utf-8") as f:
                f.write(content)

            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
            subprocess.run(["systemctl", "--user", "enable", "smart-file-organizer.service"], check=False)
            subprocess.run(["systemctl", "--user", "start", "smart-file-organizer.service"], check=False)

            return True, "Service systemd utilisateur installé et démarré avec succès !"
        except Exception as e:
            return False, f"Erreur configuration systemd Linux : {e}"

    def _disable_linux(self) -> Tuple[bool, str]:
        service_file = self._get_linux_systemd_path()
        try:
            subprocess.run(["systemctl", "--user", "stop", "smart-file-organizer.service"], check=False)
            subprocess.run(["systemctl", "--user", "disable", "smart-file-organizer.service"], check=False)
            if service_file.exists():
                service_file.unlink()
            return True, "Service systemd désactivé."
        except Exception as e:
            return False, f"Erreur désactivation systemd Linux : {e}"

    # --------------------------------------------------------------------------
    # Implementation macOS (Launchd)
    # --------------------------------------------------------------------------
    def _get_macos_plist_path(self) -> Path:
        return Path.home() / "Library" / "LaunchAgents" / "com.smartfileorganizer.daemon.plist"

    def _status_macos(self) -> Tuple[bool, str]:
        plist_file = self._get_macos_plist_path()
        if plist_file.exists():
            return True, "Agent macOS Launchd présent."
        return False, "Démarrage automatique inactif."

    def _enable_macos(self) -> Tuple[bool, str]:
        plist_file = self._get_macos_plist_path()
        try:
            plist_file.parent.mkdir(parents=True, exist_ok=True)
            cli_script = self.project_dir / "organizer_cli.py"

            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.smartfileorganizer.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.python_exec}</string>
        <string>{cli_script}</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""
            with open(plist_file, "w", encoding="utf-8") as f:
                f.write(content)

            subprocess.run(["launchctl", "load", str(plist_file)], check=False)
            return True, "Agent macOS Launchd configuré et activé au démarrage !"
        except Exception as e:
            return False, f"Erreur configuration macOS launchd : {e}"

    def _disable_macos(self) -> Tuple[bool, str]:
        plist_file = self._get_macos_plist_path()
        try:
            if plist_file.exists():
                subprocess.run(["launchctl", "unload", str(plist_file)], check=False)
                plist_file.unlink()
            return True, "Agent macOS Launchd désactivé."
        except Exception as e:
            return False, f"Erreur désactivation macOS launchd : {e}"

# Instanciation unique
autostart_mgr = AutostartManager()
