from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from .utils import html_template, get_db, GENRES
import json
from itertools import permutations
import random

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/lab3': self._main()
        elif path == '/lab3/matrix': self._matrix()
        elif path == '/lab3/bruteforce': self._brute()
        elif path == '/lab3/genetic': self._genetic()
        else: self.send_error(404)
    
    def _main(self):
        content = """
        <h2>📊 Лабораторна робота №3</h2>
        <div class="info">Визначення колективного ранжування об'єктів</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px">
            <a href="/lab3/matrix" style="padding:20px;background:#5a67d8;color:white;text-align:center;border-radius:8px;text-decoration:none"><h3>📋 Матриця переваг</h3></a>
            <a href="/lab3/bruteforce" style="padding:20px;background:#48bb78;color:white;text-align:center;border-radius:8px;text-decoration:none"><h3>🔄 Прямий перебір</h3></a>
            <a href="/lab3/genetic" style="padding:20px;background:#ed8936;color:white;text-align:center;border-radius:8px;text-decoration:none"><h3>🧬 Генетичний алгоритм</h3></a>
            <a href="/" style="padding:20px;background:#718096;color:white;text-align:center;border-radius:8px;text-decoration:none"><h3>← На головну</h3></a>
        </div>
        """
        self._send(html_template("Лаб №3", content))
    
    def _matrix(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
            leaders = self._get_leaders(db)
            matrix = self._build_matrix(votes, leaders)
            rows = ""
            for i, g1 in enumerate(leaders):
                row = f"<tr><td><strong>{g1}</strong></td>"
                for j, g2 in enumerate(leaders):
                    if i == j: row += "<td>-</td>"
                    else:
                        c = matrix.get((g1, g2), 0)
                        bg = "#c6f6d5" if c > len(votes)/2 else "#fed7d7"
                        row += f"<td style='background:{bg}'>{c}</td>"
                row += "</tr>"; rows += row
            content = f"""
            <h2>📋 Матриця попарних переваг</h2>
            <p>Число = скільки експертів віддали перевагу рядку над стовпцем</p>
            <table style='width:100%;border-collapse:collapse;margin:20px 0'><thead><tr><th>A vs B</th>{''.join([f'<th>{g}</th>' for g in leaders])}</tr></thead><tbody>{rows}</tbody></table>
            <div style="margin-top:20px"><a href="/lab3">← Назад</a> | <a href="/lab3/bruteforce">→ Прямий перебір</a></div>
            """
            self._send(html_template("Матриця переваг", content))
        except Exception as e: self._send(html_template("Помилка", f"<p class='error'>{str(e)}</p>"))
    
    def _brute(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
            leaders = self._get_leaders(db)
            if len(leaders) > 10:
                self._send(html_template("Помилка", "<p>Занадто багато об'єктів. Застосуйте евристики з Лаб 2!</p>")); return
            best, best_sum = None, float('inf')
            results = []
            for perm in permutations(leaders):
                total = sum(self._cook_dist(perm, v.get('preferences', [])) for v in votes)
                results.append((perm, total))
                if total < best_sum: best_sum, best = total, perm
            results.sort(key=lambda x: x[1])
            rows = "".join([f"<tr><td>{i+1}</td><td>{' → '.join(p)}</td><td>{d}</td></tr>" for i,(p,d) in enumerate(results[:10])])
            content = f"""
            <h2>🔄 Прямий перебір ({len(list(permutations(leaders)))} перестановок)</h2>
            <div class="info"><strong>Найкраще:</strong><br>{'<br>'.join([f'{i+1}. {g}' for i,g in enumerate(best)])}</div>
            <h3>Топ-10</h3><table><thead><tr><th>№</th><th>Ранжування</th><th>Відстань</th></tr></thead><tbody>{rows}</tbody></table>
            <div style="margin-top:20px"><a href="/lab3">← Назад</a> | <a href="/lab3/genetic">→ ГА</a></div>
            """
            self._send(html_template("Прямий перебір", content))
        except Exception as e: self._send(html_template("Помилка", f"<p class='error'>{str(e)}</p>"))
    
    def _genetic(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
            leaders = self._get_leaders(db)
            POP, GEN, MUT = 20, 50, 0.3
            pop = [list(leaders) for _ in range(POP)]
            for p in pop: random.shuffle(p)
            def fit(r): return sum(self._cook_dist(r, v.get('preferences', [])) for v in votes)
            best_ever, best_fit = None, float('inf')
            for _ in range(GEN):
                fits = [fit(p) for p in pop]
                bi = fits.index(min(fits))
                if fits[bi] < best_fit: best_fit, best_ever = fits[bi], pop[bi].copy()
                new = [pop[bi].copy()]
                while len(new) < POP:
                    p = pop[random.randint(0,POP-1) if fits[random.randint(0,POP-1)] < fits[random.randint(0,POP-1)] else random.randint(0,POP-1)].copy()
                    if random.random() < MUT:
                        i,j = random.sample(range(len(p)),2); p[i],p[j] = p[j],p[i]
                    new.append(p)
                pop = new
            content = f"""
            <h2>🧬 Генетичний алгоритм</h2>
            <div class="info"><strong>Параметри:</strong><br>Популяція: {POP}<br>Поколінь: {GEN}<br>Мутація: {MUT}</div>
            <div class="info" style="background:#c6f6d5"><strong>Результат:</strong><br>{'<br>'.join([f'{i+1}. {g}' for i,g in enumerate(best_ever)])}<br><strong>Фітнес: {best_fit}</strong></div>
            <div style="margin-top:20px"><a href="/lab3">← Назад</a> | <a href="/lab3/bruteforce">← Прямий перебір</a></div>
            """
            self._send(html_template("Генетичний алгоритм", content))
        except Exception as e: self._send(html_template("Помилка", f"<p class='error'>{str(e)}</p>"))
    
    def _get_leaders(self, db):
        scores = {g:0 for g in GENRES}
        for v in db.votes.find({}, {'_id':0}):
            prefs = v.get('preferences',[])
            if len(prefs)>0: scores[prefs[0]]+=3
            if len(prefs)>1: scores[prefs[1]]+=2
            if len(prefs)>2: scores[prefs[2]]+=1
        return [g for g,_ in sorted(scores.items(),key=lambda x:x[1],reverse=True) if scores[g]>0][:10]
    
    def _build_matrix(self, votes, leaders):
        m = {}
        for v in votes:
            prefs = v.get('preferences',[])
            for i in range(len(prefs)):
                for j in range(i+1,len(prefs)):
                    a,b = prefs[i],prefs[j]
                    if a in leaders and b in leaders: m[(a,b)] = m.get((a,b),0)+1
        return m
    
    def _cook_dist(self, ranking, prefs):
        if len(prefs)<3: return 0
        ranks = {g:i for i,g in enumerate(ranking)}
        a,b,c = prefs[0],prefs[1],prefs[2]
        return 0 if (a in ranks and b in ranks and c in ranks and ranks[a]<ranks[b]<ranks[c]) else 1
    
    def _send(self, html):
        self.send_response(200); self.send_header('Content-type','text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(html.encode('utf-8'))
