import io
import http.client
import threading
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path
from http.server import ThreadingHTTPServer
from web_app import Handler

class UrlOnlyTests(unittest.TestCase):
    def test_url_only_normalizes_remote_and_produces_zip(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        boundary = 'boundaryV24'
        def part(name, value):
            return f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        body = part('repo','https://github.com/example/demo/') + part('style','technical') + part('target','qiita') + f'--{boundary}--\r\n'.encode()
        seen = []
        def fake_run(cmd, **kwargs):
            seen.append(cmd)
            Path(cmd[cmd.index('--output') + 1]).write_text('# Repository\n\n## src/app.py\nprint("hello")', encoding='utf-8')
        try:
            with patch('web_app.subprocess.run', side_effect=fake_run):
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
                conn.request('POST','/generate',body,{'Content-Type':f'multipart/form-data; boundary={boundary}'})
                response = conn.getresponse()
                data = response.read()
                self.assertEqual(response.status, 200, data[:300])
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    self.assertIn('START_HERE.md',z.namelist())
                conn.close()
            self.assertEqual(seen[0][seen[0].index('--remote')+1], 'example/demo')
        finally:
            server.shutdown(); server.server_close()
