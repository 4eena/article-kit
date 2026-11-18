"""Regression tests proving the Repomix bridge is repository-agnostic."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from repomix_bridge import build_from_repomix

class RepositoryAgnosticTests(unittest.TestCase):
    def test_two_unrelated_repositories(self):
        repos = ['https://github.com/example-org/weather-cli', 'https://github.com/another-org/react-dashboard']
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            context = base / 'repomix.md'
            context.write_text('# Files\n## src/main.ts\nexport const hello = () => "hello";\n', encoding='utf-8')
            for index, repo in enumerate(repos):
                output = base / f'kit-{index}.zip'
                build_from_repomix(repo, 'zenn', output, context_file=context)
                with zipfile.ZipFile(output) as z:
                    self.assertIn(repo, z.read('START_HERE.md').decode())
                    self.assertEqual(z.read('repository_context.md').decode(), context.read_text())
                    manifest = json.loads(z.read('manifest.json'))
                    self.assertEqual(manifest['repository'], repo)
                    self.assertEqual(manifest['target'], 'zenn')
    def test_reject_non_github_url(self):
        with self.assertRaises(ValueError):
            build_from_repomix('https://example.com/not-a-repo', 'qiita', 'x.zip', context_file='none')
