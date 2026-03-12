from http.server import BaseHTTPRequestHandler
from .utils import load_db
from urllib.parse import parse_qs, urlparse

PROTOCOL_PASSWORD = "0000"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        if query.get('pass', [''])[0] != PROTOCOL_PASSWORD:
            self._show_login()
            return
        
        db = load_db()
        votes = db['votes']
        
        # Протокол з хешами
        entries = ""
        for v in votes:
            entries += f"""
            <div class="entry">
                <div class="timestamp">[{v['timestamp']}] ID: {v['id']}</div>
                <div>{v['comparison']}</div>
                <div class="hash">Публічний: {v['public_hash']}<br>Приватний: {v['private_hash']}</div>
            </div>"""
        
        html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Протокол</title>
    <style>
        body {{ font-family: 'Courier New', monospace; background: #1a202c; color: #48bb78; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: #2d3748; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #fff; border-bottom: 2px solid #48bb78; }}
        .entry {{ background: #1a202c; padding: 15px; margin: 10px 0; border-left: 3px solid #48bb78; }}
        .timestamp {{ color: #a0aec0; }}
        .hash {{ color: #ed8936; word-break: break-all; }}
        a {{ color: #63b3ed; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 ПРОТОКОЛ ГОЛОСУВАННЯ</h1>
        <p>Записів: {len(votes)}</p>
        {entries}
        <p><a href="/">← Назад</a></p>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _show_login(self):
        # Форма введення пароля
        html = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Доступ заборонено</title>
    <style>
        body {{ font-family: sans-serif; background: #1a202c; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
        .box {{ background: #2d3748; padding: 40px; border-radius: 15px; text-align: center; }}
        h2 {{ color: #fff; }}
        input {{ width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 2px solid #4a5568; background: #1a202c; color: #fff; }}
        button {{ width: 100%; padding: 14px; background: #5a67d8; color: white; border: none; border-radius: 8px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="box">
        <h2>🔒 Доступ до протоколу</h2>
        <form method="GET" action="/protocol">
            <input type="password" name="pass" placeholder="Пароль" required autofocus>
            <button type="submit">Увійти</button>
        </form>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
