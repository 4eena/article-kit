import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import article_validator as av

class SourceDirectorySafetyTests(unittest.TestCase):
    def test_hidden_directory_not_collected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'.private').mkdir()
            (root/'.private'/'secret.py').write_text('sensitive')
            (root/'main.py').write_text('print(1)')
            self.assertEqual(set(av.from_directory(root)),{'main.py'})

    def test_symlinked_file_not_collected(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            root=Path(d)
            (root/'main.py').write_text('print(1)')
            (Path(outside)/'secret.py').write_text('secret')
            try:(root/'link.py').symlink_to(Path(outside)/'secret.py')
            except (OSError,NotImplementedError):self.skipTest('symlink not supported')
            self.assertEqual(set(av.from_directory(root)),{'main.py'})

    def test_aggregate_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'a.py').write_text('a'*20)
            (root/'b.py').write_text('b'*20)
            with patch.object(av,'MAX_SOURCE',30):
                with self.assertRaisesRegex(ValueError,'total size limit'):
                    av.from_directory(root)

    def test_regular_file_remains_usable(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'sub').mkdir()
            (root/'sub'/'code.py').write_text('def go(): pass')
            self.assertIn('sub/code.py',av.from_directory(root))

if __name__=='__main__':unittest.main()
