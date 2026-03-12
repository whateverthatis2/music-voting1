from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import load_db, save_vote, generate_hash, STUDENT_IDS, GENRES
import secrets

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        student_id = data.get('student_id')
        p1, p2, p3 = data.get('p1'), data.get('p2'), data.get('p3')
        
        if student_id not in STUDENT_IDS:
            resp = {"error": "Невірний ID"}
        elif len(set([p1, p2, p3])) != 3:
            resp = {"error": "Жанри мають бути різними"}
        elif not all(g in GENRES for g in [p1, p2, p3]):
            resp = {"error": "Невірний жанр"}
        else:
            db = load_db()
            if student_id in db['voted_ids']:
                resp = {"error": "Цей ID вже голосував"}
            else:
                vote = {
                    "id": student_id,
                    "timestamp": datetime.now().isoformat(),
                    "preferences": [p1, p2, p3],
                    "comparison": f"{p1} ≻ {p2} ≻ {p3}",
                    "public_hash": secrets.token_hex(16)
                }
                vote["private_hash"] = generate_hash({"id": student_id, "preferences": [p1, p2, p3], "timestamp": vote["timestamp"]})
                resp = {"success": True, "private_hash": vote["private_hash"], "public_hash": vote["public_hash"]} if save_vote(vote) else {"error": "Помилка збереження"}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode('utf-8'))
