from http.server import BaseHTTPRequestHandler
from .utils import html, load_votes, GENRES

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = load_votes()
        votes = db.get('votes', [])
        
        scores = {g: {"first":0, "second":0, "third":0, "total":0} for g in GENRES}
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]]['first'] += 1; scores[prefs[0]]['total'] += 3
            if len(prefs) > 1: scores[prefs[1]]['second'] += 1; scores[prefs[1]]['total'] += 2
            if len(prefs) > 2: scores[prefs[2]]['third'] += 1; scores[prefs[2]]['total'] += 1
        
        ranking = sorted(scores.items(), key=lambda x: x[1]['total'], reverse=True)
        leaders = [g for g, d in scores.items() if d['total'] > 0]
        
        rows = ""
        for i, (g, d) in enumerate(ranking):
            if d['total'] > 0:
                rows += f"<tr><td>{i+1}</td><td>{g}</td><td>{d['first']}</td><td>{d['second']}</td><td>{d['third']}</td><td>{d['total']}</td></tr>"
        
        content = f"""
        <p>Всього голосів: <b>{len(votes)}</b></p>
        <div class="info">Ядро лідерів ({len(leaders)}): {', '.join(leaders)}</div>
        <table><thead><tr><th>Ранг</th><th>Жанр</th><th>1-ше</th><th>2-ге</th><th>3-є</th><th>Сума</th></tr></thead><tbody>{rows}</tbody></table>
        <div style="margin-top:20px">
            <a href="/">← Лаб 2 (Евристики)</a> | <a href="/protocol">Протокол Лаб 1</a> | <a href="/rankings">Ранжування 10 + ГА</a>
        </div>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Результати Лаб 1", content).encode('utf-8'))
