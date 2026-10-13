"""The retired evaluator must never report an invented successful score."""
from pathlib import Path
import subprocess
import sys
import unittest


class LegacyFinancialEvaluatorTests(unittest.TestCase):
    def test_legacy_entrypoint_cannot_be_mistaken_for_a_passed_evaluation(self):
        script = Path(__file__).resolve().with_name("evaluate_financial_extraction.py")
        result = subprocess.run(
            [sys.executable, "-I", str(script)],
            capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Not available", result.stderr)
        self.assertIn("Evaluation Lab", result.stderr)
        self.assertIn("independently reviewed reference", result.stderr)
        self.assertNotIn("[PASS]", result.stdout)
        self.assertNotIn("Precision:", result.stdout)


if __name__ == "__main__":
    unittest.main()
