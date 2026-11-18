import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from verify_kit import verify

class VerifyKitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/"test.zip"
        self.context = b"# example\n"
        self.manifest = {"repository":"https://github.com/example/repo","target":"qiita","style":"technical","source":"repomix_remote","context_bytes":len(self.context),"context_sha256":hashlib.sha256(self.context).hexdigest()}
    def tearDown(self): self.tmp.cleanup()
    def write(self, **changes):
        m = {**self.manifest, **changes}
        with zipfile.ZipFile(self.path,'w') as z:
            z.writestr('START_HERE.md','write an article')
            z.writestr('repository_context.md',self.context)
            z.writestr('manifest.json',json.dumps(m))
    def test_valid(self):
        self.write()
        self.assertEqual(verify(self.path)['source'],'repomix_remote')
    def test_hash_mismatch(self):
        self.write(context_sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'SHA256'): verify(self.path)
    def test_size_mismatch(self):
        self.write(context_bytes=999)
        with self.assertRaisesRegex(ValueError,'サイズ'): verify(self.path)
    def test_invalid_source(self):
        self.write(source='invented')
        with self.assertRaisesRegex(ValueError,'取得元'): verify(self.path)
    def test_missing_file(self):
        with zipfile.ZipFile(self.path,'w') as z: z.writestr('manifest.json','{}')
        with self.assertRaisesRegex(ValueError,'構成'): verify(self.path)

if __name__=='__main__': unittest.main()
