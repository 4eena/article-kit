import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from build_kit import main

class EvidenceSecurityTests(unittest.TestCase):
    def test_evidence_cli_blocks_secret_without_writing_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            evidence = root / 'evidence.json'
            evidence.write_text(json.dumps({'repository': 'example/repo', 'files': [{'path': 'config.py', 'url': 'https://github.com/example/repo/blob/main/config.py', 'content': 'KEY=AKIA' + 'A'*16}]}), encoding='utf-8')
            out = root / 'kit.zip'
            with patch('sys.argv', ['build_kit.py', str(evidence), '--out', str(out)]):
                with self.assertRaisesRegex(ValueError, 'aws_access_key') as err:
                    main()
            self.assertNotIn('AKIA', str(err.exception))
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix('.md').exists())

if __name__ == '__main__':
    unittest.main()
