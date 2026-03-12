from http.server import BaseHTTPRequestHandler
import json
from .utils import HEURISTICS, get_db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            db = get_db()
            votes = list(db.heuristic_votes.find({}, {'_id': 0}).sort("num", -1))
            counts = {h['id']: 0 for h in HEURISTICS}
            for v in votes:
                counts[v['h1']] += 1
                counts[v['h2']] += 1
            ranking = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        except:
            votes, ranking = [], []
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "votes": votes,
            "ranking": [{"id": k, "count": v} for k, v in ranking]
        }).encode('utf-8'))
