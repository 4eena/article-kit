import http.client
import threading
import unittest
import zipfile
import io
from http.server import ThreadingHTTPServer
from web_app import Handler

class WebUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_home(self):
        conn = http.client.HTTPConnection('127.0.0.1', self.port)
        conn.request('GET', '/')
        res = conn.getresponse()
        page = res.read().decode()
        self.assertEqual(res.status, 200)
        self.assertIn('開発ストーリー型', page)
        conn.close()

    def test_health(self):
        conn = http.client.HTTPConnection('127.0.0.1', self.port)
        conn.request('GET', '/health')
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        self.assertEqual(res.read(), b'ok')
        conn.close()

    def test_upload_story_zip(self):
        boundary = 'testBoundary123'
        parts = []
        def add(name, value, filename=None):
            disposition = f'Content-Disposition: form-data; name="{name}"'
            if filename:
                disposition += f'; filename="{filename}"'
            parts.append(f'--{boundary}\r\n{disposition}\r\nContent-Type: text/plain\r\n\r\n'.encode() + value + b'\r\n')
        add('repo', b'https://github.com/example-owner/sample-monitor')
        add('style', b'story')
        add('target', b'qiita')
        add('context', b'# Repomix\n\n# monitor.py\nprint("hello")\n', 'repomix-output.md')
        body = b''.join(parts) + f'--{boundary}--\r\n'.encode()
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        conn.request('POST', '/generate', body, {'Content-Type': f'multipart/form-data; boundary={boundary}'})
        res = conn.getresponse()
        content = res.read()
        self.assertEqual(res.status, 200, content[:500])
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            self.assertIn('開発ストーリー型', z.read('START_HERE.md').decode())
        conn.close()
