from http.server import BaseHTTPRequestHandler
import json
from .vote_heuristic import heuristic_votes, voted_experts
from .utils import HEURISTICS

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Підрахунок популярності
        counts = {}
        for h in HEURISTICS:
            counts[h['id']] = 0
        
        for v in heuristic_votes:
            counts[v['h1']] = counts.get(v['h1'], 0) + 1
            counts[v['h2']] = counts.get(v['h2'], 0) + 1
        
        # Сортування за популярністю
        ranking = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "votes": heuristic_votes,
            "total_voted": len(voted_experts),
            "ranking": [{"id": k, "count": v} for k, v in ranking]
        }).encode('utf-8'))
