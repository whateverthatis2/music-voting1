from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import STUDENT_IDS, HEURISTICS

# Сховище в пам'яті
heuristic_votes = []
voted_experts = set()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        expert_id = post_data.get('expert_id')
        h1, h2 = post_data.get('h1'), post_data.get('h2')
        
        # Валідація
        if expert_id not in STUDENT_IDS:
            self._send_json({"error": "Невірний ID"})
            return
        
        if expert_id in voted_experts:
            self._send_json({"error": "Ви вже голосували"})
            return
        
        valid_ids = [h['id'] for h in HEURISTICS]
        if h1 not in valid_ids or h2 not in valid_ids:
            self._send_json({"error": "Невірна евристика"})
            return
        
        if h1 == h2:
            self._send_json({"error": "Оберіть різні евристики"})
            return
        
        # Збереження
        heuristic_votes.append({
            "expert": expert_id,
            "h1": h1,
            "h2": h2,
            "time": datetime.now().isoformat()
        })
        voted_experts.add(expert_id)
        
        self._send_json({"success": True})
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
