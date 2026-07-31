import sys
from pathlib import Path

# Activer l'importation propre depuis backend/ et backend/core/
BASE_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BASE_DIR))

from backend.organizer_cli import main

if __name__ == "__main__":
    main()
