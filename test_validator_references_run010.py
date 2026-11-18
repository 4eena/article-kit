import unittest
from article_validator import validate

class ReferenceBoundaryRun010(unittest.TestCase):
    def rules(self, article):
        return [x['rule'] for x in validate(article, {'README.md':'ok'})['findings']]
    def test_escaped_reference_use_is_literal(self):
        self.assertNotIn('LINK001', self.rules(r'\[Guide][docs]'+'\n[docs]: missing.md'))
    def test_double_escape_reference_is_active(self):
        self.assertIn('LINK001', self.rules(r'\\[Guide][docs]'+'\n[docs]: missing.md'))
    def test_inline_code_definition_is_not_active(self):
        self.assertNotIn('LINK001', self.rules('[Guide][docs]'+'\n`[docs]: missing.md`'))
    def test_real_reference_definition_still_active(self):
        self.assertIn('LINK001', self.rules('[Guide][docs]'+'\n[docs]: missing.md'))

if __name__=='__main__': unittest.main()
