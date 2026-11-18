import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from repomix_bridge import make_prompt, build_from_repomix

class ArticleStylesTest(unittest.TestCase):
    def test_style_prompts(self):
        a = make_prompt('https://github.com/example/repo', 'qiita', 'source', 'technical')
        b = make_prompt('https://github.com/example/repo', 'qiita', 'source', 'story')
        self.assertIn('簡潔', a)
        self.assertIn('制作背景', b)
        self.assertIn('創作しない', a)
        self.assertIn('創作せず', b)
        self.assertNotEqual(a,b)
    def test_default_and_story_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            source = d/'context.md'
            source.write_text('# sample\nprint("hi")\n', encoding='utf-8')
            for style in ('technical', 'story'):
                dest = d/(style+'.zip')
                build_from_repomix('https://github.com/example/repo','qiita',dest,context_file=source,style=style)
                with zipfile.ZipFile(dest) as z:
                    self.assertEqual(json.loads(z.read('manifest.json'))['style'],style)
                    self.assertIn('記事スタイル:',z.read('START_HERE.md').decode())
    def test_reject_invalid(self):
        with self.assertRaises(ValueError):
            make_prompt('https://github.com/example/repo','qiita','source','invalid')

if __name__ == '__main__': unittest.main()
