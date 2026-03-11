from http.server import BaseHTTPRequestHandler
from .vote_heuristic import heuristic_votes
from .utils import HEURISTICS

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Забороняємо кешування
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        
        # Підрахунок
        counts = {h['id']: 0 for h in HEURISTICS}
        for v in heuristic_votes:
            counts[v['h1']] += 1
            counts[v['h2']] += 1
        
        ranking = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Протокол евристик</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: sans-serif; background: #f5f5f5; padding: 20px; max-width: 800px; margin: 0 auto; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #5a67d8; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #5a67d8; color: white; }}
        .ranking {{ background: #e6fffa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
        .rank-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #b2f5ea; }}
        a {{ color: #5a67d8; }}
        .refresh {{ color: #666; font-size: 0.9em; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 Протокол голосування за евристики</h1>
        <a href="/">← На головну</a>
        
        <div class="ranking">
            <h3>🏆 Рейтинг евристик (оновлюється автоматично)</h3>
            {''.join([f'<div class="rank-item"><span>{k}</span><strong>{v} голосів</strong></div>' for k, v in ranking])}
        </div>
        
        <h3>🗳️ Всі голоси ({len(heuristic_votes)})</h3>
        <table>
            <thead>
                <tr><th>№</th><th>Пріоритет 1</th><th>Пріоритет 2</th><th>Час</th></tr>
            </thead>
            <tbody>
                {''.join([f'<tr><td>{v["num"]}</td><td><strong>{v["h1"]}</strong></td><td><strong>{v["h2"]}</strong></td><td>{v["time"][:19]}</td></tr>' for v in reversed(heuristic_votes)])}
            </tbody>
        </table>
        
        <p class="refresh">Сторінка оновлюється кожні 5 секунд</p>
    </div>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
