import unittest
from article_generator import generate
from evidence_audit import audit

E = {"repository": "https://github.com/example-owner/sample-monitor", "branch": "main", "files": [{"path": "README.md", "url": "https://github.com/example-owner/sample-monitor/blob/main/README.md", "content": "# sample-monitor\nSynthetic monitoring example.\n"}]}

class CoverageTests(unittest.TestCase):
    def test_readme_only_discloses_limitation(self):
        self.assertIn("資料不足", generate(E))
        self.assertTrue(any("No implementation code" in w for w in audit(E, generate(E))["warnings"]))
    def test_code_evidence_does_not_raise_coverage_warning(self):
        e = {**E, "files": [{"path": "main.py", "url": "https://github.com/example-owner/sample-monitor/blob/main/main.py", "content": "print(1)"}]}
        self.assertFalse(any("No implementation code" in w for w in audit(e, generate(e))["warnings"]))
