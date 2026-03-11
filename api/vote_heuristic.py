from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import HEURISTICS, get_db

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
        
        # Збереження в MongoDB
        try:
            db = get_db()
            collection = db.heuristic_votes
            
            # Номер голосу
            count = collection.count_documents({})
            vote_num = count + 1
            
            collection.insert_one({
                "num": vote_num,
                "h1": h1,
                "h2": h2,
                "time": datetime.now().isoformat()
            })
            
            self._send_json({"success": True, "vote_num": vote_num})
        except Exception as e:
            self._send_json({"error": f"Помилка БД: {str(e)}"})
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
