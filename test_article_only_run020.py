import unittest

from article_only import run


class ArticleOnlyRun020Tests(unittest.TestCase):

    def test_source_warnings_are_excluded(self):
        result = run(
            "# Setup\n\n"
            "See `missing.py` and `conf.yaml`.\n"
        )
        rules = [f["rule"] for f in result["findings"]]
        self.assertFalse(
            any(rule.startswith(("REF", "PY")) for rule in rules)
        )

    def test_duplicate_prose_is_detected(self):
        paragraph = (
            "This monitoring workflow validates endpoint status "
            "and records the results while carefully handling "
            "temporary network failures and unexpected responses."
        )
        result = run(
            "# Monitoring\n\n"
            + paragraph + "\n\n"
            + paragraph + "\n"
        )
        rules = [f["rule"] for f in result["findings"]]
        self.assertIn("TXT001", rules)

    def test_unclosed_code_fence_is_detected(self):
        result = run(
            "# Example\n\n"
            "```python\n"
            "print('hello')\n"
        )
        rules = [f["rule"] for f in result["findings"]]
        self.assertIn("MD001", rules)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
