import unittest
from article_validator import validate, inline_code_values

class InlineRun015Tests(unittest.TestCase):
    def test_multibacktick_reference_is_checked(self):
        report = validate(
            'Refer to ``src.py:missing()``.',
            {'src.py': 'def exists(): pass'}
        )
        self.assertEqual(
            [f['rule'] for f in report['findings']],
            ['PY002']
        )

    def test_unmatched_and_nested_backticks_do_not_make_false_reference(self):
        report = validate(
            'Example: `` `missing.py` `` and unmatched `missing2.py',
            {'real.py': 'pass'}
        )
        self.assertFalse(
            any(f['rule'] == 'REF001' for f in report['findings'])
        )
        self.assertEqual(
            list(inline_code_values('`` `hello` ``')),
            ['`hello`']
        )
