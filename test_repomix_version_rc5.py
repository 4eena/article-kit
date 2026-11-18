import unittest
from unittest.mock import patch
from web_app import repomix_package

class RepomixVersionTests(unittest.TestCase):
    def test_default(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(repomix_package(), 'repomix@1.19.0')
    def test_pinned(self):
        with patch.dict('os.environ', {'ARTICLE_KIT_REPOMIX_VERSION':'1.2.3'}):
            self.assertEqual(repomix_package(), 'repomix@1.2.3')
    def test_reject_injection(self):
        for bad in ['1.2.3 --foo', '@latest', 'file:../x', '1.2.3;echo', '']:
            with self.subTest(bad=bad), patch.dict('os.environ', {'ARTICLE_KIT_REPOMIX_VERSION':bad}):
                with self.assertRaises(ValueError):
                    repomix_package()
