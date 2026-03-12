from http.server import BaseHTTPRequestHandler
from .utils import html_template, HEURISTICS, get_db
from urllib.parse import urlparse, parse_qs
import json
import random
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/' or path == '/heuristics':
            self._show_heuristics()
        elif path == '/heuristic-votes':
            self._show_heuristic_protocol()
        else:
            self.send_error(404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == '/vote-heuristic':
            self._save_heuristic_vote()
        else:
            self.send_error(404)
    
    def _show_heuristics(self):
        # Код з попередньої версії — форма вибору 2 евристик з drag & drop
        heuristics_json = json.dumps(HEURISTICS, ensure_ascii=False)
        
        content = f'''
        <div class="info-box">
            <strong>📋 Лабораторна робота №2:</strong> Оберіть 2 евристики для звуження підмножини жанрів. 
            Перетягніть або клікніть. Обрані евристики можна перетягувати між собою.
        </div>
        
        <div class="heuristics-container">
            <div class="heuristics-list" id="heuristicList"></div>
            <div class="priority-panel">
                <div class="priority-title">🎯 Обрані евристики</div>
                <div class="priority-slots">
                    <div class="priority-slot" id="slot1" data-slot="1"><span class="slot-num">1</span><span class="slot-content">Перетягніть сюди</span></div>
                    <div class="priority-slot" id="slot2" data-slot="2"><span class="slot-num">2</span><span class="slot-content">Перетягніть сюди</span></div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button id="submitBtn" disabled>Відправити вибір</button>
            <div id="result" class="result-box"></div>
        </div>
        
        <div class="links">
            <a href="/results">📊 Результати Лаб №1</a>
            <a href="/heuristic-votes">📋 Протокол евристик</a>
            <a href="/rankings">🎯 Ранжування 10 об'єктів</a>
        </div>
        
        <style>
            .heuristics-container {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px; }}
            .heuristics-list {{ display: flex; flex-direction: column; gap: 10px; }}
            .heuristic-item {{ background: #f7fafc; padding: 15px; border-radius: 8px; border: 2px solid #e2e8f0; cursor: grab; }}
            .heuristic-item.in-priority {{ display: none; }}
            .heuristic-id {{ font-weight: bold; color: #5a67d8; margin-right: 8px; }}
            .priority-panel {{ background: #fffaf0; padding: 20px; border-radius: 8px; border: 2px solid #ed8936; }}
            .priority-slot {{ background: white; border: 2px dashed #cbd5e0; border-radius: 6px; padding: 15px; min-height: 80px; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
            .priority-slot.filled {{ border-style: solid; border-color: #48bb78; background: #f0fff4; cursor: grab; }}
            .priority-slot .slot-num {{ font-size: 1.2rem; font-weight: bold; color: #5a67d8; }}
            .controls {{ text-align: center; margin-top: 20px; }}
            .result-box {{ margin-top: 15px; padding: 15px; border-radius: 6px; display: none; }}
        </style>
        
        <script>
            const heuristics = {heuristics_json};
            let selected = [null, null];
            
            const list = document.getElementById('heuristicList');
            heuristics.forEach(h => {{
                const div = document.createElement('div');
                div.className = 'heuristic-item';
                div.draggable = true;
                div.dataset.id = h.id;
                div.innerHTML = `<span class="heuristic-id">${{h.id}}</span><span>${{h.name}}</span><div style="font-size:0.85em;color:#666;margin-top:4px;">${{h.desc}}</div>`;
                div.addEventListener('click', () => selectHeuristic(h.id));
                div.addEventListener('dragstart', (e) => {{ e.dataTransfer.setData('id', h.id); e.dataTransfer.setData('source', 'list'); div.style.opacity = '0.5'; }});
                div.addEventListener('dragend', () => div.style.opacity = '1');
                list.appendChild(div);
            }});
            
            document.querySelectorAll('.priority-slot').forEach(slot => {{
                slot.addEventListener('dragover', (e) => e.preventDefault());
                slot.addEventListener('drop', (e) => {{
                    const id = e.dataTransfer.getData('id');
                    const source = e.dataTransfer.getData('source');
                    const slotNum = parseInt(slot.dataset.slot);
                    
                    if (source === 'list') placeInSlot(id, slotNum);
                    else if (source === 'slot') {{
                        const fromSlot = parseInt(e.dataTransfer.getData('fromSlot'));
                        swapSlots(fromSlot, slotNum);
                    }}
                }});
                slot.addEventListener('dragstart', (e) => {{
                    if (!slot.classList.contains('filled')) return;
                    e.dataTransfer.setData('fromSlot', slot.dataset.slot);
                    e.dataTransfer.setData('source', 'slot');
                    slot.style.opacity = '0.5';
                }});
                slot.addEventListener('dragend', () => slot.style.opacity = '1');
            }});
            
            function selectHeuristic(id) {{
                if (selected.includes(id)) return;
                if (!selected[0]) placeInSlot(id, 1);
                else if (!selected[1]) placeInSlot(id, 2);
                else placeInSlot(id, 2);
            }}
            
            function placeInSlot(id, slotNum) {{
                const otherIdx = slotNum === 1 ? 1 : 0;
                if (selected[otherIdx] === id) selected[otherIdx] = null;
                selected[slotNum - 1] = id;
                updateDisplay();
            }}
            
            function swapSlots(from, to) {{
                const temp = selected[from - 1];
                selected[from - 1] = selected[to - 1];
                selected[to - 1] = temp;
                updateDisplay();
            }}
            
            function updateDisplay() {{
                selected.forEach((id, idx) => {{
                    const slot = document.getElementById(`slot${{idx + 1}}`);
                    const content = slot.querySelector('.slot-content');
                    if (id) {{
                        const h = heuristics.find(x => x.id === id);
                        slot.className = 'priority-slot filled';
                        slot.draggable = true;
                        content.innerHTML = `<span class="heuristic-id">${{h.id}}</span> ${{h.name}}`;
                    }} else {{
                        slot.className = 'priority-slot';
                        slot.draggable = false;
                        content.textContent = 'Перетягніть сюди';
                    }}
                }});
                document.querySelectorAll('.heuristic-item').forEach(item => {{
                    item.classList.toggle('in-priority', selected.includes(item.dataset.id));
                }});
                document.getElementById('submitBtn').disabled = !(selected[0] && selected[1]);
            }}
            
            document.getElementById('submitBtn').addEventListener('click', async () => {{
                const btn = document.getElementById('submitBtn');
                btn.disabled = true;
                try {{
                    const response = await fetch('/vote-heuristic', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ h1: selected[0], h2: selected[1] }})
                    }});
                    const result = await response.json();
                    const resDiv = document.getElementById('result');
                    if (result.success) {{
                        resDiv.innerHTML = `✅ Вибір #${{result.count}} збережено!`;
                        resDiv.style.cssText = 'display:block;background:#c6f6d5;color:#22543d;';
                        selected = [null, null];
                        updateDisplay();
                    }} else throw new Error(result.error);
                }} catch (e) {{
                    document.getElementById('result').textContent = '❌ ' + e.message;
                    document.getElementById('result').style.cssText = 'display:block;background:#fed7d7;color:#c53030;';
                }}
                btn.disabled = false;
            }});
        </script>
        '''
        
        html = html_template("Лаб №2 — Вибір евристик", content)
        self.wfile.write(html.encode('utf-8'))
    
    def _save_heuristic_vote(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        h1, h2 = post_data.get('h1'), post_data.get('h2')
        
        valid_ids = [h['id'] for h in HEURISTICS]
        if h1 not in valid_ids or h2 not in valid_ids or h1 == h2:
            self._send_json({"error": "Невірний вибір"})
            return
        
        try:
            db = get_db()
            collection = db.heuristic_votes
            count = collection.count_documents({})
            
            collection.insert_one({
                "num": count + 1,
                "h1": h1,
                "h2": h2,
                "time": datetime.now().isoformat()
            })
            
            self._send_json({"success": True, "count": count + 1})
        except Exception as e:
            self._send_json({"error": str(e)})
    
    def _show_heuristic_protocol(self):
        try:
            db = get_db()
            votes = list(db.heuristic_votes.find({}, {'_id': 0}).sort("num", -1))
            
            counts = {h['id']: 0 for h in HEURISTICS}
            for v in votes:
                counts[v['h1']] += 1
                counts[v['h2']] += 1
            
            ranking = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        except:
            votes = []
            ranking = []
        
        content = f'''
        <h3>🏆 Рейтинг евристик</h3>
        <div class="ranking">
            {''.join([f'<div class="rank-item"><span>{k}</span><strong>{v} голосів</strong></div>' for k, v in ranking])}
        </div>
        
        <h3>🗳️ Всі голоси ({len(votes)})</h3>
        <table>
            <thead><tr><th>№</th><th>Пріоритет 1</th><th>Пріоритет 2</th><th>Час</th></tr></thead>
            <tbody>
                {''.join([f'<tr><td>{v["num"]}</td><td><strong>{v["h1"]}</strong></td><td><strong>{v["h2"]}</strong></td><td>{v["time"][:19]}</td></tr>' for v in votes])}
            </tbody>
        </table>
        
        <div class="links"><a href="/">← На головну</a></div>
        
        <style>
            .ranking {{ background: #e6fffa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
            .rank-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #b2f5ea; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #5a67d8; color: white; }}
        </style>
        '''
        
        html = html_template("Протокол евристик", content)
        self.wfile.write(html.encode('utf-8'))
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
