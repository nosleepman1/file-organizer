import unittest
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Activer l'importation depuis backend/ et backend/core
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.hash_cache import HashCacheManager, global_hash_cache
from core.organizer import FileOrganizer

class TestPerformanceAndCache(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Fichiers identiques pour tester les doublons
        (self.test_dir / "file_a.txt").write_bytes(b"SAME_CONTENT_123456789")
        (self.test_dir / "file_b.txt").write_bytes(b"SAME_CONTENT_123456789")
        (self.test_dir / "file_unique.txt").write_bytes(b"UNIQUE_CONTENT")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_hash_cache_manager(self):
        cache_mgr = HashCacheManager(base_dir=str(self.test_dir))
        target_file = self.test_dir / "file_a.txt"

        # Premier appel (calcul et mise en cache)
        hash1 = cache_mgr.get_hash(target_file)
        self.assertTrue(len(hash1) > 0)
        self.assertIn(str(target_file.resolve()), cache_mgr.cache_data)

        # Deuxième appel (doit restituer depuis le cache)
        hash2 = cache_mgr.get_hash(target_file)
        self.assertEqual(hash1, hash2)

    def test_parallel_duplicate_scan(self):
        organizer = FileOrganizer(str(self.test_dir))
        duplicates = organizer.scan_duplicates()

        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["count"], 2)
        dup_names = [f["file_name"] for f in duplicates[0]["files"]]
        self.assertIn("file_a.txt", dup_names)
        self.assertIn("file_b.txt", dup_names)

if __name__ == "__main__":
    unittest.main()
