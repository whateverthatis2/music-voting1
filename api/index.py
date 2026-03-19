from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .utils import html, get_db, OBJECTS
from itertools import permutations
from math import factorial
import json
import random

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/': self.main()
        elif path == '/matrix': self.matrix()
        elif path == '/brute': self.brute()
        elif path == '/ga': self.ga()
        elif path == '/lab3/add': self.add_form()  # НОВА СТОРІНКА
        else: self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/lab3/add': self.add_vote()  # НОВИЙ POST
        else: self.send_error(404)
    
    def main(self):
        content = '''
        <div class="info">Лабораторна №3: Колективне ранжування</div>
        <p><a href="/lab3/add" style="background:#48bb78;color:white;padding:10px 20px;border-radius:6px;text-decoration:none">➕ Додати голос</a></p>
        <p><a href="/matrix">📋 Матриця переваг</a></p>
        <p><a href="/brute">🔄 Прямий перебір (n!)</a></p>
        <p><a href="/ga">🧬 Генетичний алгоритм</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Лаб №3", content).encode('utf-8'))
    
    def add_form(self):
        objects_json = json.dumps(OBJECTS, ensure_ascii=False)
        content = f'''
        <div class="info">Додати експертне ранжування для Лаб №3</div>
        <form method="POST" action="/lab3/add" style="max-width:500px">
            <p><strong>Перетягуйте жанри для зміни порядку:</strong></p>
            <div id="slots" style="display:flex;flex-direction:column;gap:8px;margin:20px 0"></div>
            <input type="hidden" name="ranking" id="rankingInput">
            <button type="submit" style="background:#5a67d8;color:white;padding:12px 30px;border:none;border-radius:6px;cursor:pointer;font-size:16px">Зберегти ранжування</button>
        </form>
        <p><a href="/">← Назад</a></p>
        <script>
        const objects = {objects_json};
        let ranking = [...objects];
        const container = document.getElementById('slots');
        
        function render() {{
            container.innerHTML = '';
            ranking.forEach((obj, idx) => {{
                const div = document.createElement('div');
                div.style = "padding:12px;background:white;border:2px solid #e2e8f0;border-radius:6px;cursor:grab;display:flex;justify-content:space-between";
                div.innerHTML = `<span><strong>${{idx+1}}.</strong> ${{obj}}</span><span>☰</span>`;
                div.draggable = true;
                div.ondragstart = e => e.dataTransfer.setData('idx', idx);
                div.ondragover = e => e.preventDefault();
                div.ondrop = e => {{
                    e.preventDefault();
                    const from = parseInt(e.dataTransfer.getData('idx'));
                    const to = idx;
                    [ranking[from], ranking[to]] = [ranking[to], ranking[from]];
                    render();
                }};
                container.appendChild(div);
            }});
            document.getElementById('rankingInput').value = JSON.stringify(ranking);
        }}
        render();
        </script>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Додати голос", content).encode('utf-8'))
    
    def add_vote(self):
        try:
            db = get_db()
            # Зберігаємо в music_voting.votes (для Лаб 3)
            count = db.votes.count_documents({})
            db.votes.insert_one({
                "num": count + 1,
                "preferences": json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))).decode()).get('ranking', []),
                "time": __import__('datetime').datetime.now().isoformat()
            })
            content = f'''
            <div class="info" style="background:#c6f6d5;border-color:#48bb78">
            ✅ Збережено! Всього голосів: {count + 1}
            </div>
            <p><a href="/lab3/add">→ Додати ще</a> | <a href="/matrix">→ Матриця</a> | <a href="/">← На головну</a></p>
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
        <p><a href="/">← Назад</a> | <a href="/lab3/add">→ Додати голос</a> | <a href="/brute">→ Прямий перебір</a></p>
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
        <p><a href="/">← Назад</a> | <a href="/lab3/add">→ Додати голос</a> | <a href="/ga">→ ГА</a></p>
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
        <p><a href="/">← Назад</a> | <a href="/lab3/add">→ Додати голос</a> | <a href="/brute">← Прямий перебір</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Генетичний алгоритм", content).encode('utf-8'))
