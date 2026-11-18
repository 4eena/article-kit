import unittest
from web_app import PAGE, VERSION

class UsabilityTests(unittest.TestCase):
    def test_visible_version(self):
        self.assertGreaterEqual(tuple(map(int, VERSION.split('.'))), (0,29))
        self.assertIn(f'v{VERSION}', PAGE)
    def test_advanced_input_collapsed(self):
        self.assertIn('<details class="advanced">', PAGE)
        self.assertIn('</details><button', PAGE)
        self.assertNotIn('<details class="advanced" open', PAGE)
    def test_main_action_visible(self):
        self.assertIn('記事キットを作成（ZIP）', PAGE)
        self.assertIn('value="technical" checked', PAGE)
    def test_context_warning(self):
        self.assertIn('一致するかは自動検証されません', PAGE)
if __name__ == '__main__': unittest.main()
