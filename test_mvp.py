import unittest
from github_to_qiita import parse_repo,render,prompt
class Tests(unittest.TestCase):
 def test_parse(self): self.assertEqual(parse_repo('https://github.com/example/project'),('example','project'))
 def test_reject(self):
  for url in ('http://github.com/a/b','https://evil.com/a/b','https://github.com/a/b/tree/main'):
   with self.assertRaises(ValueError):parse_repo(url)
 def test_output(self):
  d={'repository':'https://github.com/a/b','description':'test','branch':'main','truncated_tree':False,'files':[{'path':'README.md','url':'https://github.com/a/b/blob/main/README.md','content':'hello'}]}
  self.assertIn('README.md',render(d));self.assertIn('hello',prompt(d))
if __name__=='__main__':unittest.main()

class SecurityTests(unittest.TestCase):
 def test_sensitive_filter(self):
  from github_to_qiita import SENSITIVE
  for name in ('.env','.env.production','private/id_rsa','config/secrets.yaml','key.pem'):
   self.assertIsNotNone(SENSITIVE.search(name))
 def test_prompt_is_grounded(self):
  d={'repository':'https://github.com/a/b','description':'test','branch':'main','truncated_tree':False,'files':[]}
  self.assertIn('全機能を網羅したと断定しない',prompt(d))
