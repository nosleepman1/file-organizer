import unittest
import tempfile
import shutil
import json
import sys
import os
from pathlib import Path

# Activer l'importation depuis backend/ et backend/core
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.config import ConfigManager
from core.organizer import FileOrganizer, safe_delete_file
from core.ai_organizer import DeepSeekEngine, extract_file_snippet

class TestSecurityAndMultiAI(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / "sample_doc.txt").write_text("Ceci est un document confidentiel de facturation 2026.", encoding="utf-8")
        (self.test_dir / "script.py").write_text("import os\nprint('code snippet')", encoding="utf-8")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_obfuscated_api_key_storage(self):
        cfg = ConfigManager(base_dir=str(self.test_dir))
        cfg.set("deepseek_api_key", "sk-secret-key-123456789")
        
        # Le getter doit retourner la clé en clair
        self.assertEqual(cfg.get("deepseek_api_key"), "sk-secret-key-123456789")
        self.assertTrue(cfg.get_masked_api_key().startswith("sk-s"))

        # Sur le disque JSON, la clé ne doit PAS apparaître en clair
        with open(cfg.config_file, "r", encoding="utf-8") as f:
            raw_json = json.load(f)
            stored_val = raw_json.get("deepseek_api_key", "")
            self.assertTrue(stored_val.startswith("ENC:"))
            self.assertNotIn("sk-secret-key-123456789", stored_val)

    def test_safe_trash_deletion(self):
        file_to_del = self.test_dir / "sample_doc.txt"
        self.assertTrue(file_to_del.exists())

        ok, msg = safe_delete_file(file_to_del)
        self.assertTrue(ok)
        # Le fichier d'origine ne doit plus exister à son emplacement initial
        self.assertFalse(file_to_del.exists())

    def test_content_aware_snippet_extraction(self):
        sample_file = self.test_dir / "sample_doc.txt"
        snippet = extract_file_snippet(sample_file, max_chars=100)
        self.assertIn("facturation 2026", snippet)

        py_file = self.test_dir / "script.py"
        snippet_py = extract_file_snippet(py_file, max_chars=100)
        self.assertIn("code snippet", snippet_py)

    def test_multi_provider_ai_engine(self):
        # Provider DeepSeek
        engine_ds = DeepSeekEngine(provider="deepseek", api_key="sk-test-123")
        self.assertEqual(engine_ds.provider, "deepseek")
        self.assertTrue(engine_ds.is_configured())

        # Provider Ollama (100% Offline, pas besoin de clé API)
        engine_ollama = DeepSeekEngine(provider="ollama", model="llama3")
        self.assertEqual(engine_ollama.provider, "ollama")
        self.assertTrue(engine_ollama.is_configured())

        # Provider OpenAI
        engine_oai = DeepSeekEngine(provider="openai", api_key="sk-proj-test")
        self.assertEqual(engine_oai.provider, "openai")
        self.assertTrue(engine_oai.is_configured())

if __name__ == "__main__":
    unittest.main()
