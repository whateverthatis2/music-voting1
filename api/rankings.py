from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from .utils import html, get_db, RANKING_OBJECTS
import json, random
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/aggregated-rankings': self._show_aggregated()
        else: self._show_form()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/save-ranking': self._save_ranking()
        else: self.send_error(404)

    def _show_form(self):
        objects_json = json.dumps(RANKING_OBJECTS, ensure_ascii=False)
        content = f"""
        <div class="info">Розташуйте 10 жанрів від 1 до 10. Перетягуйте для зміни.</div>
        <div id="rankSlots" style="display:flex;flex-direction:column;gap:5px"></div>
        <div style="margin-top:20px">
            <button id="submitBtn" disabled>Зберегти</button>
            <div id="result" style="margin-top:10px"></div>
        </div>
        <p><a href="/aggregated-rankings">Компромісне ранжування (ГА)</a> | <a href="/">На головну</a></p>
        <script>
        const objects = {objects_json};
        let ranking = [...objects].sort(() => Math.random() - 0.5);
        const container = document.getElementById('rankSlots');
        
        function render() {{
            container.innerHTML = '';
            ranking.forEach((obj, idx) => {{
                const div = document.createElement('div');
                div.style = "padding:10px;background:white;border:1px solid #ddd;cursor:grab;display:flex;justify-content:space-between";
                div.innerHTML = `<span>${{idx+1}}</span><span>${{obj}}</span>`;
                div.ondragstart = (e) => {{ e.dataTransfer.setData('idx', idx); }};
                div.ondragover = (e) => e.preventDefault();
                div.ondrop = (e) => {{
                    e.preventDefault();
                    const from = parseInt(e.dataTransfer.getData('idx'));
                    const to = idx;
                    const temp = ranking[from]; ranking[from] = ranking[to]; ranking[to] = temp;
                    render();
                }};
                container.appendChild(div);
            }});
            document.getElementById('submitBtn').disabled = ranking.length !== 10;
        }}
        render();
        document.getElementById('submitBtn').onclick = async () => {{
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            try {{
                const res = await fetch('/save-ranking', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ranking: ranking}})
                }});
                const data = await res.json();
                if(data.success) {{
                    document.getElementById('result').innerHTML = '✅ Збережено #' + data.count;
                    ranking = [...objects].sort(() => Math.random() - 0.5);
                    render();
                }}
            }} catch(e) {{ document.getElementById('result').innerHTML = '❌ Помилка'; }}
            btn.disabled = false;
        }};
        </script>
        """
        self._send_html(html("Ранжування 10 об'єктів", content))

    def _save_ranking(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode())
            db = get_db()
            count = db.rankings.count_documents({})
            db.rankings.insert_one({
                "num": count + 1, "ranking": data['ranking'], 
                "time": datetime.now().isoformat()
            })
            self._send_json({"success": True, "count": count + 1})
        except Exception as e:
            self._send_json({"error": str(e)})

    def _show_aggregated(self):
        try:
            db = get_db()
            rankings = list(db.rankings.find({}, {'_id': 0}).sort("num", 1))
        except: rankings = []
        
        if len(rankings) < 5:
            self._send_html(html("ГА", f"<p class='error'>Треба мінімум 5 ранжувань (зараз {len(rankings)}). <a href='/rankings'>Додати</a></p>"))
            return

        ga_result = self._ga(rankings)
        borda = self._borda(rankings)
        
        comp_rows = "".join([f"<tr><td>{i+1}</td><td>{g}</td><td>{b}</td><td>{'✅' if g==b else '❌'}</td></tr>" for i,(g,b) in enumerate(zip(ga_result, borda))])
        
        content = f"""
        <h3>Результат ГА (найкращий з 50 поколінь)</h3>
        <ol>{"".join([f"<li>{g}</li>" for g in ga_result])}</ol>
        <h3>Порівняння з методом Борда</h3>
        <table><thead><tr><th>Ранг</th><th>ГА</th><th>Борда</th><th>Збіг</th></tr></thead><tbody>{comp_rows}</tbody></table>
        <p><a href="/rankings">← Додати ще</a> | <a href="/">На головну</a></p>
        """
        self._send_html(html("Агрегування (ГА)", content))

    def _ga(self, rankings, gens=50):
        def fitness(ind):
            score = 0
            for r in rankings:
                inv = 0
                for i in range(len(ind)):
                    for j in range(i+1, len(ind)):
                        if r['ranking'].index(ind[i]) > r['ranking'].index(ind[j]): inv += 1
                score += 1 / (1 + inv)
            return score
        
        pop = [RANKING_OBJECTS.copy() for _ in range(20)]
        for p in pop: random.shuffle(p)
        
        for _ in range(gens):
            fits = [fitness(p) for p in pop]
            best = pop[fits.index(max(fits))].copy()
            new_pop = [best]
            while len(new_pop) < 20:
                p1 = pop[random.randint(0, 19)].copy()
                if random.random() < 0.3:
                    i, j = random.sample(range(10), 2)
                    p1[i], p1[j] = p1[j], p1[i]
                new_pop.append(p1)
            pop = new_pop
        return pop[0]

    def _borda(self, rankings):
        scores = {o: 0 for o in RANKING_OBJECTS}
        for r in rankings:
            for i, o in enumerate(r['ranking']):
                scores[o] += (10 - i)
        return [o for o, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]

    def _send_html(self, html_str):
        self.send_response(200); self.send_header('Content-type','text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(html_str.encode('utf-8'))
    def _send_json(self, d):
        self.send_response(200); self.send_header('Content-type','application/json'); self.end_headers()
        self.wfile.write(json.dumps(d).encode('utf-8'))
