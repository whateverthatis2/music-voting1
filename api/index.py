from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from .utils import html_template, HEURISTICS, get_db
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/heuristic-votes':
            self._show_heuristic_protocol()
        else:
            self._show_heuristics()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/vote-heuristic':
            self._save_heuristic_vote()
        else:
            self.send_error(404)

    def _show_heuristics(self):
        heuristics_json = json.dumps(HEURISTICS, ensure_ascii=False)
        content = f"""
        <div class="info-box"><strong>Лаб №2:</strong> Оберіть 2 евристики. Перетягніть або клікніть.</div>
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px">
            <div id="heuristicList" style="display:flex;flex-direction:column;gap:10px"></div>
            <div style="background:#fffaf0;padding:20px;border:2px solid #ed8936;border-radius:8px">
                <div style="font-weight:bold;margin-bottom:10px">Обрані</div>
                <div id="slot1" data-slot="1" style="border:2px dashed #ccc;padding:15px;margin-bottom:10px;min-height:50px">1</div>
                <div id="slot2" data-slot="2" style="border:2px dashed #ccc;padding:15px;min-height:50px">2</div>
            </div>
        </div>
        <div style="margin-top:20px;text-align:center">
            <button id="submitBtn" disabled>Відправити</button>
            <div id="result" style="margin-top:10px"></div>
        </div>
        <div style="margin-top:20px">
            <a href="/results">Результати Лаб 1</a> | 
            <a href="/heuristic-votes">Протокол евристик</a> | 
            <a href="/rankings">Ранжування 10 об'єктів</a>
        </div>
        <script>
        const heuristics = {heuristics_json};
        let selected = [null, null];
        const list = document.getElementById('heuristicList');
        heuristics.forEach(h => {{
            const div = document.createElement('div');
            div.className = 'heuristic-item';
            div.draggable = true;
            div.style = "background:#f7fafc;padding:10px;border:1px solid #ddd;cursor:grab";
            div.innerHTML = `<b>${{h.id}}</b> ${{h.name}}`;
            div.onclick = () => select(h.id);
            div.ondragstart = (e) => {{ e.dataTransfer.setData('id', h.id); e.dataTransfer.setData('src', 'list'); }};
            list.appendChild(div);
        }});
        ['slot1','slot2'].forEach(id => {{
            const slot = document.getElementById(id);
            slot.ondragover = e => e.preventDefault();
            slot.ondrop = (e) => {{
                e.preventDefault();
                const src = e.dataTransfer.getData('src');
                const toSlot = parseInt(slot.dataset.slot);
                if(src === 'list') place(e.dataTransfer.getData('id'), toSlot);
                else {{
                    const from = parseInt(e.dataTransfer.getData('from'));
                    swap(from, toSlot);
                }}
            }};
            slot.ondragstart = (e) => {{
                if(!slot.dataset.filled) return;
                e.dataTransfer.setData('from', slot.dataset.slot);
                e.dataTransfer.setData('src', 'slot');
            }};
        }});
        function select(id) {{
            if(selected.includes(id)) return;
            if(!selected[0]) place(id, 1); else place(id, 2);
        }}
        function place(id, slotNum) {{
            if(selected[0]===id) selected[0]=null;
            if(selected[1]===id) selected[1]=null;
            selected[slotNum-1] = id;
            update();
        }}
        function swap(from, to) {{
            const temp = selected[from-1];
            selected[from-1] = selected[to-1];
            selected[to-1] = temp;
            update();
        }}
        function update() {{
            selected.forEach((id, i) => {{
                const slot = document.getElementById(`slot${{i+1}}`);
                if(id) {{
                    const h = heuristics.find(x=>x.id===id);
                    slot.innerHTML = `<b>${{h.id}}</b> ${{h.name}}`;
                    slot.style.border = "2px solid #48bb78";
                    slot.style.background = "#f0fff4";
                    slot.dataset.filled = "true";
                }} else {{
                    slot.innerHTML = i+1;
                    slot.style.border = "2px dashed #ccc";
                    slot.style.background = "white";
                    delete slot.dataset.filled;
                }}
            }});
            document.getElementById('submitBtn').disabled = !(selected[0] && selected[1]);
        }}
        document.getElementById('submitBtn').onclick = async () => {{
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            try {{
                const res = await fetch('/vote-heuristic', {{
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({{h1: selected[0], h2: selected[1]}})
                }});
                const data = await res.json();
                if(data.success) {{
                    document.getElementById('result').innerHTML = '<span class="success">✅ Збережено!</span>';
                    selected = [null, null]; update();
                }} else {{
                    document.getElementById('result').innerHTML = '<span class="error">❌ '+data.error+'</span>';
                    btn.disabled = false;
                }}
            }} catch(e) {{
                document.getElementById('result').innerHTML = '<span class="error">❌ Помилка</span>';
                btn.disabled = false;
            }}
        }};
        </script>
        """
        self._send_html(html_template("Вибір евристик", content))

    def _save_heuristic_vote(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode())
            h1, h2 = data.get('h1'), data.get('h2')
            if h1 == h2: raise Exception("Оберіть різні")
            
            db = get_db()
            count = db.heuristic_votes.count_documents({})
            db.heuristic_votes.insert_one({
                "num": count + 1, "h1": h1, "h2": h2, 
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
            
            rows = "".join([f"<tr><td>{v['num']}</td><td>{v['h1']}</td><td>{v['h2']}</td><td>{v['time'][:19]}</td></tr>" for v in votes])
            rank_rows = "".join([f"<div>{k}: <b>{v} голосів</b></div>" for k,v in ranking])
            
            content = f"""
            <h3>Рейтинг евристик</h3><div style="background:#e6fffa;padding:10px;margin-bottom:20px">{rank_rows}</div>
            <table><thead><tr><th>№</th><th>1</th><th>2</th><th>Час</th></tr></thead><tbody>{rows}</tbody></table>
            <a href="/">← Назад</a>
            """
            self._send_html(html_template("Протокол евристик", content))
        except Exception as e:
            self._send_html(html_template("Помилка", f"<p class='error'>{e}</p><a href='/'>Назад</a>"))

    def _send_html(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
