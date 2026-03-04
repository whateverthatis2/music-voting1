from http.server import BaseHTTPRequestHandler
from .utils import load_db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db = load_db()
        votes = db['votes']
        
        entries = ""
        for v in votes:
            entries += f"""
            <div style="background: #2d3748; padding: 15px; margin: 10px 0; 
                        border-left: 3px solid #48bb78; font-family: monospace;">
                <div style="color: #a0aec0;">[{v['timestamp']}] ID: {v['id']}</div>
                <div>Порівняння: {v['comparison']}</div>
                <div style="color: #ed8936; word-break: break-all;">
                    Публічний: {v['public_hash']}<br>
                    Приватний: {v['private_hash']}
                </div>
            </div>"""
        
        html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Протокол</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background: #1a202c;
            color: #48bb78;
            padding: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #2d3748;
            padding: 30px;
            border-radius: 10px;
        }}
        h1 {{ color: #fff; border-bottom: 2px solid #48bb78; padding-bottom: 10px; }}
        a {{ color: #63b3ed; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 ПРОТОКОЛ ГОЛОСУВАННЯ</h1>
        <p>Записів: {len(votes)} | База даних: MongoDB Atlas</p>
        {entries}
        <p><a href="/">← Назад</a></p>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))