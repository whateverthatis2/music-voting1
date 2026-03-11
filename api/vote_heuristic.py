from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import HEURISTICS

heuristic_votes = []

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        h1, h2 = post_data.get('h1'), post_data.get('h2')
        
        # Валідація
        valid_ids = [h['id'] for h in HEURISTICS]
        if h1 not in valid_ids or h2 not in valid_ids:
            self._send_json({"error": "Невірна евристика"})
            return
        
        if h1 == h2:
            self._send_json({"error": "Оберіть різні евристики"})
            return
        
        # Збереження (без ID, просто порядковий номер)
        vote_num = len(heuristic_votes) + 1
        heuristic_votes.append({
            "num": vote_num,
            "h1": h1,
            "h2": h2,
            "time": datetime.now().isoformat()
        })
        
        self._send_json({"success": True, "vote_num": vote_num})
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
