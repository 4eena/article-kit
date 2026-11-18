import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from repomix_bridge import build_from_repomix

class ProvenanceTests(unittest.TestCase):
    def test_provided_context_is_not_mislabeled_repomix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            context = root / "input.md"
            context.write_text("# Example\nSome code.", encoding="utf-8")
            output = root / "out.zip"
            build_from_repomix("https://github.com/example/project", "qiita", output, context_file=context)
            with zipfile.ZipFile(output) as z:
                manifest = json.loads(z.read("manifest.json"))
                prompt = z.read("START_HERE.md").decode()
            self.assertEqual(manifest["source"], "provided_context")
            self.assertIs(manifest["context_is_complete_repository"], False)
            self.assertIn("全リポジトリ取得を確認していません", prompt)
