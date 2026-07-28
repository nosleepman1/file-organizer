import unittest
import shutil
import tempfile
from pathlib import Path
import sys
import os

# Ajouter le répertoire racine au sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.rules import get_category_for_extension
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

if __name__ == "__main__":
    unittest.main()
