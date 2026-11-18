import unittest
import ast
from article_generator import describe_verified_patterns, generate
class PatternTests(unittest.TestCase):
    def test_patterns(self):
        src = "def f():\n    urllib.request.urlopen('x')\n    state.write_text('x')\n    if count >= 2: pass\n"
        self.assertEqual(len(describe_verified_patterns(ast.parse(src))), 3)
    def test_no_patterns(self):
        self.assertEqual(describe_verified_patterns(ast.parse('def f(): pass')), [])
    def test_article(self):
        e = {'repository':'https://github.com/a/b','branch':'main','files':[{'path':'x.py','url':'https://github.com/a/b/blob/main/x.py','content':"def f():\n    urllib.request.urlopen('x')\n"}]}
        self.assertIn('通信成功は未検証', generate(e))
