import unittest
from article_generator import generate

class GeneratorTest(unittest.TestCase):
    def setUp(self):
        self.data = {'repository':'https://github.com/example/demo','branch':'main','files':[{'path':'main.py','url':'https://github.com/example/demo/blob/main/main.py','content':'def hello():\n    return 1\n'}]}
    def test_function_evidence(self):
        article=generate(self.data)
        self.assertIn('`hello()`（1行目）',article)
        self.assertIn('未検証',article)
    def test_no_files(self):
        self.data['files']=[]
        with self.assertRaises(ValueError): generate(self.data)
    def test_no_invented_description(self):
        self.assertNotIn('通知に成功',generate(self.data))
    def test_invalid_python(self):
        self.data['files'][0]['content']='def x('
        self.assertIn('構文解析不可',generate(self.data))

if __name__=='__main__': unittest.main()
