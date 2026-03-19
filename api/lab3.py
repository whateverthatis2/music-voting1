from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json, traceback, os

# Проста версія без MongoDB спочатку — щоб перевірити чи працює маршрут
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            path = urlparse(self.path).path
            
            if path == '/lab3':
                self._main()
            elif path == '/lab3/matrix':
                self._send("Матриця", "<p>Тут буде матриця переваг</p>")
            elif path == '/lab3/bruteforce':
                self._send("Прямий перебір", "<p>Тут буде перебір</p>")
            elif path == '/lab3/genetic':
                self._send("ГА", "<p>Тут буде генетичний алгоритм</p>")
            else:
                self.send_error(404)
        except Exception as e:
            # Показуємо реальну помилку в браузері
            self._send("Помилка", f"<pre>{traceback.format_exc()}</pre>")
    
    def _main(self):
        content = """
        <h2>📊 Лабораторна робота №3</h2>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-top:20px">
            <a href="/lab3/matrix" style="padding:20px;background:#5a67d8;color:white;text-align:center;border-radius:8px;text-decoration:none">📋 Матриця</a>
            <a href="/lab3/bruteforce" style="padding:20px;background:#48bb78;color:white;text-align:center;border-radius:8px;text-decoration:none">🔄 Перебір</a>
            <a href="/lab3/genetic" style="padding:20px;background:#ed8936;color:white;text-align:center;border-radius:8px;text-decoration:none">🧬 ГА</a>
            <a href="/" style="padding:20px;background:#718096;color:white;text-align:center;border-radius:8px;text-decoration:none">← Назад</a>
        </div>
        """
        self._send("Лаб №3", content)
    
    def _send(self, title, content):
        html = f"<!DOCTYPE html><html><head><title>{title}</title><style>body{{font-family:sans-serif;max-width:800px;margin:20px auto}}a{{color:#5a67d8}}</style></head><body><h1>{title}</h1>{content}</body></html>"
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
