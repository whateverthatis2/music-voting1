from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .utils import html, get_db, OBJECTS
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/': self.main()
        elif path == '/lab3/matrix': self.matrix()
        elif path == '/lab3/brute': self.brute()
        elif path == '/lab3/ga': self.ga()
        else: self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/lab3/add': self.add_vote()
        else: self.send_error(404)
    
    def main(self):
        content = '''
        <div class="info">Лабораторна №3: Колективне ранжування</div>
        <p><a href="/lab3/add" style="background:#48bb78;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin:5px">➕ Додати голос</a></p>
        <p><a href="/lab3/matrix" style="background:#5a67d8;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin:5px">📋 Матриця переваг</a></p>
        <p><a href="/lab3/brute" style="background:#ed8936;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin:5px">🔄 Прямий перебір</a></p>
        <p><a href="/lab3/ga" style="background:#9f7aea;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block;margin:5px">🧬 Генетичний алгоритм</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Лаб №3", content).encode('utf-8'))
    
    def add_form(self):
        objects_json = json.dumps(OBJECTS, ensure_ascii=False)
        content = f'''
        <div class="info">Додати експертне ранжування</div>
        <form method="POST" action="/lab3/add">
            <div id="ranking" style="display:flex;flex-direction:column;gap:10px;margin:20px 0">
                {"".join([f'<div class="rank-item" data-idx="{i}"><span class="rank-num">{i+1}.</span><span class="obj-name">{obj}</span><button type="button" onclick="moveUp({i})" {"" if i==0 else ""}>↑</button><button type="button" onclick="moveDown({i})" {"" if i==len(OBJECTS)-1 else ""}>↓</button></div>' for i, obj in enumerate(OBJECTS)])}
            </div>
            <input type="hidden" name="ranking" id="rankingInput" value='{objects_json}'>
            <button type="submit" style="background:#5a67d8;color:white;padding:12px 30px;border:none;border-radius:6px;cursor:pointer;font-size:16px">Зберегти</button>
        </form>
        <p><a href="/">← Назад</a></p>
        <style>
        .rank-item{{display:flex;align-items:center;gap:15px;padding:12px;background:#f7fafc;border:2px solid #e2e8f0;border-radius:6px}}
        .rank-num{{font-weight:bold;color:#5a67d8;min-width:30px}}
        .obj-name{{flex-grow:1;font-weight:500}}
        .rank-item button{{background:#5a67d8;color:white;border:none;padding:5px 10px;border-radius:4px;cursor:pointer;font-size:18px}}
        .rank-item button:disabled{{background:#cbd5e0;cursor:not-allowed}}
        </style>
        <script>
        function moveUp(idx) {{
            const items = document.querySelectorAll('.rank-item');
            if (idx > 0) {{
                items[idx].parentNode.insertBefore(items[idx], items[idx-1]);
                updateNumbers();
            }}
        }}
        function moveDown(idx) {{
            const items = document.querySelectorAll('.rank-item');
            if (idx < items.length - 1) {{
                items[idx].parentNode.insertBefore(items[idx+1], items[idx]);
                updateNumbers();
            }}
        }}
        function updateNumbers() {{
            const items = document.querySelectorAll('.rank-item');
            const order = [];
            items.forEach((item, i) => {{
                item.querySelector('.rank-num').textContent = (i+1) + '.';
                order.push(item.querySelector('.obj-name').textContent);
            }});
            document.getElementById('rankingInput').value = JSON.stringify(order);
        }}
        </script>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Додати голос", content).encode('utf-8'))
    
    def add_vote(self):
        try:
            # Читаємо дані з форми
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            ranking_str = params.get('ranking', [''])[0]
            ranking = json.loads(ranking_str)
            
            # Зберігаємо в БД
            db = get_db()
            count = db.votes.count_documents({})
            db.votes.insert_one({
                "num": count + 1,
                "preferences": ranking,
                "time": datetime.now().isoformat()
            })
            
            content = f'''
            <div class="info" style="background:#c6f6d5;border-color:#48bb78">
            ✅ Збережено! Всього голосів: {count + 1}
            </div>
            <p><a href="/lab3/add">→ Додати ще</a> | <a href="/lab3/matrix">→ Матриця</a> | <a href="/">← На головну</a></p>
            '''
        except Exception as e:
            content = f'<div class="info" style="background:#fed7d7;border-color:#e53e3e">❌ Помилка: {str(e)}</div><p><a href="/lab3/add">← Назад</a></p>'
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Результат", content).encode('utf-8'))
    
    def matrix(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
        except Exception as e:
            votes = []
            print(f"Error: {e}")
        
        matrix = {}
        for g1 in OBJECTS:
            for g2 in OBJECTS:
                if g1 != g2: matrix[(g1,g2)] = 0
        
        for v in votes:
            prefs = v.get('preferences', [])
            for i in range(len(prefs)):
                for j in range(i+1, len(prefs)):
                    a, b = prefs[i], prefs[j]
                    if a in OBJECTS and b in OBJECTS:
                        matrix[(a,b)] = matrix.get((a,b), 0) + 1
        
        rows = ""
        for g1 in OBJECTS:
            row = f"<tr><td><b>{g1}</b></td>"
            for g2 in OBJECTS:
                if g1 == g2: row += "<td>-</td>"
                else:
                    c = matrix.get((g1,g2), 0)
                    bg = "#c6f6d5" if c > len(votes)/2 else "#fed7d7"
                    row += f"<td style='background:{bg};text-align:center'>{c}</td>"
            row += "</tr>"; rows += row
        
        content = f'''
        <div class="info">Матриця попарних переваг<br>Всього голосів: <strong>{len(votes)}</strong></div>
        <table><thead><tr><th>A vs B</th>{"".join([f"<th>{g}</th>" for g in OBJECTS])}</tr></thead><tbody>{rows}</tbody></table>
        <p><a href="/">← Назад</a> | <a href="/lab3/add">→ Додати голос</a> | <a href="/lab3/brute">→ Прямий перебір</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Матриця", content).encode('utf-8'))
    
    def brute(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
        except:
            votes = []
        
        n = len(OBJECTS)
        from math import factorial
        perms = factorial(n)
        
        scores = {g: 0 for g in OBJECTS}
        for v in votes:
            prefs = v.get('preferences', [])
            for i, g in enumerate(prefs):
                if g in OBJECTS: scores[g] += (n - i)
        
        borda = [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        
        content = f'''
        <div class="info">Об'єктів: {n}<br>Перестановок (n!): {perms:,}<br>Голосів в БД: <strong>{len(votes)}</strong></div>
        <h3>Результат (метод Борда):</h3>
        <ol>{"".join([f"<li>{g}</li>" for g in borda])}</ol>
        <p><a href="/">← Назад</a> | <a href="/lab3/add">→ Додати голос</a> | <a href="/lab3/ga">→ ГА</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Прямий перебір", content).encode('utf-8'))
    
    def ga(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
        except:
            votes = []
        
        if len(votes) < 3:
            content = f'''
            <div class="info" style="background:#fed7d7;border-color:#e53e3e">
            ⚠️ Недостатньо даних<br>Потрібно мінімум 3 голоси (зараз {len(votes)}).<br>
            <a href="/lab3/add" style="background:#48bb78;color:white;padding:8px 16px;border-radius:4px;text-decoration:none">→ Додати голоси</a>
            </div>
            <p><a href="/">← Назад</a></p>
            '''
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html("ГА", content).encode('utf-8'))
            return
        
        import random
        POP_SIZE, GENERATIONS, MUT_RATE = 20, 50, 0.3
        
        def fitness(ind):
            total = 0
            for v in votes:
                prefs = v.get('preferences', [])
                for i, obj in enumerate(ind):
                    if obj in prefs: total += abs(i - prefs.index(obj))
            return -total
        
        pop = [OBJECTS.copy() for _ in range(POP_SIZE)]
        for p in pop: random.shuffle(p)
        
        for _ in range(GENERATIONS):
            fits = [fitness(p) for p in pop]
            best = pop[fits.index(max(fits))].copy()
            new_pop = [best]
            while len(new_pop) < POP_SIZE:
                c1, c2 = random.sample(range(POP_SIZE), 2)
                parent = pop[c1 if fits[c1] > fits[c2] else c2].copy()
                if random.random() < MUT_RATE:
                    i, j = random.sample(range(len(parent)), 2)
                    parent[i], parent[j] = parent[j], parent[i]
                new_pop.append(parent)
            pop = new_pop
        
        ga_result = pop[0]
        
        scores = {g: 0 for g in OBJECTS}
        for v in votes:
            prefs = v.get('preferences', [])
            for i, g in enumerate(prefs):
                if g in OBJECTS: scores[g] += (len(OBJECTS) - i)
        borda = [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        
        comp = "".join([f"<tr><td>{i+1}</td><td>{ga}</td><td>{bo}</td><td>{'✅' if ga==bo else '❌'}</td></tr>" for i,(ga,bo) in enumerate(zip(ga_result, borda))])
        
        content = f'''
        <div class="info">Параметри ГА:<br>Популяція: {POP_SIZE} | Поколінь: {GENERATIONS} | Голосів: <strong>{len(votes)}</strong></div>
        <h3>Результат ГА:</h3>
        <ol>{"".join([f"<li>{g}</li>" for g in ga_result])}</ol>
        <h3>Порівняння з методом Борда:</h3>
        <table><thead><tr><th>Ранг</th><th>ГА</th><th>Борда</th><th>Збіг</th></tr></thead><tbody>{comp}</tbody></table>
        <p><a href="/">← Назад</a> | <a href="/lab3/add">→ Додати голос</a> | <a href="/lab3/brute">← Прямий перебір</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Генетичний алгоритм", content).encode('utf-8'))
