import unittest
from unittest.mock import patch
from repomix_bridge import repomix_command

@patch.dict('os.environ', {}, clear=True)
class WindowsLauncherTests(unittest.TestCase):
    def test_explicit_npx_cmd(self):
        self.assertEqual(repomix_command('npx.cmd'), ['npx.cmd', '--yes', 'repomix@1.19.0'])
    def test_explicit_npx(self):
        self.assertEqual(repomix_command('npx'), ['npx', '--yes', 'repomix@1.19.0'])
    def test_python_fake_remains_compatible(self):
        self.assertEqual(repomix_command('fake_repomix.py')[1:], ['fake_repomix.py'])
    @patch('repomix_bridge.sys.platform', 'win32')
    @patch('repomix_bridge.shutil.which', side_effect=lambda x: None if x == 'repomix' else 'C:/node/npx.cmd')
    def test_windows_default_fallback(self, _):
        self.assertEqual(repomix_command('repomix'), ['C:/node/npx.cmd', '--yes', 'repomix@1.19.0'])
    @patch('repomix_bridge.shutil.which', return_value='/usr/bin/repomix')
    def test_installed_repomix_unchanged(self, _):
        self.assertEqual(repomix_command('repomix'), ['repomix'])
