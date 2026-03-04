from http.server import BaseHTTPRequestHandler
from .protocol import active_sessions

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Видаляємо сесію
        cookie_header = self.headers.get('Cookie', '')
        session_id = None
        
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                if key == 'session':
                    session_id = value
                    break
        
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]
        
        # Перенаправляємо на головну з очищенням cookie
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'session=; HttpOnly; Path=/; Max-Age=0')
        self.end_headers()
