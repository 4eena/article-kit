"""Regression tests for Windows console encoding and child process failures."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from repomix_bridge import build_from_repomix

REPO = 'https://github.com/example-owner/sample-monitor'

class RepomixOutputTests(unittest.TestCase):
    def test_unicode_console_bytes_do_not_require_decoding(self):
        def fake_run(cmd, **kwargs):
            self.assertNotIn('text', kwargs)
            self.assertNotIn('encoding', kwargs)
            self.assertEqual(kwargs['stdout'], subprocess.PIPE)
            self.assertEqual(kwargs['stderr'], subprocess.PIPE)
            Path(cmd[cmd.index('--output') + 1]).write_text(
                '# sample-monitor\n\n## File: README.md\nExample\n', encoding='utf-8')
            return subprocess.CompletedProcess(cmd, 0, stdout=b'\x81\x8b', stderr=b'\xff')
        with tempfile.TemporaryDirectory() as td, patch('repomix_bridge.subprocess.run', side_effect=fake_run):
            out = Path(td) / 'article.zip'
            build_from_repomix(REPO, 'qiita', out, executable='repomix')
            self.assertTrue(out.is_file())

    def test_failed_child_cannot_create_successful_zip(self):
        def fake_run(cmd, **kwargs):
            raise subprocess.CalledProcessError(1, cmd, stderr=b'\xff')
        with tempfile.TemporaryDirectory() as td, patch('repomix_bridge.subprocess.run', side_effect=fake_run):
            out = Path(td) / 'article.zip'
            with self.assertRaises(subprocess.CalledProcessError):
                build_from_repomix(REPO, 'qiita', out, executable='repomix')
            self.assertFalse(out.exists())

if __name__ == '__main__':
    unittest.main()
