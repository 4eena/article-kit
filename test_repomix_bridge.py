import tempfile
import json
import hashlib
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from repomix_bridge import build_from_repomix

class BridgeTests(unittest.TestCase):
    def test_reject_non_github(self):
        with self.assertRaises(ValueError):
            build_from_repomix('https://evil.example/a/b', 'qiita', 'x.zip')
    def test_reject_unsupported_target(self):
        with self.assertRaises(ValueError):
            build_from_repomix('https://github.com/a/b', 'invalid', 'x.zip')
    def test_cli_and_artifacts(self):
        def fake_run(cmd, **kwargs):
            Path(cmd[cmd.index('--output')+1]).write_text('# Repository\n## File: README.md\nExample', encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {}, clear=True), patch('repomix_bridge.subprocess.run', side_effect=fake_run) as mock:
            out = Path(tmp)/'kit.zip'
            build_from_repomix('https://github.com/a/b', 'zenn', out)
            self.assertTrue(out.with_suffix('.md').exists())
            with zipfile.ZipFile(out) as z:
                self.assertEqual(set(z.namelist()), {'START_HERE.md', 'repository_context.md', 'manifest.json'})
                self.assertIn('Zenn', z.read('START_HERE.md').decode())
                manifest = json.loads(z.read('manifest.json'))
                context = z.read('repository_context.md')
                self.assertEqual(manifest['context_sha256'], hashlib.sha256(context).hexdigest())
            self.assertIn('--remote', mock.call_args.args[0])
        self.assertEqual(mock.call_args.args[0][1:3], ['--yes', 'repomix@1.19.0'])
    def test_limit(self):
        def fake_run(cmd, **kwargs):
            Path(cmd[cmd.index('--output')+1]).write_text('A'*100, encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp, patch('repomix_bridge.subprocess.run', side_effect=fake_run):
            with self.assertRaises(ValueError):
                build_from_repomix('https://github.com/a/b', 'qiita', Path(tmp)/'x.zip', max_bytes=10)

if __name__ == '__main__':
    unittest.main()
