import unittest
from build_kit import build

class KitTests(unittest.TestCase):
    def setUp(self):
        self.data={'repository':'https://github.com/a/b','files':[{'path':'main.py','url':'https://github.com/a/b/blob/main/main.py','content':'print("hi")'}]}
    def test_targets(self):
        for target in ('qiita','zenn','generic'):
            result=build(self.data,target)
            self.assertIn('print("hi")',result)
            self.assertIn('https://github.com/a/b/blob/main/main.py',result)
    def test_empty_rejected(self):
        with self.assertRaises(ValueError): build({'files':[]})
    def test_unknown_target(self):
        with self.assertRaises(ValueError): build(self.data,'unknown')
