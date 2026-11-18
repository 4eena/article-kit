"""Offline dependency and regression check. No GitHub/npm traffic."""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

MIN_NODE_MAJOR = 22

def node_major(version):
    match = re.fullmatch(r"v?(\d+)\.\d+\.\d+", version.strip())
    return int(match.group(1)) if match else None

def command_version(command):
    try:
        return subprocess.run([command, '--version'], capture_output=True, text=True, timeout=8, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None

def main():
    root = Path(__file__).resolve().parent
    node = shutil.which('node')
    npx = shutil.which('npx.cmd' if sys.platform == 'win32' else 'npx')
    git = shutil.which('git')
    node_version = command_version(node) if node else None
    major = node_major(node_version) if node_version else None
    requirements = {
        'Python 3.9以上': sys.version_info >= (3, 9),
        'Node.js 22以上': major is not None and major >= MIN_NODE_MAJOR,
        'npx': bool(npx),
        'Git': bool(git),
        'Webアプリ本体': (root/'web_app.py').is_file(),
        'Windows起動スクリプト': (root/'start_windows.bat').is_file(),
    }
    print('GitHub Article Kit - オフライン事前検査')
    print('Python:', sys.version.split()[0], 'Node.js:', node_version or '未検出')
    for name, passed in requirements.items():
        print(('OK' if passed else 'NG') + ': ' + name)
    suite = unittest.defaultTestLoader.discover(str(root), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    print('注意: GitHub通信、Repomix実行、Windowsブラウザ動作は未検証です。')
    return 0 if all(requirements.values()) and result.wasSuccessful() else 1

if __name__ == '__main__':
    raise SystemExit(main())
