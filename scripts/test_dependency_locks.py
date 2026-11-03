import unittest

from scripts.check_dependency_locks import pins


class LockTests(unittest.TestCase):
    def test_hashes_and_normalized_extras(self):
        self.assertEqual(pins("Some_package[extra]==1.2 \\\n    --hash=sha256:" + "a" * 64,
            require_hashes=True), {"some-package": "1.2"})

    def test_missing_hash_duplicate_and_unpinned_rejected(self):
        for value in ("package==1", "package>=1", "package @ https://example.invalid/x", "-e .",
            "package==1 --hash=sha256:" + "a" * 64 + "\npackage==1 --hash=sha256:" + "a" * 64):
            with self.subTest(value=value), self.assertRaises(ValueError):
                pins(value, require_hashes=True)


if __name__ == "__main__":
    unittest.main()
