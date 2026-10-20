"""A minimal collector for Dead Letter's play telemetry.

The game POSTs batches as JSON text: {"sid", "build", "sent", "events": [...]}. This server appends each batch, with
the time it arrived, to data/YYYY-MM-DD.jsonl, one batch per line. It answers CORS so the game can be hosted anywhere.
Standard library only.

    python collector.py --port 8787 --data ./data
    # then open the game with ?telemetry=https://your-host:8787/events

Put it behind HTTPS (a reverse proxy, or a host's TLS) when the game is served over HTTPS; browsers block mixed content.
"""
import argparse
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 512 * 1024


class Handler(BaseHTTPRequestHandler):
    data_dir = 'data'

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0 or n > MAX_BODY:
            self.send_response(413 if n > MAX_BODY else 400)
            self._cors()
            self.end_headers()
            return
        try:
            batch = json.loads(self.rfile.read(n))
            assert isinstance(batch.get('events'), list) and isinstance(batch.get('sid'), str)
        except Exception:
            self.send_response(400)
            self._cors()
            self.end_headers()
            return
        batch['received'] = time.time()
        os.makedirs(self.data_dir, exist_ok=True)
        with open(os.path.join(self.data_dir, time.strftime('%Y-%m-%d') + '.jsonl'), 'a') as f:
            f.write(json.dumps(batch, separators=(',', ':')) + '\n')
        self.send_response(204)
        self._cors()
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8787)
    ap.add_argument('--data', default='data')
    a = ap.parse_args()
    Handler.data_dir = a.data
    print(f'collecting on :{a.port} into {a.data}/')
    ThreadingHTTPServer(('', a.port), Handler).serve_forever()
