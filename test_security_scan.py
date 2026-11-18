import tempfile
import unittest
from pathlib import Path
from repomix_bridge import build_from_repomix
from security_scan import scan

class SecurityTests(unittest.TestCase):
    def test_aws_key(self):
        self.assertEqual(scan('prefix\nAKIA' + 'A'*16), [('aws_access_key', 2)])
    def test_private_key(self):
        self.assertEqual(scan('-----BEGIN PRIVATE KEY-----'), [('private_key', 1)])
    def test_normal_code(self):
        self.assertEqual(scan('def main():\n  return 1'), [])
    def test_block_export(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/'packed.md'
            source.write_text('AKIA' + 'A'*16)
            out = Path(d)/'kit.zip'
            with self.assertRaisesRegex(ValueError, 'Potential secrets'):
                build_from_repomix('https://github.com/example-owner/sample-monitor', 'qiita', out, context_file=source)
            self.assertFalse(out.exists())

if __name__ == '__main__':
    unittest.main()

class TelegramRegressionTests(unittest.TestCase):
    def test_telegram_token_is_blocked_without_leaking_value(self):
        token = '123456789:' + 'A' * 35
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'packed.md'
            source.write_text('bot token = ' + token, encoding='utf-8')
            with self.assertRaises(ValueError) as error:
                build_from_repomix('https://github.com/example/unrelated-project', 'qiita', Path(tmp) / 'kit.zip', context_file=source)
            self.assertIn('telegram_bot_token', str(error.exception))
            self.assertNotIn(token, str(error.exception))
            self.assertFalse((Path(tmp) / 'kit.zip').exists())

    def test_regular_telegram_link_is_not_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'packed.md'
            source.write_text('Documentation: https://t.me/example_channel', encoding='utf-8')
            output = Path(tmp) / 'kit.zip'
            build_from_repomix('https://github.com/example/unrelated-project', 'zenn', output, context_file=source)
            self.assertTrue(output.is_file())
