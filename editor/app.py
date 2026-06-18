import sys
import os
import json
import subprocess
import tempfile
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

JJITLANG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'py'))
INTERPRETER = os.path.join(JJITLANG_DIR, 'jjitlang', 'interpreter.py')
PORT = 8080

_START = '야, 이 씨발련아'
_END = '니 친정 엄마, 씹구멍 찢으면 좋겠니'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/' or path == '/index.html':
            self.serve_file(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), 'text/html; charset=utf-8')
        elif path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path == '/run':
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            code = body.get('code', '')
            stdin_data = body.get('stdin', '')

            stripped = code.strip()
            if not stripped.startswith(_START):
                self._respond({'stdout': '', 'stderr': '찢랭 코드는 "' + _START + '"로 시작해야 합니다', 'returncode': -1})
                return
            if not stripped.endswith(_END):
                self._respond({'stdout': '', 'stderr': '찢랭 코드는 "' + _END + '"로 끝나야 합니다', 'returncode': -1})
                return

            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.jjit', delete=False, encoding='utf-8')
            tmp.write(stripped)
            tmp.close()

            try:
                proc = subprocess.run(
                    [sys.executable, INTERPRETER, tmp.name],
                    input=stdin_data,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                result = {
                    'stdout': proc.stdout,
                    'stderr': proc.stderr,
                    'returncode': proc.returncode,
                }
            except subprocess.TimeoutExpired:
                result = {'stdout': '', 'stderr': 'Timeout (30s)', 'returncode': -1}
            except Exception as e:
                result = {'stdout': '', 'stderr': str(e), 'returncode': -1}
            finally:
                os.unlink(tmp.name)
            self._respond(result)
        else:
            self.send_response(404)
            self.end_headers()

    def _respond(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def serve_file(self, filepath, content_type):
        try:
            with open(filepath, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    print(f'찢랭 에디터: http://localhost:{PORT}')
    webbrowser.open(f'http://localhost:{PORT}')
    server = HTTPServer(('', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n종료')
        server.server_close()


if __name__ == '__main__':
    main()
