import json
import unittest
from article_validator import validate, report_markdown

class RedactionRegressionTests(unittest.TestCase):
    def setUp(self):
        self.files={'README.md':'hello'}
        self.secret='ghp_'+'Z'*36

    def assert_redacted(self, article):
        result=validate(article,self.files)
        self.assertNotIn(self.secret,json.dumps(result,ensure_ascii=False))
        self.assertNotIn(self.secret,report_markdown(result))
        self.assertIn('[REDACTED_SECRET]',json.dumps(result,ensure_ascii=False))

    def test_missing_inline_file_path_does_not_leak_token(self):
        self.assert_redacted('See `'+self.secret+'.py`')

    def test_missing_link_path_does_not_leak_token(self):
        self.assert_redacted('[bad]('+self.secret+'.md)')

    def test_missing_github_link_does_not_leak_token(self):
        result=validate('[bad](https://github.com/me/repo/blob/main/'+self.secret+'.py)',self.files,'me/repo')
        self.assertNotIn(self.secret,json.dumps(result))
        self.assertNotIn(self.secret,report_markdown(result))

    def test_normal_path_remains_readable(self):
        result=validate('`missing.py`',self.files)
        self.assertIn('missing.py',report_markdown(result))

if __name__=='__main__':unittest.main()
