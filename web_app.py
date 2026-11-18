"""Local-only browser interface for GitHub Article Kit (stdlib only)."""
import html
import threading
import webbrowser
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
from repomix_bridge import build_from_repomix, repomix_package

HOST = '127.0.0.1'
PORT = int(os.environ.get('ARTICLE_KIT_PORT', '8765'))
VERSION = '0.41'
MAX_REQUEST = 2_200_000
# A local user can accidentally open multiple tabs. Do not spawn parallel npx processes.
GENERATION_SLOT = threading.BoundedSemaphore(1)
PAGE = '''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GitHub Article Kit</title><style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#17221c;background:#f4f7f4}body{max-width:680px;margin:48px auto;padding:0 18px}main{background:white;border:1px solid #d9e5dc;border-radius:18px;padding:28px;box-shadow:0 8px 30px #14281b0b}h1{margin:0 0 8px;font-size:1.8rem}.version{font-size:.75rem;color:#617064;font-weight:500;margin-left:8px}.advanced{margin:20px 0;border-top:1px solid #e5ebe6;padding-top:14px}.advanced summary{cursor:pointer;color:#45634d;font-weight:650}.muted{color:#617064}label{display:block;font-weight:650;margin:20px 0 8px}input[type=url],select{box-sizing:border-box;width:100%;padding:12px;border:1px solid #abbcaf;border-radius:9px;font:inherit}fieldset{border:0;padding:0;margin:16px 0}legend{font-weight:650;margin-bottom:10px}.choice{display:block;border:1px solid #d7e2da;padding:12px;border-radius:10px;margin:8px 0;font-weight:400}.choice input{margin-right:8px}button{background:#27854b;color:white;border:0;border-radius:10px;padding:14px 22px;font:inherit;font-weight:700;cursor:pointer;width:100%}.hint{font-size:.9rem;color:#617064;line-height:1.6}.error{background:#fff0ed;color:#902c24;padding:12px;border-radius:8px}footer{font-size:.85rem;margin:18px 0;color:#617064}</style><main><h1>GitHub Article Kit <span class="version">v0.41</span></h1><p class="muted">公開GitHubリポジトリから、AIに渡す記事執筆キットを無料で作成。</p>{notice}<form method="post" action="/generate" enctype="multipart/form-data"><label for="repo">GitHubリポジトリURL</label><input id="repo" type="url" name="repo" placeholder="https://github.com/owner/repository" required><fieldset><legend>記事のスタイル</legend><label class="choice"><input type="radio" name="style" value="technical" checked>技術解説型（おすすめ）<small class="muted"> — 要点を簡潔に</small></label><label class="choice"><input type="radio" name="style" value="story">開発ストーリー型<small class="muted"> — 背景や工夫も紹介</small></label></fieldset><label for="target">投稿先</label><select name="target" id="target"><option value="qiita">Qiita</option><option value="zenn">Zenn</option><option value="generic">一般ブログ</option></select><details class="advanced"><summary>詳細設定：既存のRepomix資料を使う</summary><label for="context">Repomix出力（任意・オフライン検証用）</label><input type="file" name="context" id="context" accept=".md,.txt,text/markdown,text/plain"><p class="hint">通常はファイル不要。URLからRepomixを実行します。既存のrepomix-output.mdを選ぶと再取得せずに作成します。アップロードした資料が入力URLのリポジトリと一致するかは自動検証されません。</p></details><button type="submit">記事キットを作成（ZIP）</button><p id="progress" class="hint" role="status" aria-live="polite"></p></form><footer>記事本文の生成は行いません。生成ZIPを展開し、START_HERE.md と repository_context.md をChatGPT等に添付して記事を執筆します。秘密情報の自動検出は完全ではありません。公開前に内容を確認してください。</footer></main><script>document.querySelector("form").addEventListener("submit",()=>{const b=document.querySelector("button");b.disabled=true;b.textContent="生成中…";document.getElementById("progress").textContent="GitHubから資料を取得しています。数分かかる場合があります。画面を閉じずにお待ちください。";});</script></html>'''

class Handler(BaseHTTPRequestHandler):
    def local_request(self):
        """Reject browser requests addressed through non-loopback hosts or foreign origins."""
        host = self.headers.get('Host', '').lower()
        if host not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
            return False
        origin = self.headers.get('Origin')
        if origin and origin.lower() not in (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'):
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return self.send_error(403)
        if self.path == '/health':
            return self.respond(200, b'ok', 'text/plain; charset=utf-8')
        if self.path == '/version':
            return self.respond(200, VERSION.encode(), 'text/plain; charset=utf-8')
        if self.path != '/':
            return self.send_error(404)
        self.respond(200, PAGE.replace('{notice}', '').encode(), 'text/html; charset=utf-8')

    def respond(self, status, data, mime, filename=None):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not GENERATION_SLOT.acquire(blocking=False):
            self.respond(429, PAGE.replace('{notice}', '<p class="error">別の記事キットを生成中です。完了してから再試行してください。</p>').encode(), 'text/html; charset=utf-8')
            return
        try:
            self._generate()
        finally:
            GENERATION_SLOT.release()

    def _generate(self):
        if not self.local_request():
            return self.send_error(403)
        if self.path != '/generate':
            return self.send_error(404)
        try:
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError as exc:
                raise ValueError('リクエストのサイズが正しくありません。') from exc
            if length < 1 or length > MAX_REQUEST:
                raise ValueError('アップロードは2MB以内にしてください。')
            body = self.rfile.read(length)
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                raise ValueError('フォーム形式が正しくありません。')
            msg = BytesParser(policy=default).parsebytes((f'MIME-Version: 1.0\r\nContent-Type: {content_type}\r\n\r\n').encode() + body)
            fields = {part.get_param('name', header='content-disposition'): part for part in msg.iter_parts()}
            def field(name, fallback=''):
                return fields[name].get_content() if name in fields else fallback
            repo = field('repo').strip()
            from repomix_bridge import URL
            if not URL.fullmatch(repo):
                raise ValueError('公開GitHubリポジトリのURLを入力してください。')
            style = field('style', 'technical')
            target = field('target', 'qiita')
            with tempfile.TemporaryDirectory() as temp:
                source = None
                if style not in ('technical', 'story') or target not in ('qiita', 'zenn', 'generic'):
                    raise ValueError('記事スタイルまたは投稿先が正しくありません。')
                origin = 'provided_context'
                if 'context' in fields and fields['context'].get_filename():
                    upload = fields['context'].get_payload(decode=True)
                    if len(upload) > 2_000_000:
                        raise ValueError('Repomix資料は2MB以内にしてください。')
                    source = Path(temp) / 'uploaded.md'
                    source.write_bytes(upload)
                executable = 'npx.cmd' if sys.platform == 'win32' else 'npx'
                # npx accepts the --yes option and package name; pass a fixed executable wrapper.
                if source is None:
                    repomix = Path(temp) / 'repomix.md'
                    cmd = [executable, '--yes', repomix_package(), '--remote', repo.removeprefix('https://github.com/').rstrip('/'), '--style', 'markdown', '--output', str(repomix)]
                    subprocess.run(cmd, check=True, capture_output=True, timeout=180)
                    if not repomix.is_file():
                        raise ValueError('Repomixの出力ファイルが作成されませんでした。')
                    if repomix.stat().st_size > 2_000_000:
                        raise ValueError('取得した資料が2MBを超えています。対象リポジトリを小さくしてください。')
                    source = repomix
                    origin = 'repomix_remote'
                output = Path(temp) / 'article_kit.zip'
                build_from_repomix(repo, target, output, context_file=source, style=style, context_origin=origin)
                data = output.read_bytes()
            self.respond(200, data, 'application/zip', f'article_kit_{style}.zip')
        except (ValueError, FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired, UnicodeError, OSError) as exc:
            if isinstance(exc, FileNotFoundError):
                message = 'Node.js / npx が見つかりません。Node.js をインストールしてください。'
            elif isinstance(exc, subprocess.TimeoutExpired):
                message = 'GitHubからの取得が3分以内に終わりませんでした。再試行してください。'
            elif isinstance(exc, subprocess.CalledProcessError):
                message = 'GitHubから取得できませんでした。公開リポジトリかURLと接続を確認してください。'
            else:
                message = str(exc)
            message = html.escape(message)[:400]
            self.respond(400, PAGE.replace('{notice}', f'<p class="error">生成できませんでした：{message}</p>').encode(), 'text/html; charset=utf-8')

def start_app(open_browser=True):
    """Bind first, open browser only after the intended server is ready."""
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as exc:
        raise RuntimeError(
            f'ポート {PORT} を使用できません。古いArticle Kitを終了してから再起動してください。'
            f' すでに http://{HOST}:{PORT}/ が開いている場合は、その画面のバージョンを確認してください。'
        ) from exc
    print(f'GitHub Article Kit v{VERSION} - http://{HOST}:{PORT}/', flush=True)
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(f'http://{HOST}:{PORT}/')).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == '__main__':
    try:
        start_app()
    except RuntimeError as exc:
        print(f'起動エラー: {exc}', file=sys.stderr)
        sys.exit(1)
