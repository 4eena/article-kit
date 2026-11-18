import unittest
from pathlib import Path
from web_app import repomix_package
from unittest.mock import patch

ROOT = Path(__file__).parent
class ReleaseConsistencyTests(unittest.TestCase):
    def test_default_dependency_is_pinned(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(repomix_package(), 'repomix@1.19.0')
    def test_readme_does_not_claim_latest_default(self):
        self.assertNotIn('repomix@latest', (ROOT/'README.md').read_text(encoding='utf-8'))
    def test_release_checklist_identifies_outstanding_checks(self):
        text=(ROOT/'RELEASE_CHECKLIST.md').read_text(encoding='utf-8')
        self.assertIn('固定版RepomixでのWindows実機確認',text)
        self.assertIn('推移的依存関係のライセンス確認',text)
