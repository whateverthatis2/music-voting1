from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from .utils import load_db

# Хардкордний пароль
PROTOCOL_PASSWORD = "0000"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # GET — завжди показуємо форму (немає сесій!)
        self._send_password_form()
    
    def do_POST(self):
        # Читаємо POST дані
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        provided = params.get('password', [''])[0]
        
        if provided == PROTOCOL_PASSWORD:
            # Правильний пароль — показуємо протокол
            self._show_protocol()
        else:
            # Неправильний — форма з помилкою
            self._send_password_form(error="Неправильний пароль!")
    
    def _show_protocol(self):
        """Показати протокол"""
        db = load_db()
        votes = db.get('votes', [])
        
        entries = ""
        for v in votes:
            entries += f"""
            <div style="background: #2d3748; padding: 15px; margin: 10px 0; 
                        border-left: 3px solid #48bb78; font-family: monospace;">
                <div style="color: #a0aec0;">[{v.get('timestamp', 'N/A')}] ID: {v.get('id', 'N/A')}</div>
                <div>Порівняння: {v.get('comparison', 'N/A')}</div>
                <div style="color: #ed8936; word-break: break-all;">
                    Публічний: {v.get('public_hash', 'N/A')}<br>
                    Приватний: {v.get('private_hash', 'N/A')}
                </div>
            </div>"""
        
        db_status = "✅ OK" if db.get('ok') else f"⚠️ {db.get('error', 'Помилка')}"
        
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
        .back {{
            color: #a0aec0;
            text-decoration: none;
            font-size: 0.9em;
        }}
        .db-status {{
            background: {'#1a472a' if db.get('ok') else '#742a2a'};
            color: {'#48bb78' if db.get('ok') else '#fc8181'};
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-family: sans-serif;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            🔐 ПРОТОКОЛ ГОЛОСУВАННЯ
            <a href="/" class="back">[← Назад]</a>
        </h1>
        <div class="db-status">Статус БД: {db_status} | Записів: {len(votes)}</div>
        {entries}
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _send_password_form(self, error=""):
        """Форма введення пароля"""
        error_html = f'<p style="color: #fc8181; font-weight: bold; margin-bottom: 15px;">{error}</p>' if error else ""
        
        html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Доступ заборонено</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: #1a202c;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }}
        .box {{
            background: #2d3748;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
            text-align: center;
            border: 2px solid #4a5568;
        }}
        h2 {{ color: #fff; margin-bottom: 10px; }}
        p {{ color: #a0aec0; margin-bottom: 20px; }}
        input {{
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            border: 2px solid #4a5568;
            border-radius: 8px;
            font-size: 16px;
            background: #1a202c;
            color: #fff;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }}
        .lock {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="box">
        <div class="lock">🔒</div>
        <h2>Доступ до протоколу</h2>
        <p>Введіть пароль викладача</p>
        {error_html}
        <form method="POST" action="/protocol">
            <input type="password" name="password" placeholder="Пароль" required autofocus autocomplete="off">
            <button type="submit">Увійти</button>
        </form>
    </div>
</body>
</html>"""
        
        self.send_response(401 if error else 200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
