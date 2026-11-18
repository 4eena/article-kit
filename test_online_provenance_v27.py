import io, json, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
from web_app import Handler
from repomix_bridge import build_from_repomix
import tempfile

SAMPLE_CONTEXT = "# Sample Monitor\n\n## File: README.md\nSynthetic monitoring example.\n"

class ProvenanceV27(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.context = Path(workspace.name) / "repomix-output.md"
        self.context.write_text(SAMPLE_CONTEXT, encoding="utf-8")

    def test_remote_marked_only_when_remote_execution_succeeds(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.zip'
            build_from_repomix('https://github.com/example-owner/sample-monitor','qiita',out,context_file=self.context,context_origin='repomix_remote')
            with zipfile.ZipFile(out) as z:
                m=json.loads(z.read('manifest.json'))
                self.assertEqual(m['source'],'repomix_remote')
                self.assertTrue(m['repository_identity_verified'])
                self.assertIsNone(m['context_is_complete_repository'])
    def test_upload_remains_unverified(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.zip'
            build_from_repomix('https://github.com/example-owner/sample-monitor','qiita',out,context_file=self.context)
            with zipfile.ZipFile(out) as z:
                m=json.loads(z.read('manifest.json'))
                self.assertEqual(m['source'],'provided_context')
                self.assertFalse(m['repository_identity_verified'])

class WebRemotePathV27(unittest.TestCase):
    def test_url_only_marks_remote(self):
        import http.client, threading
        from http.server import ThreadingHTTPServer
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def fake_run(cmd, **kwargs):
            Path(cmd[cmd.index('--output')+1]).write_text(SAMPLE_CONTEXT, encoding="utf-8")
        boundary='v27boundary'
        fields=[('repo','https://github.com/example-owner/sample-monitor'),('style','technical'),('target','qiita')]
        body=b''.join((f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n').encode() for k,v in fields)+f'--{boundary}--\r\n'.encode()
        try:
            with patch('web_app.subprocess.run',side_effect=fake_run):
                c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
                c.request('POST','/generate',body,{'Content-Type':f'multipart/form-data; boundary={boundary}'})
                r=c.getresponse(); data=r.read(); self.assertEqual(r.status,200,data[:200]);c.close()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                m=json.loads(z.read('manifest.json'))
                self.assertEqual(m['source'],'repomix_remote')
                self.assertTrue(m['repository_identity_verified'])
        finally:
            server.shutdown();server.server_close()
