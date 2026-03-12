from http.server import BaseHTTPRequestHandler
import json
from .utils import get_db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            db = get_db()
            count = db.rankings.count_documents({})
            self._send_json({"count": count})
        except:
            self._send_json({"count": 0})
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
