import unittest
from article_validator import validate, mask_inline_code

class MarkdownEdgeCases(unittest.TestCase):
    def setUp(self):
        self.files={'README.md':'# Test'}
    def rules(self, text):
        return [f['rule'] for f in validate(text,self.files)['findings']]
    def test_escaped_link_is_literal(self):
        self.assertNotIn('LINK001',self.rules(r'\[example](missing.md)'))
    def test_double_escaped_link_is_active(self):
        self.assertIn('LINK001',self.rules(r'\\[example](missing.md)'))
    def test_double_backtick_code_is_not_link(self):
        self.assertNotIn('LINK001',self.rules('``[example](missing.md)``'))
    def test_real_link_after_double_backticks(self):
        self.assertEqual(self.rules('``[fake](bad.md)`` [real](missing.md)').count('LINK001'),1)
    def test_unclosed_inline_backtick_is_not_masked(self):
        self.assertIn('LINK001',self.rules('` unmatched [real](missing.md)'))
if __name__=='__main__': unittest.main()
