"""Verify the extracted Article Kit release. Outputs and npm cache stay on disk."""
import argparse
import http.client
import locale
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent


def run(command, **kwargs):
    return subprocess.run(command, cwd=ROOT, check=True, timeout=240, **kwargs)


def request(port, method, path, body=None, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=210)
    try:
        connection.request(method, path, body, headers or {})
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def check_zip(path, expected, verify):
    manifest = verify(path)
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise RuntimeError(f'Unexpected manifest in {path.name}: {manifest}')
    print(f'OK: {path.name}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('distribution_zip', type=Path)
    parser.add_argument('--repo', default='https://github.com/octocat/Hello-World')
    parser.add_argument('--offline', action='store_true', help='Skip npm and GitHub')
    args = parser.parse_args()

    from repomix_bridge import URL, repomix_command
    from verify_kit import verify
    from web_app import Handler, VERSION

    if not URL.fullmatch(args.repo):
        parser.error('--repo must be a public GitHub repository URL')
    with ZipFile(args.distribution_zip) as archive:
        names = archive.namelist()
        if (len(names) != len(set(names)) or archive.testzip() is not None
                or '01_事前チェック.bat' not in names
                or '02_生成ZIPを検証.bat' not in names):
            raise RuntimeError('Distribution archive CRC, path names or uniqueness check failed')
        for name in names:
            path = (ROOT / name).resolve()
            if ROOT not in path.parents or not path.is_file() or path.read_bytes() != archive.read(name):
                raise RuntimeError(f'Extracted file differs from ZIP: {name}')
    print(f'OK: distribution ZIP and all {len(names)} extracted files', flush=True)
    print(f'Python {sys.version.split()[0]}, locale {locale.getpreferredencoding(False)}', flush=True)
    # Run the actual release defaults even if the parent environment has an override.
    os.environ.pop('ARTICLE_KIT_REPOMIX_VERSION', None)
    if repomix_command()[1:3] != ['--yes', 'repomix@1.19.0']:
        raise RuntimeError('CLI default does not request Repomix 1.19.0')
    run([sys.executable, 'preflight.py'])
    if args.offline:
        print('OFFLINE PASS: live npm, GitHub and browser checks are pending.')
        return
    node = run(['node', '--version'], stdout=subprocess.PIPE).stdout.decode('ascii').strip()
    npx = shutil.which('npx.cmd' if sys.platform == 'win32' else 'npx')
    if npx is None:
        raise RuntimeError('npx launcher is missing')
    output = run([npx, '--yes', 'repomix@1.19.0', '--version'], stdout=subprocess.PIPE).stdout
    if not re.search(rb'(?<![\d.])1\.19\.0(?![\d.])', output):
        raise RuntimeError('npm launcher did not report Repomix 1.19.0')
    print(f'OK: Node {node}, Repomix 1.19.0', flush=True)
    artifacts = Path(tempfile.mkdtemp(prefix='Article Kit 非ASCII '))
    print(f'Output directory: {artifacts}', flush=True)
    cli_path = artifacts / 'cli.zip'
    run([sys.executable, 'repomix_bridge.py', args.repo, '--out', str(cli_path)])
    expected = {'repository': args.repo, 'target': 'qiita'}
    check_zip(cli_path, dict(expected, source='repomix_cli', style='technical'), verify)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, page = request(server.server_port, 'GET', '/')
        if status != 200 or f'v{VERSION}'.encode() not in page:
            raise RuntimeError('Web home page did not report the expected version')
        boundary = 'ArticleKitWindowsVerification'
        for style in ('technical', 'story'):
            fields = dict(repo=args.repo, target='qiita', style=style)
            body = ''.join(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'
                for key, value in fields.items()
            ).encode() + f'--{boundary}--\r\n'.encode()
            headers = {'Content-Type': f'multipart/form-data; boundary={boundary}',
                       'Origin': f'http://127.0.0.1:{server.server_port}'}
            status, data = request(server.server_port, 'POST', '/generate', body, headers)
            archive = artifacts / f'web-{style}.zip'
            if status != 200:
                error_path = archive.with_suffix('.html')
                error_path.write_bytes(data)
                raise RuntimeError(f'Web generation returned HTTP {status}. See {error_path}')
            archive.write_bytes(data)
            check_zip(archive, dict(expected, source='repomix_remote', style=style), verify)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    print('AUTOMATED PASS: start_windows.bat and the real browser still need a manual check.')


if __name__ == '__main__':
    main()
