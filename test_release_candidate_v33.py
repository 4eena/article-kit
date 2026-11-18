import unittest
from pathlib import Path
import web_app

class ReleaseCandidateTests(unittest.TestCase):
    def test_version_matches_page(self):
        self.assertIn('v' + web_app.VERSION, web_app.PAGE)
    def test_remote_output_size_guard_present(self):
        source = Path(web_app.__file__).read_text(encoding='utf-8')
        self.assertIn('repomix.stat().st_size > 2_000_000', source)
    def test_bad_length_guard_present(self):
        source = Path(web_app.__file__).read_text(encoding='utf-8')
        self.assertIn('リクエストのサイズが正しくありません', source)
