import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class QiitaAcceptance(unittest.TestCase):
    def run_validator(self, article):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'src').mkdir()
            (root / 'src' / 'monitor.py').write_text(
                'def check_status():\n    return True\n',
                encoding='utf-8'
            )
            (root / 'article.md').write_text(article, encoding='utf-8')
            result = subprocess.run(
                [
                    sys.executable, str(ROOT / 'article_validator.py'),
                    '--article', str(root / 'article.md'),
                    '--source-dir', str(root / 'src'),
                    '--repo', 'example-owner/sample-monitor',
                    '--out', str(root / 'report')
                ],
                capture_output=True, text=True,
                encoding='utf-8', errors='replace'
            )
            report = json.loads(
                (root / 'report' / 'report.json').read_text(encoding='utf-8')
            )
            markdown = (
                root / 'report' / 'report.md'
            ).read_text(encoding='utf-8')
            return result, report, markdown

    def test_valid_qiita_article_no_false_positive(self):
        article = (
            '# GitHub Actionsによる死活監視\n\n'
            '`monitor.py:check_status()` を実装しました。\n\n'
            '```python\nprint("example.py:missing()")\n```\n'
        )
        proc, report, markdown = self.run_validator(article)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report['summary']['error'], 0)
        self.assertEqual(report['summary']['warning'], 0)
        self.assertIn('品質検査レポート', markdown)

    def test_missing_function_and_unclosed_fence_report(self):
        article = (
            '# 監視処理\n\n'
            '`monitor.py:does_not_exist()`\n\n'
            '```python\nprint("hello")\n'
        )
        proc, report, markdown = self.run_validator(article)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(
            {x['rule'] for x in report['findings']
             if x['severity'] == 'error'},
            {'MD001', 'PY002'}
        )
        self.assertIn('PY002', markdown)
