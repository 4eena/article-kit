import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from web_app import Handler, GENERATION_SLOT, VERSION

class BusyTests(unittest.TestCase):
    def test_single_generation_guard(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.assertTrue(GENERATION_SLOT.acquire(blocking=False))
            try:
                conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
                conn.request('POST', '/generate', body=b'irrelevant')
                res = conn.getresponse()
                self.assertEqual(res.status, 429)
                self.assertIn('生成中', res.read().decode())
                conn.close()
            finally:
                GENERATION_SLOT.release()
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port)
            conn.request('GET', '/version')
            res = conn.getresponse()
            self.assertEqual(res.read().decode(), '0.41')
            conn.close()
        finally:
            server.shutdown()
            server.server_close()
