import tempfile
import unittest
from pathlib import Path
from article_validator import from_repomix, from_directory, validate, report_markdown

class ArticleValidatorTests(unittest.TestCase):
    def setUp(self):
        self.files={'monitor.py':'def get_status():\n    return 1\n\ndef send_telegram():\n    pass\n','README.md':'# Test'}
    def test_clean(self):
        r=validate('# Title\n\n`monitor.py` contains `get_status()`.',self.files)
        self.assertTrue(r['ok']);self.assertEqual(r['summary']['warning'],0)
    def test_missing_file(self):
        r=validate('See `missing.py`',self.files)
        self.assertIn('REF001',[f['rule'] for f in r['findings']])
    def test_unclosed_fence(self):
        self.assertFalse(validate('```python\nprint(1)',self.files)['ok'])
    def test_secret_redacted(self):
        secret='AKIA'+'A'*16
        r=validate('token '+secret,self.files)
        self.assertFalse(r['ok']);self.assertNotIn(secret,report_markdown(r))
    def test_explicit_missing_symbol(self):
        r=validate('`monitor.py:missing()`',self.files)
        self.assertIn('PY002',[f['rule'] for f in r['findings']])
    def test_qualified_missing_source_warns(self):
        r=validate('`absent.py:foo()`',self.files)
        self.assertIn('REF001',[f['rule'] for f in r['findings']])
        self.assertNotIn('PY002',[f['rule'] for f in r['findings']])
    def test_class_method_exists(self):
        files={'module.py':'class Worker:\n    def run(self): pass\n'}
        r=validate('`module.py:Worker.run()`',files)
        self.assertEqual(r['summary']['error'],0)
    def test_class_method_missing(self):
        files={'module.py':'class Worker:\n    def run(self): pass\n'}
        r=validate('`module.py:Worker.stop()`',files)
        self.assertIn('PY002',[f['rule'] for f in r['findings']])
    def test_nested_function_not_public(self):
        files={'module.py':'def outer():\n    def inner(): pass\n'}
        r=validate('`module.py:inner()`',files)
        self.assertIn('PY002',[f['rule'] for f in r['findings']])
    def test_symbol_valid(self):
        self.assertTrue(validate('`monitor.py:get_status()`',self.files)['ok'])
    def test_external_link_not_checked(self):
        self.assertTrue(validate('[x](https://example.org/a)',self.files)['ok'])
    def test_github_link_missing(self):
        r=validate('[x](https://github.com/me/repo/blob/main/missing.py)',self.files,'me/repo')
        self.assertIn('REF002',[f['rule'] for f in r['findings']])
    def test_github_slash_branch_existing_file(self):
        files={'src/monitor.py':'def run(): pass'}
        r=validate('[x](https://github.com/me/repo/blob/feature/my-branch/src/monitor.py)',files,'me/repo')
        self.assertFalse(any(f['rule'].startswith('REF') for f in r['findings']))
    def test_github_slash_branch_unknown_is_not_false_error(self):
        r=validate('[x](https://github.com/me/repo/blob/feature/my-branch/src/missing.py)',self.files,'me/repo')
        self.assertNotIn('REF002',[f['rule'] for f in r['findings']])
        self.assertIn('REF003',[f['rule'] for f in r['findings']])
    def test_github_without_repo_does_not_assume_identity(self):
        r=validate('[x](https://github.com/other/repo/blob/main/missing.py)',self.files)
        self.assertFalse(any(f['rule'].startswith('REF') for f in r['findings']))
    def test_github_link_other_repo(self):
        r=validate('[x](https://github.com/other/repo/blob/main/missing.py)',self.files,'me/repo')
        self.assertEqual(r['summary']['warning'],0)
    def test_link_in_inline_code_is_not_validated(self):
        r=validate('Example: `[docs](missing.md)`',self.files)
        self.assertNotIn('LINK001',[f['rule'] for f in r['findings']])
    def test_github_link_in_inline_code_is_not_validated(self):
        r=validate('`[source](https://github.com/me/repo/blob/main/missing.py)`',self.files,'me/repo')
        self.assertNotIn('REF002',[f['rule'] for f in r['findings']])
    def test_real_link_next_to_inline_code_still_validated(self):
        r=validate('`[example](fake.md)` and [real](missing.md)',self.files)
        self.assertEqual([f['rule'] for f in r['findings']].count('LINK001'),1)
        self.assertIn('missing.md',str(r['findings']))
    def test_real_github_link_next_to_inline_code_still_validated(self):
        r=validate('`[fake](https://github.com/me/repo/blob/main/fake.py)` and [real](https://github.com/me/repo/blob/main/missing.py)',self.files,'me/repo')
        self.assertEqual([f['rule'] for f in r['findings']].count('REF002'),1)
        self.assertIn('missing.py',str(r['findings']))
    def test_link_with_parentheses_is_complete(self):
        files={**self.files, 'docs/guide(v2).md':'ok'}
        r=validate('[guide](docs/guide(v2).md)',files)
        self.assertNotIn('LINK001',[f['rule'] for f in r['findings']])

    def test_missing_link_with_parentheses(self):
        r=validate('[guide](docs/missing(v2).md)',self.files)
        self.assertIn('LINK001',[f['rule'] for f in r['findings']])
        self.assertIn('docs/missing(v2).md',str(r['findings']))

    def test_link_with_title(self):
        r=validate('[guide](missing.md "Read guide")',self.files)
        self.assertEqual([f['rule'] for f in r['findings']].count('LINK001'),1)

    def test_angle_link_with_spaces(self):
        files={**self.files,'docs/my guide.md':'ok'}
        r=validate('[guide](<docs/my guide.md>)',files)
        self.assertNotIn('LINK001',[f['rule'] for f in r['findings']])

    def test_repomix(self):
        t='## File: monitor.py\n```python\ndef foo(): pass\n```\n'
        self.assertIn('monitor.py',from_repomix(t))
    def test_repomix_nested_header_is_source_text(self):
        source='## File: main.py\n````python\n# ## File: not-a-file.py\n## File: fake.py\n```python\nprint(1)\n````\n'
        files=from_repomix(source)
        self.assertEqual(set(files),{'main.py'})
        self.assertIn('## File: fake.py',files['main.py'])
    def test_repomix_unclosed_block_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'Unclosed Repomix'):
            from_repomix('## File: main.py\n```python\nprint(1)\n')
    def test_repomix_crlf_and_tilde_fences(self):
        files=from_repomix('## File: main.py\r\n~~~python\r\nprint(1)\r\n~~~\r\n')
        self.assertEqual(files['main.py'],'print(1)')
    def test_source_dir(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'monitor.py').write_text('def foo(): pass')
            self.assertIn('monitor.py',from_directory(d))
    def test_heading(self):
        r=validate('# A\n### B',self.files)
        self.assertIn('MD002',[f['rule'] for f in r['findings']])
    def test_code_fence_ignored(self):
        r=validate('```\n`missing.py`\n```',self.files)
        self.assertEqual(r['summary']['warning'],0)
    def test_no_secret_in_json(self):
        secret='ghp_'+'A'*36
        self.assertNotIn(secret,str(validate(secret,self.files)))
if __name__=='__main__':unittest.main()
