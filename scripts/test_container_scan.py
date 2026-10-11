import unittest

from scripts.check_container_scan import summarize


class ScanTests(unittest.TestCase):
    def test_incomplete_scan_fails_closed(self):
        for report in ({}, {"Metadata": {"OS": {"Family": "debian"}}, "Results": []}):
            with self.assertRaises(ValueError): summarize(report)

    def test_all_findings_reported_and_available_severe_fixes_block(self):
        counts, blockers = summarize({"Metadata": {"OS": {"Family": "debian"}}, "Results": [{
            "Class": "os-pkgs", "Packages": [{"Name": "package"}], "Vulnerabilities": [
                {"Severity": "CRITICAL"}, {"Severity": "HIGH", "FixedVersion": "2"},
                {"Severity": "LOW", "FixedVersion": "2"}]}]})
        self.assertEqual(counts, {"CRITICAL": 1, "HIGH": 1, "LOW": 1})
        self.assertEqual(blockers, 1)


if __name__ == "__main__":
    unittest.main()
