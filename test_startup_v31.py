import unittest
from unittest.mock import patch, MagicMock
import web_app

class StartupTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(web_app.VERSION, '0.41')
        self.assertIn('v0.41', web_app.PAGE)

    def test_port_collision_does_not_open_browser(self):
        with patch.object(web_app, 'ThreadingHTTPServer', side_effect=OSError('busy')):
            with patch.object(web_app.webbrowser, 'open') as browser:
                with self.assertRaisesRegex(RuntimeError, '古いArticle Kit'):
                    web_app.start_app()
                browser.assert_not_called()

    def test_bind_before_browser(self):
        events=[]
        server=MagicMock()
        server.serve_forever.side_effect=lambda: events.append('serve')
        with patch.object(web_app, 'ThreadingHTTPServer', side_effect=lambda *a: events.append('bind') or server):
            with patch.object(web_app.threading, 'Timer') as timer:
                web_app.start_app()
                self.assertEqual(events, ['bind','serve'])
                timer.assert_called_once()
                server.server_close.assert_called_once()

if __name__ == '__main__': unittest.main()
