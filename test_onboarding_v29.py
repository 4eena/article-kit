import unittest
from pathlib import Path
from web_app import PAGE, VERSION
from repomix_bridge import make_prompt
class OnboardingTests(unittest.TestCase):
    def test_version(self):
        self.assertGreaterEqual(tuple(map(int, VERSION.split('.'))), (0,29))
        self.assertIn(f'v{VERSION}', PAGE)
    def test_web_instructions(self):
        self.assertIn('START_HERE.md と repository_context.md',PAGE)
    def test_prompt_instructions(self):
        self.assertIn('両方を読んでください',make_prompt('https://github.com/a/b','qiita','x'))
    def test_readme(self):
        text=(Path(__file__).parent/'はじめにお読みください.md').read_text(encoding='utf-8')
        self.assertIn('start_windows.bat',text)
        self.assertIn('記事本文を自動生成するツールではありません',text)
if __name__=='__main__': unittest.main()
