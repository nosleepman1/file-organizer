import unittest
import tempfile
import shutil
import os
from pathlib import Path
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
        self.assertIsInstance(desc, str)

    def test_history_24h_digest(self):
        history_mgr = HistoryManager(str(self.test_dir))
        moves = [
            {
                "source": str(self.test_dir / "script_test.py"),
                "destination": str(self.test_dir / "Code" / "script_test.py"),
                "file_name": "script_test.py",
                "category": "Code & Dev",
                "size_bytes": 100
            }
        ]
        batch_id = history_mgr.record_batch(moves)
        self.assertIsNotNone(batch_id)

        digest = history_mgr.get_24h_digest()
        self.assertEqual(digest["total_files_moved"], 1)
        self.assertEqual(digest["total_bytes_moved"], 100)
        self.assertIn("Code & Dev", digest["categories"])

    def test_surgical_filters_regex(self):
        organizer = FileOrganizer(str(self.test_dir))
        # Filtre Regex uniquement pour les fichiers PDF
        filters = {"regex": r".*\.pdf$"}
        actions = organizer.scan(mode="type", surgical_filters=filters)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["file_name"], "rapport_2026.pdf")

    def test_surgical_filters_size(self):
        organizer = FileOrganizer(str(self.test_dir))
        # Filtre taille minimale 1Mo (doit capturer uniquement le PDF de 2Mo)
        filters = {"min_size_mb": 1.0}
        actions = organizer.scan(mode="type", surgical_filters=filters)
        
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["file_name"], "rapport_2026.pdf")

    def test_deepseek_engine_unconfigured(self):
        engine = DeepSeekEngine(api_key="")
        self.assertFalse(engine.is_configured())
        ok, items, msg = engine.categorize_files([{"name": "test.txt"}])
        self.assertFalse(ok)
        self.assertIn("absente", msg.lower())

if __name__ == "__main__":
    unittest.main()
