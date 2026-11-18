import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLI = ROOT / "article_validator.py"


class ArticleOnlyCLITests(unittest.TestCase):

    def invoke(self, *extra):
        return subprocess.run(
            [sys.executable, str(CLI), *map(str, extra)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_article_only_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            article = root / "article.md"
            article.write_text(
                "# Sample\n\nThis is a simple test article.\n",
                encoding="utf-8",
            )
            out = root / "report"

            result = self.invoke(
                "--article", article,
                "--article-only",
                "--out", out,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out / "report.json").exists())
            self.assertTrue((out / "report.md").exists())

            data = json.loads(
                (out / "report.json").read_text(encoding="utf-8")
            )
            self.assertFalse(
                any(
                    f["rule"].startswith(("REF", "PY"))
                    for f in data["findings"]
                )
            )

    def test_missing_article_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.invoke(
                "--article", Path(tmp) / "missing.md",
                "--article-only",
                "--out", Path(tmp) / "report",
            )
            self.assertEqual(result.returncode, 2)

    def test_source_modes_are_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.invoke(
                "--article", Path(tmp) / "article.md",
                "--article-only",
                "--source-dir", tmp,
            )
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
