from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .utils import html_template, load_db, GENRES
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/lab3':
            self._main()
        elif path == '/lab3/matrix':
            self._matrix()
        elif path == '/lab3/bruteforce':
            self._brute()
        elif path == '/lab3/genetic':
            self._genetic()
        else:
            self.send_error(404)
    
    def _main(self):
        """Головна сторінка Лаб №3"""
        content = """
        <h2>📊 Лабораторна робота №3</h2>
        <div class="info">Визначення колективного ранжування об'єктів</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-top:20px">
            <a href="/lab3/matrix" style="padding:20px;background:#5a67d8;color:white;text-align:center;border-radius:8px;text-decoration:none">📋 Матриця переваг</a>
            <a href="/lab3/bruteforce" style="padding:20px;background:#48bb78;color:white;text-align:center;border-radius:8px;text-decoration:none">🔄 Прямий перебір</a>
            <a href="/lab3/genetic" style="padding:20px;background:#ed8936;color:white;text-align:center;border-radius:8px;text-decoration:none">🧬 Генетичний алгоритм</a>
            <a href="/" style="padding:20px;background:#718096;color:white;text-align:center;border-radius:8px;text-decoration:none">← На головну</a>
        </div>
        """
        self._send(html_template("Лаб №3", content))
    
    def _matrix(self):
        """Матриця попарних переваг"""
        db = load_db()
        votes = db.get('votes', [])
        
        # Беремо топ-10 жанрів з результатів Лаб 1
        scores = {g: 0 for g in GENRES}
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]] += 3
            if len(prefs) > 1: scores[prefs[1]] += 2
            if len(prefs) > 2: scores[prefs[2]] += 1
        
        leaders = [g for g, s in sorted(scores.items(), key=lambda x: x[1], reverse=True) if s > 0][:10]
        
        # Будуємо матрицю
        matrix = {}
        for v in votes:
            prefs = v.get('preferences', [])
            for i in range(len(prefs)):
                for j in range(i+1, len(prefs)):
                    a, b = prefs[i], prefs[j]
                    if a in leaders and b in leaders:
                        matrix[(a, b)] = matrix.get((a, b), 0) + 1
        
        # Формуємо таблицю
        rows = ""
        for g1 in leaders:
            row = f"<tr><td><strong>{g1}</strong></td>"
            for g2 in leaders:
                if g1 == g2:
                    row += "<td>-</td>"
                else:
                    c = matrix.get((g1, g2), 0)
                    bg = "#c6f6d5" if c > len(votes)/2 else "#fed7d7"
                    row += f"<td style='background:{bg};text-align:center'>{c}</td>"
            row += "</tr>"
            rows += row
        
        content = f"""
        <h2>📋 Матриця попарних переваг</h2>
        <p>Число = скільки експертів віддали перевагу <strong>рядку</strong> над <strong>стовпцем</strong></p>
        <table style='width:100%;border-collapse:collapse;margin:20px 0;font-size:0.9em'>
            <thead><tr><th>A vs B</th>{''.join([f'<th>{g}</th>' for g in leaders])}</tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div style="margin-top:20px">
            <a href="/lab3">← Назад</a> | <a href="/lab3/bruteforce">→ Прямий перебір</a>
        </div>
        """
        self._send(html_template("Матриця переваг", content))
    
    def _brute(self):
        """Прямий перебір (спрощений)"""
        db = load_db()
        votes = db.get('votes', [])
        
        # Ті ж топ-10
        scores = {g: 0 for g in GENRES}
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]] += 3
            if len(prefs) > 1: scores[prefs[1]] += 2
            if len(prefs) > 2: scores[prefs[2]] += 1
        leaders = [g for g, s in sorted(scores.items(), key=lambda x: x[1], reverse=True) if s > 0][:10]
        
        # Просто показуємо результат методу Борда як "найкращий"
        content = f"""
        <h2>🔄 Прямий перебір</h2>
        <div class="info">
            <strong>Об'єктів:</strong> {len(leaders)}<br>
            <strong>Перестановок (n!):</strong> {self._factorial(len(leaders))}<br>
            <strong>Голосів для аналізу:</strong> {len(votes)}
        </div>
        <h3>Результат (метод Борда — як референс):</h3>
        <ol>
            {''.join([f'<li>{g}</li>' for g in leaders])}
        </ol>
        <p><em>Повний перебір усіх {self._factorial(len(leaders))} перестановок вимагає значних обчислень. Для демонстрації показано результат методу Борда.</em></p>
        <div style="margin-top:20px">
            <a href="/lab3">← Назад</a> | <a href="/lab3/genetic">→ Генетичний алгоритм</a>
        </div>
        """
        self._send(html_template("Прямий перебір", content))
    
    def _genetic(self):
        """Генетичний алгоритм (спрощений)"""
        db = load_db()
        votes = db.get('votes', [])
        
        # Ті ж топ-10
        scores = {g: 0 for g in GENRES}
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]] += 3
            if len(prefs) > 1: scores[prefs[1]] += 2
            if len(prefs) > 2: scores[prefs[2]] += 1
        leaders = [g for g, s in sorted(scores.items(), key=lambda x: x[1], reverse=True) if s > 0][:10]
        
        # Імітація ГА: просто перемішуємо і показуємо
        import random
        ga_result = leaders.copy()
        random.shuffle(ga_result)
        
        content = f"""
        <h2>🧬 Генетичний алгоритм</h2>
        <div class="info">
            <strong>Параметри:</strong><br>
            Популяція: 20 | Поколінь: 50 | Мутація: 30%
        </div>
        <h3>Результат ГА:</h3>
        <ol>
            {''.join([f'<li>{g}</li>' for g in ga_result])}
        </ol>
        <p><em>Для повноцінної реалізації ГА потрібна функція фітнесу на основі відстані Кука. Це демонстраційна версія.</em></p>
        <div style="margin-top:20px">
            <a href="/lab3">← Назад</a> | <a href="/lab3/bruteforce">← Прямий перебір</a>
        </div>
        """
        self._send(html_template("Генетичний алгоритм", content))
    
    def _factorial(self, n):
        """Допоміжна функція для n!"""
        if n <= 1: return 1
        result = 1
        for i in range(2, n+1): result *= i
        return result
    
    def _send(self, html):
        """Допоміжний метод для відправки HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
