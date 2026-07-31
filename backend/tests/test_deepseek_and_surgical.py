import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path

# Activer l'importation depuis backend/ et backend/core
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.config import ConfigManager
from core.history import HistoryManager
from core.organizer import FileOrganizer
from core.autostart import AutostartManager
from core.ai_organizer import DeepSeekEngine

class TestDeepSeekAndSurgical(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Créer des fichiers de test fictifs
        (self.test_dir / "rapport_2026.pdf").write_bytes(b"A" * (2 * 1024 * 1024))  # 2MB
        (self.test_dir / "photo_vacances.jpg").write_bytes(b"B" * 500)             # 500B
        (self.test_dir / "script_test.py").write_text("print('hello')", encoding="utf-8")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_config_manager(self):
        cfg = ConfigManager(base_dir=str(self.test_dir))
        cfg.set("deepseek_api_key", "sk-1234567890abcdef")
        self.assertTrue(cfg.get_masked_api_key().startswith("sk-1"))
        self.assertEqual(cfg.get("deepseek_model"), "deepseek-chat")

    def test_autostart_manager(self):
        mgr = AutostartManager()
        status, desc = mgr.get_status()
        self.assertIsInstance(status, bool)

    def test_surgical_filters_scan(self):
        organizer = FileOrganizer(str(self.test_dir))
        
        # Test filtre Taille (> 1MB)
        actions = organizer.scan(surgical_filters={"min_size_mb": 1.0})
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["file_name"], "rapport_2026.pdf")

        # Test filtre Regex (*.py)
        actions_py = organizer.scan(surgical_filters={"regex": r"\.py$"})
        self.assertEqual(len(actions_py), 1)
        self.assertEqual(actions_py[0]["file_name"], "script_test.py")

    def test_history_24h_digest(self):
        hist_mgr = HistoryManager(str(self.test_dir))
        moves = [
            {
                "source": str(self.test_dir / "test.txt"),
                "destination": str(self.test_dir / "Documents" / "test.txt"),
                "file_name": "test.txt",
                "category": "Documents",
                "size_bytes": 1024
            }
        ]
        batch_id = hist_mgr.record_batch(moves)
        self.assertIsNotNone(batch_id)

        digest = hist_mgr.get_24h_digest()
        self.assertEqual(digest["total_files_moved"], 1)
        self.assertIn("Documents", digest["categories"])

    def test_deepseek_engine_unconfigured(self):
        engine = DeepSeekEngine(api_key="")
        configured = engine.is_configured()
        if engine.provider != "ollama":
            self.assertFalse(configured)

if __name__ == "__main__":
    unittest.main()
