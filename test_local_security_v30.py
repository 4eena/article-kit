import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from web_app import Handler

class LocalSecurityTests(unittest.TestCase):
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

    def request(self, method, path, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port)
        conn.request(method, path, headers=headers or {})
        response = conn.getresponse()
        status = response.status
        response.read()
        conn.close()
        return status

    def test_localhost_accepted(self):
        self.assertEqual(self.request('GET', '/', {'Host': f'localhost:{self.port}'}), 200)

    def test_external_host_rejected(self):
        self.assertEqual(self.request('GET', '/', {'Host': f'evil.example:{self.port}'}), 403)

    def test_external_origin_rejected(self):
        self.assertEqual(self.request('POST', '/generate', {'Origin': 'https://evil.example'}), 403)

    def test_local_origin_reaches_validation(self):
        self.assertEqual(self.request('POST', '/generate', {'Origin': f'http://127.0.0.1:{self.port}'}), 400)
