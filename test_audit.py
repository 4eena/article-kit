import unittest
from evidence_audit import audit

E = {'repository':'https://github.com/a/b','truncated_tree':False,'files':[{'path':'monitor.py','url':'https://github.com/a/b/blob/main/monitor.py','content':'print(1)'}]}

class AuditTests(unittest.TestCase):
    def test_valid_citation(self):
        r = audit(E, '[monitor](https://github.com/a/b/blob/main/monitor.py)')
        self.assertTrue(r['ok']); self.assertEqual(r['warnings'], [])
    def test_unverified_citation(self):
        r = audit(E, 'https://github.com/a/b/blob/main/fake.py')
        self.assertTrue(any('Unverified' in w for w in r['warnings']))
    def test_missing_evidence(self):
        r = audit({**E,'files':[]}, '')
        self.assertFalse(r['ok'])
    def test_incomplete_tree(self):
        r = audit({**E,'truncated_tree':True}, '')
        self.assertTrue(any('truncated' in w for w in r['warnings']))
    def test_template_warning(self):
        r = audit(E, '<!-- README とコードを確認して執筆 -->')
        self.assertTrue(any('template' in w for w in r['warnings']))

if __name__ == '__main__': unittest.main()
