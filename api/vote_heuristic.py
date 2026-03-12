from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import HEURISTICS, get_db

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        h1, h2 = data.get('h1'), data.get('h2')
        
        valid_ids = [h['id'] for h in HEURISTICS]
        if h1 not in valid_ids or h2 not in valid_ids:
            return self._json({"error": "Невірна евристика"})
        if h1 == h2:
            return self._json({"error": "Оберіть різні евристики"})
        
        try:
            db = get_db()
            num = db.heuristic_votes.count_documents({}) + 1
            db.heuristic_votes.insert_one({"num": num, "h1": h1, "h2": h2, "time": datetime.now().isoformat()})
            self._json({"success": True, "vote_num": num})
        except Exception as e:
            self._json({"error": f"Помилка БД: {str(e)}"})
    
    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
