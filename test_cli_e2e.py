"""End-to-end CLI smoke test with a fake Repomix executable (no network)."""
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class CliE2ETests(unittest.TestCase):
    def test_all_targets_through_cli(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            fake = d / 'fake_repomix.py'
            fake.write_text('''#!/usr/bin/env python3
import pathlib,sys
args=sys.argv[1:]
assert args[args.index('--remote')+1] == 'https://github.com/example-owner/sample-monitor'
assert args[args.index('--style')+1] == 'markdown'
p=pathlib.Path(args[args.index('--output')+1])
p.write_text('# sample-monitor\\n\\n## File: README.md\\nSynthetic monitoring example.\\n',encoding='utf-8')
''', encoding='utf-8')
            fake.chmod(0o755)
            for target in ('qiita', 'zenn', 'generic'):
                out = d / (target + '.zip')
                result = subprocess.run([sys.executable, str(ROOT/'repomix_bridge.py'),
                    'https://github.com/example-owner/sample-monitor', '--target', target,
                    '--out', str(out), '--repomix', str(fake)],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(out.is_file())
                with zipfile.ZipFile(out) as z:
                    self.assertEqual(set(z.namelist()), {'START_HERE.md','repository_context.md','manifest.json'})
                    self.assertIn('sample-monitor', z.read('repository_context.md').decode())
                    self.assertIn('未実行のテスト', z.read('START_HERE.md').decode())
                self.assertIn('sample-monitor', out.with_suffix('.md').read_text(encoding='utf-8'))

if __name__ == '__main__':
    unittest.main()
