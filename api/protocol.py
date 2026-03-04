from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from .utils import load_db
import secrets
import time

# Хардкордний пароль (зміни на свій)
PROTOCOL_PASSWORD = "0000"

# Активні сесії (в пам'яті — при перезапуску сервера скидаються)
active_sessions = {}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Перевірка сесії по cookie
        session_id = self._get_cookie("session")
        
        if session_id and session_id in active_sessions:
            # Перевірка чи не застаріла сесія (1 година)
            if time.time() - active_sessions[session_id] < 3600:
                self._show_protocol()
                return
            else:
                del active_sessions[session_id]
        
        # Немає сесії — показуємо форму пароля
        self._send_password_form()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)
        
        provided = params.get('password', [''])[0]
        
        if provided == PROTOCOL_PASSWORD:
            # Створюємо сесію
            session_id = secrets.token_hex(16)
            active_sessions[session_id] = time.time()
            
            # Перенаправляємо з встановленням cookie
            self.send_response(302)
            self.send_header('Location', '/protocol')
            self.send_header('Set-Cookie', f'session={session_id}; HttpOnly; Path=/; Max-Age=3600')
            self.end_headers()
        else:
            self._send_password_form(error="Неправильний пароль!")
    
    def _get_cookie(self, name):
        """Отримання значення cookie"""
        cookie_header = self.headers.get('Cookie', '')
        cookies = {}
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value
        return cookies.get(name)
    
    def _show_protocol(self):
        """Показати протокол (тільки з валідною сесією)"""
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
            <a href="/protocol/logout" class="logout">[Вийти]</a>
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
    
    def _send_password_form(self, error=""):
        """Форма введення пароля"""
        error_html = f'<p style="color: #e53e3e; font-weight: bold;">{error}</p>' if error else ""
        
        html = """<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Доступ заборонено</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #1a202c;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        .box {
            background: #2d3748;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 400px;
            text-align: center;
            border: 2px solid #4a5568;
        }
        h2 { color: #fff; margin-bottom: 10px; }
        p { color: #a0aec0; margin-bottom: 20px; }
        input {
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            border: 2px solid #4a5568;
            border-radius: 8px;
            font-size: 16px;
            background: #1a202c;
            color: #fff;
            box-sizing: border-box;
        }
        input:focus {
            outline: none;
            border-color: #5a67d8;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover {
            opacity: 0.9;
        }
        .lock {
            font-size: 48px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="box">
        <div class="lock">🔒</div>
        <h2>Доступ до протоколу</h2>
        <p>Введіть пароль викладача</p>
        """ + error_html + """
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
    
    def _send_error(self, msg):
        """Сторінка помилки"""
        html = f"""<!DOCTYPE html>
<html><body style="font-family: sans-serif; padding: 40px; background: #1a202c; color: #fff;">
<h1>⚠️ Помилка</h1><p style="color: #e53e3e;">{msg}</p><a href="/" style="color: #63b3ed;">← Назад</a>
</body></html>"""
        self.send_response(500)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

