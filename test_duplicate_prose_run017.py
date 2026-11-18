import unittest
from article_validator import validate

class DuplicateProseTests(unittest.TestCase):
    def test_adjacent_long_duplicate_warns(self):
        para = "This monitoring workflow validates the endpoint status and records results with careful handling of transient failures. "
        report = validate("# Intro\n\n" + para + "\n\n" + para + "\n", {})
        self.assertEqual([f["rule"] for f in report["findings"]], ["TXT001"])

    def test_short_and_code_duplicates_ignored(self):
        report = validate("Short note.\n\nShort note.\n\n```text\n" + "x"*120 + "\n" + "x"*120 + "\n```", {})
        self.assertNotIn("TXT001", [f["rule"] for f in report["findings"]])

    def test_different_long_paragraphs_ignored(self):
        a = "A detailed explanation of how the status checker works and why each step is important for the operational environment. "
        b = "A detailed explanation of how the status checker works and why each step is important for the production environment. "
        report = validate(a + "\n\n" + b, {})
        self.assertNotIn("TXT001", [f["rule"] for f in report["findings"]])
