from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from .utils import html, get_db, OBJECTS
from itertools import permutations
from math import factorial
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/': self.main()
        elif path == '/matrix': self.matrix()
        elif path == '/brute': self.brute()
        elif path == '/ga': self.ga()
        else: self.send_error(404)
    
    def main(self):
        content = '''
        <div class="info">Лабораторна №3: Колективне ранжування</div>
        <p><a href="/matrix">📋 Матриця переваг</a></p>
        <p><a href="/brute">🔄 Прямий перебір (n!)</a></p>
        <p><a href="/ga">🧬 Генетичний алгоритм</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Лаб №3", content).encode('utf-8'))
    
    def matrix(self):
        try:
            db = get_db()
            # ЧИТАЄМО З votes (Лаб №1), а не rankings!
            votes = list(db.votes.find({}, {'_id': 0}))
        except: votes = []
        
        # Матриця попарних переваг
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
        <div class="info">Матриця попарних переваг<br>Число = скільки разів РЯДОК був вище СТОВПЦЯ<br>Всього голосів: {len(votes)}</div>
        <table><thead><tr><th>A vs B</th>{"".join([f"<th>{g}</th>" for g in OBJECTS])}</tr></thead><tbody>{rows}</tbody></table>
        <p><a href="/">← Назад</a> | <a href="/brute">→ Прямий перебір</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Матриця", content).encode('utf-8'))
    
    def brute(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
        except: votes = []
        
        n = len(OBJECTS)
        perms = factorial(n)
        
        # Метод Борда на основі votes
        scores = {g: 0 for g in OBJECTS}
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]] += 3
            if len(prefs) > 1: scores[prefs[1]] += 2
            if len(prefs) > 2: scores[prefs[2]] += 1
        
        borda = [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        
        content = f'''
        <div class="info">Об'єктів: {n}<br>Перестановок (n!): {perms:,}<br>Голосів в БД: {len(votes)}</div>
        <h3>Результат (метод Борда):</h3>
        <ol>{"".join([f"<li>{g}</li>" for g in borda])}</ol>
        <p><em>Повний перебір {perms:,} перестановок вимагає значних обчислень.</em></p>
        <p><a href="/">← Назад</a> | <a href="/ga">→ Генетичний алгоритм</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Прямий перебір", content).encode('utf-8'))
    
    def ga(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
        except: votes = []
        
        if len(votes) < 3:
            content = f'''
            <div class="info" style="background:#fed7d7;border-color:#e53e3e">
            ⚠️ Недостатньо даних<br>Потрібно мінімум 3 голоси (зараз {len(votes)}).
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
                if len(prefs) >= 3:
                    a, b, c = prefs[0], prefs[1], prefs[2]
                    ranks = {obj: i for i, obj in enumerate(ind)}
                    if a in ranks and b in ranks and c in ranks:
                        if not (ranks[a] < ranks[b] < ranks[c]):
                            total += 1
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
        
        # Порівняння з Борда
        scores = {g: 0 for g in OBJECTS}
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]] += 3
            if len(prefs) > 1: scores[prefs[1]] += 2
            if len(prefs) > 2: scores[prefs[2]] += 1
        borda = [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
        
        comp = "".join([f"<tr><td>{i+1}</td><td>{ga}</td><td>{bo}</td><td>{'✅' if ga==bo else '❌'}</td></tr>" for i,(ga,bo) in enumerate(zip(ga_result, borda))])
        
        content = f'''
        <div class="info">Параметри ГА:<br>Популяція: {POP_SIZE} | Поколінь: {GENERATIONS} | Мутація: {MUT_RATE*100:.0f}%<br>Голосів: {len(votes)}</div>
        <h3>Результат ГА:</h3>
        <ol>{"".join([f"<li>{g}</li>" for g in ga_result])}</ol>
        <h3>Порівняння з методом Борда:</h3>
        <table><thead><tr><th>Ранг</th><th>ГА</th><th>Борда</th><th>Збіг</th></tr></thead><tbody>{comp}</tbody></table>
        <p><a href="/">← Назад</a> | <a href="/brute">← Прямий перебір</a></p>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html("Генетичний алгоритм", content).encode('utf-8'))
