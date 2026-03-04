from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from .utils import load_db

# Хардкордний пароль (зміни на свій)
PROTOCOL_PASSWORD = "teacher2024"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Перевірка пароля
        query = parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
        provided = query.get('pass', [''])[0]
        
        if provided != PROTOCOL_PASSWORD:
            self._send_password_form()
            return
        
        # Якщо пароль правильний — показуємо протокол
        db = load_db()
        votes = db['votes']
        
        if not db.get('ok'):
            self._send_error("Помилка бази даних")
            return
        
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
        .logout {{
            float: right;
            color: #ed8936;
            text-decoration: none;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>
            🔐 ПРОТОКОЛ ГОЛОСУВАННЯ
            <a href="/protocol" class="logout">[Вийти]</a>
        </h1>
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
    
    def do_POST(self):
        # Обробка форми пароля
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        provided = params.get('password', [''])[0]
        
        if provided == PROTOCOL_PASSWORD:
            # Перенаправляємо з паролем в URL
            self.send_response(302)
            self.send_header('Location', f'/protocol?pass={PROTOCOL_PASSWORD}')
            self.end_headers()
        else:
            # Неправильний пароль
            self._send_password_form(error="Неправильний пароль!")
    
    def _send_password_form(self, error=""):
        error_html = f'<p style="color: #e53e3e;">{error}</p>' if error else ""
        
        html = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Доступ до протоколу</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .box {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        h2 { color: #2d3748; margin-bottom: 20px; }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #5a67d8;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
        .hint {
            margin-top: 20px;
            font-size: 0.8em;
            color: #718096;
        }
    </style>
</head>
<body>
    <div class="box">
        <h2>🔐 Доступ до протоколу</h2>
        <p>Введіть пароль для перегляду</p>
        """ + error_html + """
        <form method="POST" action="/protocol">
            <input type="password" name="password" placeholder="Пароль" required autofocus>
            <button type="submit">Увійти</button>
        </form>
        <p class="hint">Для викладача</p>
    </div>
</body>
</html>"""
        
        self.send_response(401 if error else 200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _send_error(self, msg):
        html = f"""<!DOCTYPE html>
<html><body style="font-family: sans-serif; padding: 40px;">
<h1>Помилка</h1><p>{msg}</p><a href="/">← Назад</a>
</body></html>"""
        self.send_response(500)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
