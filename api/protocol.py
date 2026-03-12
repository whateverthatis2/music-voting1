from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .utils import load_db, html_template

PASSWORD = "0000"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if query.get('pass', [''])[0] != PASSWORD:
            self._show_login()
            return
        
        db = load_db()
        votes = db.get('votes', [])
        entries = "".join([f"<div style='background:#1a202c;color:#48bb78;padding:10px;margin:5px 0;font-family:monospace'>[{v['timestamp']}] {v['id']}: {v['comparison']}<br>Hash: {v['public_hash']}</div>" for v in votes])
        
        content = f"<p>Записів: {len(votes)}</p>{entries}<p><a href='/'>← Назад</a></p>"
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_template("Протокол", content).encode('utf-8'))

    def _show_login(self):
        content = """
        <form method="GET"><input type="password" name="pass" placeholder="Пароль" style="padding:10px"><button type="submit">Увійти</button></form>
        <p><a href="/">← Назад</a></p>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_template("Доступ заборонено", content).encode('utf-8'))
