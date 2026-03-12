from http.server import BaseHTTPRequestHandler
from .utils import get_db, html_template
from urllib.parse import urlparse
import json
import random

RANKING_OBJECTS = ["Фанк", "Рок", "Електронна", "Інді", "Реп", 
                   "R&B/Soul", "Панк", "Транс", "Блюз", "Латино"]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/rankings':
            self._show_form()
        elif path == '/aggregated-rankings':
            self._show_aggregated()
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == '/save-ranking':
            self._save_ranking()
        else:
            self.send_error(404)
    
    def _show_form(self):
        # Форма drag-drop ранжування 10 об'єктів
        objects_json = json.dumps(RANKING_OBJECTS, ensure_ascii=False)
        
        content = f'''
        <div class="info-box">
            <strong>🎯 Агрегування ранжувань:</strong> Розташуйте 10 жанрів від 1 до 10. 
            Перетягуйте для зміни порядку. Зберіть 5-8 ранжувань.
        </div>
        
        <div class="ranking-list" id="rankingList">
            <div class="rank-slots" id="rankSlots"></div>
        </div>
        
        <div class="controls">
            <button id="submitBtn" disabled>Зберегти ранжування</button>
            <button id="clearBtn" style="background:#e53e3e;margin-left:10px;">Очистити</button>
            <div id="result" class="result-box"></div>
        </div>
        
        <div class="links">
            <a href="/aggregated-rankings">📋 Компромісне ранжування</a>
            <a href="/">← На головну</a>
        </div>
        
        <style>
            .ranking-list {{ background: #fffaf0; padding: 20px; border-radius: 8px; border: 2px solid #ed8936; }}
            .rank-slots {{ display: flex; flex-direction: column; gap: 8px; }}
            .rank-slot {{ display: flex; align-items: center; gap: 15px; padding: 12px; background: white; border: 2px solid #e2e8f0; border-radius: 6px; cursor: grab; }}
            .rank-slot.dragging {{ opacity: 0.5; }}
            .rank-num {{ width: 30px; height: 30px; background: #5a67d8; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }}
            .rank-slot.top-3 .rank-num {{ background: #ffd700; color: #744210; }}
            .rank-slot.top-3 {{ background: #fffbeb; border-color: #ffd700; }}
            .controls {{ text-align: center; margin: 20px 0; }}
            .result-box {{ margin-top: 15px; padding: 15px; border-radius: 6px; display: none; }}
        </style>
        
        <script>
            const objects = {objects_json};
            let currentRanking = [...objects].sort(() => Math.random() - 0.5);
            
            function render() {{
                const container = document.getElementById('rankSlots');
                container.innerHTML = '';
                currentRanking.forEach((obj, idx) => {{
                    const slot = document.createElement('div');
                    slot.className = 'rank-slot' + (idx < 3 ? ' top-3' : '');
                    slot.draggable = true;
                    slot.dataset.index = idx;
                    slot.innerHTML = `<span class="rank-num">${{idx + 1}}</span><span style="flex-grow:1;font-weight:500;">${{obj}}</span>`;
                    
                    let draggedIdx = null;
                    slot.addEventListener('dragstart', (e) => {{ draggedIdx = idx; slot.classList.add('dragging'); }});
                    slot.addEventListener('dragend', () => slot.classList.remove('dragging'));
                    slot.addEventListener('dragover', (e) => e.preventDefault());
                    slot.addEventListener('drop', (e) => {{
                        const targetIdx = idx;
                        if (draggedIdx === targetIdx) return;
                        const temp = currentRanking[draggedIdx];
                        currentRanking[draggedIdx] = currentRanking[targetIdx];
                        currentRanking[targetIdx] = temp;
                        render();
                    }});
                    
                    container.appendChild(slot);
                }});
                document.getElementById('submitBtn').disabled = currentRanking.length !== 10;
            }}
            
            document.getElementById('clearBtn').addEventListener('click', () => {{
                currentRanking = [];
                render();
            }});
            
            document.getElementById('submitBtn').addEventListener('click', async () => {{
                const btn = document.getElementById('submitBtn');
                btn.disabled = true;
                try {{
                    const response = await fetch('/save-ranking', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ ranking: currentRanking }})
                    }});
                    const result = await response.json();
                    const resDiv = document.getElementById('result');
                    if (result.success) {{
                        resDiv.innerHTML = `✅ Ранжування #${{result.count}} збережено!`;
                        resDiv.style.cssText = 'display:block;background:#c6f6d5;color:#22543d;';
                        currentRanking = [...objects].sort(() => Math.random() - 0.5);
                        render();
                    }} else throw new Error(result.error);
                }} catch (e) {{
                    document.getElementById('result').textContent = '❌ ' + e.message;
                    document.getElementById('result').style.cssText = 'display:block;background:#fed7d7;color:#c53030;';
                }}
                btn.disabled = false;
            }});
            
            render();
        </script>
        '''
        
        html = html_template("Ранжування 10 об'єктів", content)
        self.wfile.write(html.encode('utf-8'))
    
    def _save_ranking(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        ranking = post_data.get('ranking', [])
        if len(ranking) != 10:
            self._send_json({"error": "Потрібно 10 об'єктів"})
            return
        
        try:
            from datetime import datetime
            db = get_db()
            collection = db.rankings
            count = collection.count_documents({})
            
            collection.insert_one({
                "num": count + 1,
                "ranking": ranking,
                "time": datetime.now().isoformat()
            })
            
            self._send_json({"success": True, "count": count + 1})
        except Exception as e:
            self._send_json({"error": str(e)})
    
    def _show_aggregated(self):
        try:
            db = get_db()
            rankings = list(db.rankings.find({}, {'_id': 0}).sort("num", 1))
        except:
            rankings = []
        
        if len(rankings) < 5:
            content = '''
            <div class="error-box">
                <strong>⚠️ Недостатньо даних</strong><br>
                Зібрано ''' + str(len(rankings)) + ''' ранжувань, потрібно мінімум 5.<br>
                <a href="/rankings">← Додати ранжування</a>
            </div>
            '''
            html = html_template("Компромісне ранжування", content)
            self.wfile.write(html.encode('utf-8'))
            return
        
        # === ГЕНЕТИЧНИЙ АЛГОРИТМ ===
        ga_result = self._genetic_algorithm(rankings)
        
        # === МЕТОД БОРДА ===
        borda_result = self._borda_method(rankings)
        
        # Порівняння
        comparison = ""
        for i, (ga, bo) in enumerate(zip(ga_result, borda_result)):
            match = "✓" if ga == bo else "✗"
            comparison += f"<tr><td>{i+1}</td><td><strong>{ga}</strong></td><td>{bo}</td><td>{match}</td></tr>"
        
        content = f'''
        <h3>🏆 Результат генетичного алгоритму</h3>
        <table class="result-table">
            <thead><tr><th>Ранг</th><th>Жанр (ГА)</th></tr></thead>
            <tbody>
                {''.join([f'<tr class="{"top-3" if i < 3 else ""}"><td>{i+1}</td><td><strong>{obj}</strong></td></tr>' for i, obj in enumerate(ga_result)])}
            </tbody>
        </table>
        
        <h3>📊 Порівняння з методом Борда</h3>
        <table class="compare-table">
            <thead><tr><th>Ранг</th><th>Генетичний алгоритм</th><th>Метод Борда</th><th>Співпадіння</th></tr></thead>
            <tbody>{comparison}</tbody>
        </table>
        
        <h3>📋 Вихідні ранжування ({len(rankings)})</h3>
        <div class="table-scroll">
            <table class="all-rankings">
                <thead><tr><th>№</th>{''.join([f'<th>{o[:4]}</th>' for o in RANKING_OBJECTS])}</tr></thead>
                <tbody>
                    {''.join([f"<tr><td>#{r['num']}</td>{''.join([f'<td>{r[chr(39)]ranking[chr(39)].index(o)+1}</td>' for o in RANKING_OBJECTS])}</tr>" for r in rankings])}
                </tbody>
            </table>
        </div>
        
        <div class="links"><a href="/rankings">← Додати ще</a> <a href="/">На головну</a></div>
        
        <style>
            .result-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .result-table th {{ background: #5a67d8; color: white; padding: 15px; }}
            .result-table td {{ padding: 15px; border-bottom: 2px solid #e2e8f0; }}
            .result-table tr.top-3 {{ background: #fffbeb; font-size: 1.2em; }}
            .compare-table {{ width: 100%; margin: 20px 0; border-collapse: collapse; }}
            .compare-table th {{ background: #4c51bf; color: white; padding: 12px; }}
            .compare-table td {{ padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }}
            .all-rankings {{ font-size: 0.8em; }}
            .all-rankings td, .all-rankings th {{ padding: 6px; border: 1px solid #ddd; text-align: center; }}
            .table-scroll {{ overflow-x: auto; }}
        </style>
        '''
        
        html = html_template("ГА — агрегування", content)
        self.wfile.write(html.encode('utf-8'))
    
    def _genetic_algorithm(self, rankings, generations=50, pop_size=20):
        """Спрощений ГА"""
        objects = RANKING_OBJECTS.copy()
        
        def fitness(ind):
            score = 0
            for expert in rankings:
                # Кендалл тау відстань
                inversions = 0
                for i in range(len(ind)):
                    for j in range(i+1, len(ind)):
                        pos_i = expert['ranking'].index(ind[i])
                        pos_j = expert['ranking'].index(ind[j])
                        if (i < j and pos_i > pos_j) or (i > j and pos_i < pos_j):
                            inversions += 1
                score += 1 / (1 + inversions)
            return score
        
        # Популяція
        pop = [objects.copy() for _ in range(pop_size)]
        for p in pop:
            random.shuffle(p)
        
        # Додати експертів
        for r in rankings[:3]:
            pop.append(r['ranking'].copy())
        
        for _ in range(generations):
            fitnesses = [fitness(p) for p in pop]
            
            # Селекція + схрещування + мутація
            new_pop = [pop[fitnesses.index(max(fitnesses))].copy()]  # Елітизм
            
            while len(new_pop) < pop_size:
                # Турнір
                candidates = random.sample(range(len(pop)), 3)
                best = max(candidates, key=lambda i: fitnesses[i])
                parent = pop[best].copy()
                
                # Мутація (swap)
                if random.random() < 0.3:
                    i, j = random.sample(range(10), 2)
                    parent[i], parent[j] = parent[j], parent[i]
                
                new_pop.append(parent)
            
            pop = new_pop
        
        final_fitnesses = [fitness(p) for p in pop]
        best_idx = final_fitnesses.index(max(final_fitnesses))
        return pop[best_idx]
    
    def _borda_method(self, rankings):
        """Метод Борда для порівняння"""
        scores = {obj: 0 for obj in RANKING_OBJECTS}
        
        for r in rankings:
            for idx, obj in enumerate(r['ranking']):
                scores[obj] += (10 - idx)  # 10 за 1-ше, 1 за 10-те
        
        return [obj for obj, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
