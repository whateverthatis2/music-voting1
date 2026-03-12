from http.server import BaseHTTPRequestHandler
from .utils import load_db, GENRES, html_template

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = load_db()
        votes = db['votes']
        
        # Підрахунок голосів
        scores = {g: {"1": 0, "2": 0, "3": 0, "total": 0} for g in GENRES}
        for v in votes:
            p = v['preferences']
            scores[p[0]]["1"] += 1; scores[p[0]]["total"] += 3
            scores[p[1]]["2"] += 1; scores[p[1]]["total"] += 2
            scores[p[2]]["3"] += 1; scores[p[2]]["total"] += 1
        
        ranking = sorted(scores.items(), key=lambda x: x[1]["total"], reverse=True)
        leaders = [g for g, d in scores.items() if d["total"] > 0]
        
        # Генерация рядків таблиці
        rows = "".join(
            f'<tr class="rank-{i+1}"><td>{i+1}</td><td><strong>{g}</strong></td>'
            f'<td>{d["1"]} ({d["1"]*3})</td><td>{d["2"]} ({d["2"]*2})</td>'
            f'<td>{d["3"]} ({d["3"]})</td><td><strong>{d["total"]}</strong></td></tr>'
            for i, (g, d) in enumerate(ranking) if d["total"] > 0
        )
        
        # Бюлетені
        bullets = "".join(
            f'<tr><td><code>{v["id"]}</code></td><td>{v["timestamp"][:19]}</td>'
            f'<td>{v["comparison"]}</td><td><code>{v["public_hash"][:16]}...</code></td></tr>'
            for v in votes
        )
        
        leaders_html = "".join(f'<span class="metric">{l}</span>' for l in leaders)
        
        content = f'''
        <h2>📊 Результати агрегування</h2>
        <p>Всього голосів: <strong>{len(votes)}</strong>/21</p>
        <div class="leaders"><h3>🎯 Ядро лідерів:</h3><p>{leaders_html}</p><p><em>Кількість: {len(leaders)} з 20</em></p></div>
        <h3>Ранжування (метод Борда):</h3>
        <table><thead><tr><th>Ранг</th><th>Жанр</th><th>🥇 1-ше (×3)</th><th>🥈 2-ге (×2)</th><th>🥉 3-є (×1)</th><th>Сума</th></tr></thead><tbody>{rows}</tbody></table>
        <h3>📋 Бюлетені:</h3>
        <table><thead><tr><th>ID</th><th>Час</th><th>Порівняння</th><th>Хеш</th></tr></thead><tbody>{bullets}</tbody></table>
        <div class="links"><a href="/">← Головна</a><a href="/protocol">Протокол →</a></div>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_template("Результати", content).encode('utf-8'))
