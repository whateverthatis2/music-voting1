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
        
        rows = ""
        rank = 1
        for genre, data in ranking:
            if data['total'] > 0:
                css_class = f"rank-{rank}" if rank <= 3 else ""
                rows += f"""
                <tr class="{css_class}">
                    <td>{rank}</td>
                    <td><strong>{genre}</strong></td>
                    <td>{data['first']} ({data['first']*3})</td>
                    <td>{data['second']} ({data['second']*2})</td>
                    <td>{data['third']} ({data['third']})</td>
                    <td><strong>{data['total']}</strong></td>
                </tr>"""
                rank += 1
        
        bulletins = ""
        for v in votes:
            bulletins += f"""
            <tr>
                <td><code>{v['id']}</code></td>
                <td>{v['timestamp'][:19]}</td>
                <td>{v['comparison']}</td>
                <td><code>{v['public_hash'][:16]}...</code></td>
            </tr>"""
        
        leaders_html = ''.join([f'<span class="metric">{l}</span>' for l in leaders])
        
        content = f"""
        <h2>📊 Результати агрегування</h2>
        <p>Всього голосів: <strong>{len(votes)}</strong>/21</p>
        
        <div class="leaders">
            <h3>🎯 Ядро лідерів:</h3>
            <p>{leaders_html}</p>
            <p><em>Кількість: {len(leaders)} з 20</em></p>
        </div>
        
        <h3>Ранжування (метод Борда):</h3>
        <table>
            <thead>
                <tr>
                    <th>Ранг</th>
                    <th>Жанр</th>
                    <th>🥇 1-ше (×3)</th>
                    <th>🥈 2-ге (×2)</th>
                    <th>🥉 3-є (×1)</th>
                    <th>Сума</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        
        <h3>📋 Бюлетені:</h3>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Час</th>
                    <th>Порівняння</th>
                    <th>Хеш</th>
                </tr>
            </thead>
            <tbody>{bulletins}</tbody>
        </table>
        
        <div class="links">
            <a href="/">← Головна</a>
            <a href="/protocol">Протокол →</a>
        </div>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_template("Результати", content).encode('utf-8'))