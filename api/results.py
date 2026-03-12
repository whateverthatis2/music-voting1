from http.server import BaseHTTPRequestHandler
from .utils import load_db, GENRES, html_template

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = load_db()
        votes = db['votes']
        
        scores = {genre: {"first": 0, "second": 0, "third": 0, "total": 0} 
                  for genre in GENRES}
        
        for vote in votes:
            prefs = vote['preferences']
            scores[prefs[0]]['first'] += 1
            scores[prefs[0]]['total'] += 3
            scores[prefs[1]]['second'] += 1
            scores[prefs[1]]['total'] += 2
            scores[prefs[2]]['third'] += 1
            scores[prefs[2]]['total'] += 1
        
        ranking = sorted(scores.items(), key=lambda x: x[1]['total'], reverse=True)
        leaders = [g for g, d in scores.items() if d['total'] > 0]
        
        # ... (решта коду без змін)
        # Таблиця ранжування + бюлетені як у попередній версії
        
        content = f"""
        <h2>📊 Результати Лаб №1</h2>
        <p>Всього голосів: <strong>{len(votes)}</strong></p>
        
        <div class="leaders">
            <h3>🎯 Ядро лідерів ({len(leaders)} жанрів)</h3>
            <p>{', '.join(leaders)}</p>
        </div>
        
        <h3>Ранжування (метод Борда)</h3>
        <table>...</table>
        
        <div class="links">
            <a href="/">← Лаб №2 (евристики)</a>
            <a href="/rankings">🎯 Ранжування 10 об'єктів</a>
        </div>
        """
        
        html = html_template("Результати Лаб №1", content)
        self.wfile.write(html.encode('utf-8'))
