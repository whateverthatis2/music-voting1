from http.server import BaseHTTPRequestHandler
from .utils import OBJECTS, PROTOCOL_PASSWORD, load_rankings, save_ranking, get_db, html_template, GENRES
from urllib.parse import parse_qs
import json, random, time
from itertools import permutations
from math import factorial

# ==================== ГОЛОВНА СТОРІНКА (РАНЖУВАННЯ) ====================

def index_handler(self):
    objects_json = json.dumps(OBJECTS, ensure_ascii=False)
    content = '''<div class="info-box"><strong>📊 Експертне ранжування:</strong> Розставте 10 об'єктів за пріоритетом (1 - найважливіший).</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
    <div><h3>📦 Об'єкти</h3><div id="objectsList" style="min-height:300px;border:2px dashed #e2e8f0;border-radius:8px;padding:10px"></div></div>
    <div><h3>🎯 Порядок пріоритетів</h3><div id="rankingSlots" style="min-height:300px"></div></div></div>
    <div style="text-align:center;margin-top:20px"><button id="submitBtn" disabled style="padding:12px 30px;font-size:16px;background:#5a67d8;color:white;border:none;border-radius:6px;cursor:pointer;margin-top:15px">Зберегти ранжування</button>
    <div id="result" style="margin-top:15px;padding:15px;border-radius:6px;display:none"></div></div>
    <div class="links">
        <a href="/results">📊 Результати</a>
        <a href="/protocol">🔐 Протокол</a>
        <a href="/lab3">🧬 Лаб №3</a>
    </div>
    <style>
    .obj-item{background:#f7fafc;padding:12px;margin:8px 0;border-radius:6px;border:2px solid #e2e8f0;cursor:grab;display:flex;justify-content:space-between;align-items:center}
    .obj-item:hover{border-color:#5a67d8}.obj-item.dragging{opacity:.5}.obj-item.in-ranking{display:none}
    .obj-name{font-weight:600}.obj-rank{background:#5a67d8;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:.85em}
    .rank-slot{background:white;border:2px dashed #cbd5e0;border-radius:6px;padding:12px;margin:8px 0;display:flex;align-items:center;gap:10px;min-height:44px}
    .rank-slot.filled{border-style:solid;border-color:#48bb78;background:#f0fff4}.rank-slot.drag-over{background:#e0e7ff;border-color:#5a67d8}
    .rank-num{font-weight:bold;color:#5a67d8;min-width:24px}.slot-placeholder{color:#999}
    </style>
    <script>
    const objects = ''' + objects_json + ''';
    let ranking = [];
    const list = document.getElementById('objectsList');
    const slots = document.getElementById('rankingSlots');
    objects.forEach((o, i) => {
        const div = document.createElement('div');
        div.className = 'obj-item'; div.draggable = true; div.dataset.idx = i;
        div.innerHTML = '<span class="obj-name">' + o + '</span><span class="obj-rank">' + (i+1) + '</span>';
        div.addEventListener('dragstart', function(e) { e.dataTransfer.setData('idx', this.dataset.idx); this.classList.add('dragging'); });
        div.addEventListener('dragend', function() { this.classList.remove('dragging'); });
        div.addEventListener('click', function() { addToRanking(parseInt(this.dataset.idx)); });
        list.appendChild(div);
    });
    for (let i = 0; i < objects.length; i++) {
        const slot = document.createElement('div');
        slot.className = 'rank-slot'; slot.dataset.rank = i + 1;
        slot.innerHTML = '<span class="rank-num">' + (i+1) + '.</span><span class="slot-placeholder">Перетягніть</span>';
        slot.addEventListener('dragover', function(e) { e.preventDefault(); this.classList.add('drag-over'); });
        slot.addEventListener('dragleave', function() { this.classList.remove('drag-over'); });
        slot.addEventListener('drop', function(e) { e.preventDefault(); this.classList.remove('drag-over'); const idx = parseInt(e.dataTransfer.getData('idx')); moveToRanking(idx, parseInt(this.dataset.rank)); });
        slot.addEventListener('click', function() { if (this.classList.contains('filled')) { removeFromRanking(parseInt(this.dataset.rank)); }});
        slots.appendChild(slot);
    }
    function addToRanking(idx) { if (ranking.includes(idx)) return; ranking.push(idx); updateDisplay(); }
    function moveToRanking(idx, rank) { const pos = ranking.indexOf(idx); if (pos >= 0) ranking.splice(pos, 1); ranking.splice(rank - 1, 0, idx); updateDisplay(); }
    function removeFromRanking(rank) { ranking.splice(rank - 1, 1); updateDisplay(); }
    function updateDisplay() {
        document.querySelectorAll('.obj-item').forEach((el, i) => { el.classList.toggle('in-ranking', ranking.includes(i)); });
        document.querySelectorAll('.rank-slot').forEach((slot, i) => {
            const idx = ranking[i];
            if (idx !== undefined) { slot.classList.add('filled'); slot.innerHTML = '<span class="rank-num">' + (i+1) + '.</span><span class="obj-name">' + objects[idx] + '</span>'; }
            else { slot.classList.remove('filled'); slot.innerHTML = '<span class="rank-num">' + (i+1) + '.</span><span class="slot-placeholder">Перетягніть</span>'; }
        });
        document.getElementById('submitBtn').disabled = ranking.length !== objects.length;
    }
    document.getElementById('submitBtn').addEventListener('click', async function() {
        try {
            const response = await fetch('/submit', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ranking: ranking.map(i => objects[i])}) });
            const result = await response.json();
            const resDiv = document.getElementById('result');
            if (result.success) { resDiv.innerHTML = 'Збережено!'; resDiv.style.cssText = 'display:block;background:#c6f6d5;color:#22543d;'; ranking = []; updateDisplay(); }
            else { resDiv.innerHTML = 'Помилка: ' + result.error; resDiv.style.cssText = 'display:block;background:#fed7d7;color:#c53030;'; }
        } catch (e) { alert('Помилка: ' + e.message); }
    });
    </script>'''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html_template("Ранжування", content).encode('utf-8'))

# ==================== ЗБЕРЕЖЕННЯ РАНЖУВАННЯ ====================

def submit_handler(self, body):
    data = json.loads(body) if body else {}
    ranking = data.get('ranking')
    if not ranking or len(ranking) != len(OBJECTS):
        return send_json(self, {"error": "Неповне ранжування"})
    expert = "Експерт_" + str(int(time.time() % 10000))
    if save_ranking(expert, ranking):
        send_json(self, {"success": True})
    else:
        send_json(self, {"error": "Помилка БД"})

# ==================== РЕЗУЛЬТАТИ ====================

def results_handler(self):
    rankings = load_rankings()
    # Тільки мурашиний алгоритм (спрощений)
    ant = ant_colony(rankings) if rankings else OBJECTS.copy()
    ant_fit = fitness(ant, rankings) if rankings else 0
    content = f'''<h2>📊 Результати ранжування</h2><p>Отримано ранжувань: <b>{len(rankings)}</b></p>
    <h3>🐜 Компромісне ранжування (Мурашиний алгоритм)</h3>
    <div style="background:#e6fffa;padding:20px;border-radius:8px;margin:20px 0;border:2px solid #38b2ac">
    <p style="font-size:1.2em;margin:0"><strong>Результат:</strong></p>
    <p style="font-size:1.5em;color:#2c7a7b;margin:10px 0">{' → '.join(ant)}</p>
    <p style="color:#666;margin:0"><strong>Фітнес (відстань Кеміні):</strong> {-ant_fit}</p>
    </div>
    <h3>📋 Всі ранжування</h3><table><thead><tr><th>Експерт</th><th>Час</th><th>Порядок</th></tr></thead><tbody>'''
    for r in rankings:
        content += f'<tr><td><b>{r.get("expert","")}</b></td><td>{r.get("time","")[:19]}</td><td>{" → ".join(r.get("ranking",[]))}</td></tr>'
    content += '''</tbody></table><div class="links"><a href="/">← Ранжувати</a><a href="/protocol">🔐 Протокол</a><a href="/lab3">🧬 Лаб №3</a></div>'''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html_template("Результати", content).encode('utf-8'))

# ==================== ПРОТОКОЛ ====================

def protocol_handler(self, method='GET', body=''):
    if method == 'GET':
        return protocol_form(self)
    params = parse_qs(body)
    if params.get('password', [''])[0] == PROTOCOL_PASSWORD:
        return protocol_show(self)
    return protocol_form(self, error="Неправильний пароль!")

def protocol_show(self):
    rankings = load_rankings()
    entries = "".join('<div style="background:#2d3748;padding:15px;margin:10px 0;border-left:3px solid #48bb78;border-radius:4px"><div style="color:#a0aec0">['+r.get('time','N/A')[:19]+'] '+r.get('expert','N/A')+'</div><div style="color:#48bb78;margin-top:5px">Ранжування: '+' → '.join(r.get('ranking',[]))+'</div></div>' for r in rankings)
    html = f'''<!DOCTYPE html><html lang="uk"><head><meta charset="UTF-8"><title>Протокол</title>
    <style>body{{font-family:'Courier New',monospace;background:#1a202c;color:#48bb78;padding:40px;margin:0}}.container{{max-width:900px;margin:0 auto;background:#2d3748;padding:30px;border-radius:10px}}h1{{color:#fff;border-bottom:2px solid #48bb78;padding-bottom:10px}}a{{color:#63b3ed;text-decoration:none}}</style></head>
    <body><div class="container"><h1>🔐 ПРОТОКОЛ<a href="/" style="float:right">[← Назад]</a></h1><p style="color:#a0aec0">Записів: {len(rankings)}</p>{entries}</div></body></html>'''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html.encode('utf-8'))

def protocol_form(self, error=""):
    error_html = '<p style="color:#fc8181;font-weight:bold">'+error+'</p>' if error else ""
    html = '<!DOCTYPE html><html lang="uk"><head><meta charset="UTF-8"><title>Доступ</title><style>body{font-family:sans-serif;background:#1a202c;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0}.box{background:#2d3748;padding:40px;border-radius:15px;max-width:400px;text-align:center}h2{color:#fff}input{width:100%;padding:14px;margin:15px 0;border:2px solid #4a5568;border-radius:8px;background:#1a202c;color:#fff;font-size:16px}button{width:100%;padding:14px;background:#5a67d8;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;font-weight:600}</style></head><body><div class="box"><h2>🔐 Доступ до протоколу</h2><p style="color:#a0aec0;margin:20px 0">Введіть пароль</p>'+error_html+'<form method="POST" action="/protocol"><input type="password" name="password" placeholder="Пароль" required><button type="submit">Увійти</button></form></div></body></html>'
    self.send_response(401 if error else 200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html.encode('utf-8'))

# ==================== ЛАБОРАТОРНА №3 ====================

def lab3_main(self):
    content = '''
    <h2>📊 Лабораторна робота №3</h2>
    <div class="info-box">Визначення колективного ранжування об'єктів</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-top:20px">
        <a href="/lab3/matrix" class="btn">📋 Матриця переваг</a>
        <a href="/lab3/brute" class="btn">🔄 Прямий перебір</a>
        <a href="/lab3/ga" class="btn">🧬 Генетичний алгоритм</a>
        <a href="/" class="btn" style="background:#718096">← На головну</a>
    </div>
    '''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html_template("Лаб №3", content).encode('utf-8'))

def lab3_matrix(self):
    rankings = load_rankings()
    matrix = {}
    for g1 in OBJECTS:
        for g2 in OBJECTS:
            if g1 != g2: matrix[(g1,g2)] = 0
    for r in rankings:
        rank = r.get('ranking', [])
        for i in range(len(rank)):
            for j in range(i+1, len(rank)):
                a, b = rank[i], rank[j]
                if a in OBJECTS and b in OBJECTS:
                    matrix[(a,b)] = matrix.get((a,b), 0) + 1
    rows = ""
    for g1 in OBJECTS:
        row = f"<tr><td><strong>{g1}</strong></td>"
        for g2 in OBJECTS:
            if g1 == g2: row += "<td>-</td>"
            else:
                c = matrix.get((g1,g2), 0)
                bg = "#c6f6d5" if c > len(rankings)/2 else "#fed7d7"
                row += f"<td style='background:{bg};text-align:center'>{c}</td>"
        row += "</tr>"; rows += row
    content = f'''
    <h2>📋 Матриця попарних переваг</h2>
    <p>Число = скільки разів <strong>рядок</strong> був вище <strong>стовпця</strong></p>
    <table style='width:100%;border-collapse:collapse;margin:20px 0;font-size:0.9em'><thead><tr><th>A vs B</th>{''.join([f'<th>{g}</th>' for g in OBJECTS])}</tr></thead><tbody>{rows}</tbody></table>
    <div class="links"><a href="/lab3">← Назад</a><a href="/lab3/brute">→ Прямий перебір</a></div>
    '''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html_template("Матриця переваг", content).encode('utf-8'))

def lab3_brute(self):
    rankings = load_rankings()
    n = len(OBJECTS)
    perms = factorial(n)
    # Метод Борда як референс
    scores = {g: 0 for g in OBJECTS}
    for r in rankings:
        rank = r.get('ranking', [])
        for i, g in enumerate(rank):
            if g in OBJECTS: scores[g] += (n - i)
    borda_result = [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
    content = f'''
    <h2>🔄 Прямий перебір</h2>
    <div class="info-box"><strong>Об'єктів:</strong> {n}<br><strong>Перестановок (n!):</strong> {perms:,}<br><strong>Ранжувань:</strong> {len(rankings)}</div>
    <h3>Результат (метод Борда):</h3><ol>{''.join([f'<li>{g}</li>' for g in borda_result])}</ol>
    <p><em>Повний перебір {perms:,} перестановок вимагає значних обчислень.</em></p>
    <div class="links"><a href="/lab3">← Назад</a><a href="/lab3/ga">→ ГА</a></div>
    '''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html_template("Прямий перебір", content).encode('utf-8'))

def lab3_ga(self):
    rankings = load_rankings()
    if len(rankings) < 3:
        content = f'''<h2>🧬 Генетичний алгоритм</h2><div class="info-box" style="background:#fed7d7;border-color:#e53e3e"><strong>⚠️ Недостатньо даних</strong><br>Потрібно мінімум 3 ранжування (зараз {len(rankings)}).<br><a href="/">← Додати ранжування</a></div>'''
        self.send_response(200); self.send_header('Content-type', 'text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(html_template("ГА", content).encode('utf-8')); return
    POP_SIZE, GENERATIONS, MUT_RATE = 20, 50, 0.3
    def fitness(ind):
        total = 0
        for r in rankings:
            exp = r.get('ranking', [])
            for i, obj in enumerate(ind):
                if obj in exp: total += abs(i - exp.index(obj))
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
    for r in rankings:
        rank = r.get('ranking', [])
        for i, g in enumerate(rank):
            if g in OBJECTS: scores[g] += (len(OBJECTS) - i)
    borda = [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
    comp = "".join([f"<tr><td>{i+1}</td><td>{ga}</td><td>{bo}</td><td>{'✅' if ga==bo else '❌'}</td></tr>" for i,(ga,bo) in enumerate(zip(ga_result, borda))])
    content = f'''
    <h2>🧬 Генетичний алгоритм</h2>
    <div class="info-box"><strong>Параметри:</strong><br>Популяція: {POP_SIZE} | Поколінь: {GENERATIONS} | Мутація: {MUT_RATE*100:.0f}%</div>
    <h3>Результат ГА:</h3><ol>{''.join([f'<li>{g}</li>' for g in ga_result])}</ol>
    <h3>Порівняння з методом Борда:</h3>
    <table><thead><tr><th>Ранг</th><th>ГА</th><th>Борда</th><th>Збіг</th></tr></thead><tbody>{comp}</tbody></table>
    <div class="links"><a href="/lab3">← Назад</a><a href="/lab3/brute">← Прямий перебір</a></div>
    '''
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(html_template("Генетичний алгоритм", content).encode('utf-8'))

# ==================== МЕТАЕВРИСТИКИ (для results) ====================

def fitness(ranking, expert_rankings):
    total = 0
    for exp in expert_rankings:
        exp_rank = exp.get('ranking', [])
        for i, obj in enumerate(ranking):
            if obj in exp_rank:
                total += abs(i - exp_rank.index(obj))
    return -total

def mutate(ranking):
    r = ranking.copy()
    i, j = random.sample(range(len(r)), 2)
    r[i], r[j] = r[j], r[i]
    return r

def ant_colony(expert_rankings, iterations=100, ants=50):
    n = len(OBJECTS)
    pheromone = [[1.0] * n for _ in range(n)]
    best_ranking, best_fit = None, float('-inf')
    for iteration in range(iterations):
        solutions = []
        for _ in range(ants):
            solution = []
            available = OBJECTS.copy()
            while available:
                if not solution:
                    obj = random.choice(available)
                else:
                    last_idx = OBJECTS.index(solution[-1])
                    probs = [pheromone[last_idx][OBJECTS.index(o)] for o in available]
                    total = sum(probs)
                    r = random.random() * total
                    cumsum = 0
                    obj = available[0]
                    for i, o in enumerate(available):
                        cumsum += probs[i]
                        if cumsum >= r:
                            obj = o
                            break
                solution.append(obj)
                available.remove(obj)
            solutions.append(solution)
            f = fitness(solution, expert_rankings)
            if f > best_fit:
                best_fit, best_ranking = f, solution
        for sol in solutions:
            for i in range(n - 1):
                idx1, idx2 = OBJECTS.index(sol[i]), OBJECTS.index(sol[i + 1])
                pheromone[idx1][idx2] += 0.1
        for row in pheromone:
            for i in range(len(row)):
                row[i] *= 0.95
    return best_ranking if best_ranking else OBJECTS.copy()

# ==================== ДОПОМІЖНІ ====================

def send_json(self, data):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

# ==================== ГОЛОВНИЙ HANDLER ====================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/': index_handler(self)
        elif self.path == '/results': results_handler(self)
        elif self.path == '/protocol': protocol_handler(self, 'GET', '')
        elif self.path == '/lab3': lab3_main(self)
        elif self.path == '/lab3/matrix': lab3_matrix(self)
        elif self.path == '/lab3/brute': lab3_brute(self)
        elif self.path == '/lab3/ga': lab3_ga(self)
        else: send_json(self, {"error": "Not found"}, 404)
    
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8')
        if self.path == '/submit': submit_handler(self, body)
        elif self.path == '/protocol': protocol_handler(self, 'POST', body)
        else: send_json(self, {"error": "Not found"}, 404)
