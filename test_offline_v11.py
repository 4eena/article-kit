import tempfile
import unittest
import zipfile
from pathlib import Path
from repomix_bridge import build_from_repomix

class OfflineTests(unittest.TestCase):
    def test_offline_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            context = root / 'repomix-output.md'
            context.write_text('# File: monitor.py\n\ndef check(): return True\n', encoding='utf-8')
            for target in ('qiita', 'zenn', 'generic'):
                out = root / (target + '.zip')
                build_from_repomix('https://github.com/example-owner/sample-monitor', target, out, executable='nonexistent-repomix', context_file=context)
                self.assertTrue(out.exists())
                self.assertTrue(out.with_suffix('.md').exists())
                with zipfile.ZipFile(out) as z:
                    self.assertIn('monitor.py', z.read('repository_context.md').decode())
                    self.assertIn('AI記事生成', z.read('START_HERE.md').decode())

    def test_missing_context(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                build_from_repomix('https://github.com/example-owner/sample-monitor', 'qiita', Path(td)/'out.zip', context_file=Path(td)/'missing.md')

    def test_size_guard(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = Path(td)/'large.md'
            ctx.write_text('x'*101)
            with self.assertRaises(ValueError):
                build_from_repomix('https://github.com/example-owner/sample-monitor', 'qiita', Path(td)/'out.zip', max_bytes=100, context_file=ctx)
