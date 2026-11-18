import unittest
from article_validator import validate

class ReferenceLinksRun009(unittest.TestCase):
    def rules(self,article):
        return [f['rule'] for f in validate(article,{'README.md':'ok'})['findings']]
    def test_reference_link_missing(self):
        self.assertIn('LINK001',self.rules('[Guide][docs]\n\n[docs]: missing.md'))
    def test_reference_link_exists(self):
        self.assertNotIn('LINK001',self.rules('[Guide][docs]\n\n[docs]: README.md'))
    def test_reference_case_whitespace(self):
        self.assertIn('LINK001',self.rules('[Guide][A  B]\n[A b]: missing.md'))
    def test_collapsed_reference(self):
        self.assertIn('LINK001',self.rules('[Guide][]\n[guide]: missing.md'))
    def test_unused_definition_no_warning(self):
        self.assertNotIn('LINK001',self.rules('[unused]: missing.md'))
    def test_code_reference_not_link(self):
        self.assertNotIn('LINK001',self.rules('`[Guide][docs]`\n[docs]: missing.md'))
    def test_parent_relative_uncertain(self):
        rules=self.rules('[Guide](../docs/missing.md)')
        self.assertIn('LINK002',rules)
        self.assertNotIn('LINK001',rules)

if __name__=='__main__':unittest.main()
