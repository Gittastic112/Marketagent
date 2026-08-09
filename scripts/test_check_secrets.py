import tempfile
import unittest
from pathlib import Path

from scripts.check_secrets import scan_repository, scan_text


class SecretScannerTests(unittest.TestCase):
    def test_detects_credential_shapes_without_printing_values(self) -> None:
        api_key_name = "OPENAI" + "_API_KEY"
        api_key = "".join(("sk-", "proj-abcdefghijklmnopqrstuvwxyz123456"))
        password_name = "DATABASE" + "_PASSWORD"
        password_value = "".join(("actual-", "production-password"))
        findings = scan_text(
            Path("settings.py"),
            f'{api_key_name}="{api_key}"\n{password_name}="{password_value}"\n',
        )

        self.assertEqual(
            {finding.kind for finding in findings},
            {"openai_key", "credential_assignment"},
        )
        self.assertTrue(all(password_value not in repr(finding) for finding in findings))

    def test_allows_placeholders_and_excludes_generated_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.example").write_text(
                'OPENAI_API_KEY="your_openai_api_key"\n',
                encoding="utf-8",
            )
            generated = root / "node_modules"
            generated.mkdir()
            credential_name = "pass" + "word"
            generated_value = "unsafe-" + "value"
            (generated / "fixture.js").write_text(
                f'{credential_name}="{generated_value}"\n',
                encoding="utf-8",
            )

            self.assertEqual(scan_repository(root), [])


if __name__ == "__main__":
    unittest.main()
