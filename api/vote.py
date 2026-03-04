from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
from .utils import load_db, save_vote, generate_hash, STUDENT_IDS, GENRES
import secrets

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        student_id = data.get('student_id')
        p1, p2, p3 = data.get('p1'), data.get('p2'), data.get('p3')
        
        response = {}
        
        if student_id not in STUDENT_IDS:
            response = {"error": "Невірний ID"}
        elif len(set([p1, p2, p3])) != 3:
            response = {"error": "Жанри мають бути різними"}
        elif not all(g in GENRES for g in [p1, p2, p3]):
            response = {"error": "Невірний жанр"}
        else:
            db = load_db()
            if student_id in db['voted_ids']:
                response = {"error": "Цей ID вже голосував"}
            else:
                vote_record = {
                    "id": student_id,
                    "timestamp": datetime.now().isoformat(),
                    "preferences": [p1, p2, p3],
                    "comparison": f"{p1} ≻ {p2} ≻ {p3}",
                    "public_hash": secrets.token_hex(16)
                }
                
                private_data = {
                    "id": student_id,
                    "preferences": [p1, p2, p3],
                    "timestamp": vote_record["timestamp"]
                }
                vote_record["private_hash"] = generate_hash(private_data)
                
                if save_vote(vote_record):
                    response = {
                        "success": True,
                        "private_hash": vote_record["private_hash"],
                        "public_hash": vote_record["public_hash"]
                    }
                else:
                    response = {"error": "Помилка збереження (можливо, ID вже голосував)"}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))