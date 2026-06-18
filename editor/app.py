import sys
import os
import json
import subprocess
import tempfile
import threading
import webbrowser
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

JJITLANG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'py'))
INTERPRETER = os.path.join(JJITLANG_DIR, 'jjitlang', 'interpreter.py')
PORT = 8080
TIMEOUT = 30

_running = {}
_lock = threading.Lock()
_next_id = 0

ENV = os.environ.copy()
ENV['PYTHONUNBUFFERED'] = '1'


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/' or path == '/index.html':
            self.serve_file(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), 'text/html; charset=utf-8')
        elif path.startswith('/stream/'):
            self._stream_output(path)
        elif path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/run':
            self._run_code()
        elif path.startswith('/stop/'):
            self._stop_job(path)
        else:
            self.send_response(404)
            self.end_headers()

    def _run_code(self):
        length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(length))
        code = body.get('code', '')
        stdin_data = body.get('stdin', '')

        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.jjit', delete=False, encoding='utf-8')
        tmp.write(code.strip())
        tmp.close()

        global _next_id
        with _lock:
            job_id = str(_next_id)
            _next_id += 1

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({'job_id': job_id}).encode('utf-8'))

        lines_buf = []
        with _lock:
            _running[job_id] = {'lines': lines_buf, 'proc': None, 'done': False, 'rc': None}

        def run():
            try:
                proc = subprocess.Popen(
                    [sys.executable, '-u', INTERPRETER, '--timeout', str(TIMEOUT), tmp.name],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    env=ENV,
                )
                with _lock:
                    _running[job_id]['proc'] = proc
            except Exception as e:
                with _lock:
                    _running[job_id]['lines'].append(f'[오류] {e}\n')
                    _running[job_id]['done'] = True
                    _running[job_id]['rc'] = -1
                try: os.unlink(tmp.name)
                except: pass
                return

            def reader(stream, label):
                for line in iter(stream.readline, ''):
                    text = line if label == 'stdout' else f'[STDERR] {line}'
                    with _lock:
                        _running[job_id]['lines'].append(text)
                    print(text, end='', flush=True)
                stream.close()

            t1 = threading.Thread(target=reader, args=(proc.stdout, 'stdout'), daemon=True)
            t2 = threading.Thread(target=reader, args=(proc.stderr, 'stderr'), daemon=True)
            t1.start()
            t2.start()

            if stdin_data:
                proc.stdin.write(stdin_data)
                proc.stdin.close()

            try:
                proc.wait(timeout=TIMEOUT + 5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
                with _lock:
                    _running[job_id]['lines'].append('\n[시간 초과 - 강제 종료]\n')
            t1.join()
            t2.join()

            with _lock:
                _running[job_id]['done'] = True
                _running[job_id]['rc'] = proc.returncode
            print(f'[찢랭] 종료 (코드 {proc.returncode})', flush=True)

            try: os.unlink(tmp.name)
            except: pass

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def _stream_output(self, path):
        job_id = path.split('/stream/', 1)[1]
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        sent = 0
        poll_count = 0
        while True:
            with _lock:
                entry = _running.get(job_id)
            if entry is None:
                poll_count += 1
                if poll_count > 6000:
                    data = json.dumps({'type': 'error', 'text': 'Timeout'})
                    self.wfile.write(f'data: {data}\n\n'.encode('utf-8'))
                    self.wfile.flush()
                    break
                time.sleep(0.05)
                continue

            lines = entry['lines']
            done = entry['done']
            rc = entry['rc']

            while sent < len(lines):
                data = json.dumps({'type': 'stdout', 'text': lines[sent]})
                self.wfile.write(f'data: {data}\n\n'.encode('utf-8'))
                sent += 1

            if done:
                data = json.dumps({'type': 'done', 'returncode': rc})
                self.wfile.write(f'data: {data}\n\n'.encode('utf-8'))
                self.wfile.flush()
                with _lock:
                    _running.pop(job_id, None)
                break

            self.wfile.flush()
            time.sleep(0.05)

    def _stop_job(self, path):
        job_id = path.split('/stop/', 1)[1]
        with _lock:
            entry = _running.get(job_id)
        if entry and isinstance(entry, dict) and entry.get('proc'):
            try:
                entry['proc'].kill()
                entry['proc'].wait(timeout=5)
            except:
                pass
            with _lock:
                entry['lines'].append('\n[강제 종료됨]\n')
                entry['done'] = True
                entry['rc'] = -1
            self._respond({'ok': True})
        else:
            self._respond({'ok': False, 'reason': 'not running'})

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
        print(f'[HTTP] {args[0] if args else ""}')


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
