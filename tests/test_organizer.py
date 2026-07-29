import unittest
import shutil
import tempfile
from pathlib import Path
import sys
import os

# Ajouter le répertoire racine au sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.rules import get_category_for_extension, is_temp_or_ignored, save_custom_rules, load_custom_rules
from core.organizer import FileOrganizer
from core.history import HistoryManager

class TestSmartFileOrganizer(unittest.TestCase):

    def setUp(self):
        # Créer un dossier temporaire pour les tests
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Créer quelques fichiers fictifs
        (self.test_dir / "document_1.pdf").write_text("dummy content pdf")
        (self.test_dir / "photo_1.png").write_text("dummy content png")
        (self.test_dir / "script.py").write_text("print('hello')")
        (self.test_dir / "archive.zip").write_text("dummy zip")

    def tearDown(self):
        # Nettoyer le dossier temporaire
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_rules_categorization(self):
        self.assertEqual(get_category_for_extension("pdf"), "Documents")
        self.assertEqual(get_category_for_extension(".png"), "Images")
        self.assertEqual(get_category_for_extension("py"), "Code & Dev")
        self.assertEqual(get_category_for_extension("unknown_ext_xyz"), "Autres")

    def test_temp_file_exclusion(self):
        temp_file = self.test_dir / "download.crdownload"
        temp_file.write_text("partial download content")
        self.assertTrue(is_temp_or_ignored(temp_file))

        organizer = FileOrganizer(str(self.test_dir))
        actions = organizer.scan(mode="type")
        action_sources = [a["source"] for a in actions]
        self.assertNotIn(str(temp_file), action_sources)

    def test_scan_and_execute(self):
        organizer = FileOrganizer(str(self.test_dir))
        actions = organizer.scan(mode="type")

        self.assertEqual(len(actions), 4)

        # Exécuter l'organisation
        res = organizer.execute(actions)
        self.assertTrue(res["success"])
        self.assertEqual(res["count"], 4)

        # Vérifier que les sous-dossiers ont été créés et les fichiers déplacés
        self.assertTrue((self.test_dir / "Documents" / "document_1.pdf").exists())
        self.assertTrue((self.test_dir / "Images" / "photo_1.png").exists())
        self.assertTrue((self.test_dir / "Code & Dev" / "script.py").exists())
        self.assertTrue((self.test_dir / "Archives" / "archive.zip").exists())

    def test_undo_functionality(self):
        organizer = FileOrganizer(str(self.test_dir))
        actions = organizer.scan(mode="type")
        organizer.execute(actions)

        # Vérifier que les fichiers ont bougé
        self.assertFalse((self.test_dir / "document_1.pdf").exists())

        # Effectuer l'annulation
        history_mgr = HistoryManager(str(self.test_dir))
        success, msg, restored = history_mgr.undo_last_batch()

        self.assertTrue(success)
        self.assertEqual(restored, 4)

        # Vérifier que les fichiers sont revenus à la racine
        self.assertTrue((self.test_dir / "document_1.pdf").exists())
        self.assertTrue((self.test_dir / "photo_1.png").exists())
        self.assertTrue((self.test_dir / "script.py").exists())
        self.assertTrue((self.test_dir / "archive.zip").exists())

    def test_duplicate_detection(self):
        # Créer deux fichiers strictement identiques
        dup1 = self.test_dir / "file_copy1.txt"
        dup2 = self.test_dir / "file_copy2.txt"
        content = "Identical content for SHA256 test hash 123456"
        dup1.write_text(content)
        dup2.write_text(content)

        organizer = FileOrganizer(str(self.test_dir))
        groups = organizer.scan_duplicates()

        self.assertGreaterEqual(len(groups), 1)
        group = groups[0]
        self.assertEqual(group["count"], 2)

        # Supprimer le doublon 2
        res = organizer.delete_duplicates([str(dup2)])
        self.assertTrue(res["success"])
        self.assertEqual(res["deleted_count"], 1)
        self.assertFalse(dup2.exists())
        self.assertTrue(dup1.exists())

    def test_bulk_rename(self):
        file_with_spaces = self.test_dir / "My Test File 1.pdf"
        file_with_spaces.write_text("some pdf text")

        organizer = FileOrganizer(str(self.test_dir))
        res = organizer.bulk_rename(replace_spaces="_", lowercase=True)

        self.assertTrue(res["success"])
        self.assertTrue((self.test_dir / "my_test_file_1.pdf").exists())

    def test_custom_rules_persistence(self):
        custom = {"Design": ["psd", "blend"], "Docs": ["pdf"]}
        save_custom_rules(custom, str(self.test_dir))

        loaded = load_custom_rules(str(self.test_dir))
        self.assertIn("Design", loaded)
        self.assertEqual(loaded["Design"], ["psd", "blend"])

if __name__ == "__main__":
    unittest.main()
