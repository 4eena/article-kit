"""Offline HTTP smoke test simulating the Repomix subprocess, not a network test."""
import hashlib
import http.client
import io
import json
import threading
import unittest
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from web_app import Handler
from verify_kit import verify
import tempfile

REPOS = ('https://github.com/example-owner/sample-monitor', 'https://github.com/octocat/Hello-World')

class SimulatedOnlineReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_two_repositories_all_style_target_combinations(self):
        calls = []
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            self.assertEqual(cmd[1:3], ['--yes', 'repomix@1.19.0'])
            self.assertEqual(kwargs['timeout'], 180)
            self.assertFalse(kwargs.get('text'))
            self.assertNotIn('encoding', kwargs)
            Path(cmd[cmd.index('--output') + 1]).write_text(
                '# File Summary\n\n## README.md\nSample project for ' + cmd[cmd.index('--remote') + 1],
                encoding='utf-8')
        with patch.dict('os.environ', {'ARTICLE_KIT_REPOMIX_VERSION': '1.19.0'}), patch('web_app.subprocess.run', side_effect=fake_run):
            for repo in REPOS:
                for style in ('technical', 'story'):
                    for target in ('qiita', 'zenn', 'generic'):
                        with self.subTest(repo=repo, style=style, target=target):
                            boundary = 'ArticleKitReleaseTest'
                            fields = {'repo': repo, 'style': style, 'target': target}
                            body = b''.join(
                                (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()
                                for name, value in fields.items()
                            ) + f'--{boundary}--\r\n'.encode()
                            conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
                            try:
                                conn.request('POST', '/generate', body, {'Content-Type': f'multipart/form-data; boundary={boundary}', 'Origin': f'http://127.0.0.1:{self.server.server_port}'})
                                response = conn.getresponse()
                                data = response.read()
                                self.assertEqual(response.status, 200, data[:250])
                            finally:
                                conn.close()
                            with tempfile.TemporaryDirectory() as d:
                                archive = Path(d) / 'result.zip'
                                archive.write_bytes(data)
                                manifest = verify(archive)
                                self.assertEqual(manifest['repository'], repo)
                                self.assertEqual(manifest['source'], 'repomix_remote')
                                self.assertEqual(manifest['style'], style)
                                self.assertEqual(manifest['target'], target)
                                with zipfile.ZipFile(io.BytesIO(data)) as z:
                                    self.assertIn(repo, z.read('START_HERE.md').decode())
        self.assertEqual(len(calls), 12)
        self.assertEqual({c[c.index('--remote') + 1] for c in calls}, {'example-owner/sample-monitor', 'octocat/Hello-World'})
