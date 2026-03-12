from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import get_db

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        ranking = post_data.get('ranking', [])
        
        if len(ranking) != 10:
            self._send_json({"error": "Потрібно 10 об'єктів"})
            return
        
        try:
            db = get_db()
            collection = db.rankings
            
            count = collection.count_documents({})
            
            collection.insert_one({
                "num": count + 1,
                "ranking": ranking,
                "time": datetime.now().isoformat()
            })
            
            self._send_json({"success": True, "count": count + 1})
        except Exception as e:
            self._send_json({"error": str(e)})
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
