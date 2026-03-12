from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from .utils import html, HEURISTICS, get_db
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/heuristic-votes':
            self._show_protocol()
        else:
            self._show_heuristics()
    
    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/vote-heuristic':
            self._save_vote()
        else:
            self.send_error(404)
    
    def _show_heuristics(self):
        h_json = json.dumps(HEURISTICS, ensure_ascii=False)
        content = f"""
        <div class="info"><strong>Лаб №2:</strong> Оберіть 2 евристики. Перетягуйте або клікайте.</div>
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px">
            <div id="hList" style="display:flex;flex-direction:column;gap:10px"></div>
            <div style="background:#fffaf0;padding:15px;border:2px solid #ed8936;border-radius:8px">
                <div style="font-weight:bold;margin-bottom:10px">Обрані</div>
                <div id="s1" data-slot="1" style="border:2px dashed #ccc;padding:15px;margin-bottom:10px;min-height:50px;cursor:grab">1</div>
                <div id="s2" data-slot="2" style="border:2px dashed #ccc;padding:15px;min-height:50px;cursor:grab">2</div>
            </div>
        </div>
        <div style="margin-top:20px;text-align:center">
            <button id="btn" disabled>Відправити</button>
            <div id="res" style="margin-top:10px"></div>
        </div>
        <div style="margin-top:20px">
            <a href="/results">Результати Лаб 1</a> | <a href="/heuristic-votes">Протокол</a> | <a href="/rankings">Ранжування 10 + ГА</a>
        </div>
        <script>
        const h={h_json}; let sel=[null,null];
        const list=document.getElementById('hList');
        h.forEach(x=>{{
            const d=document.createElement('div');
            d.className='h-item'; d.draggable=true; d.dataset.id=x.id;
            d.innerHTML=`<b>${{x.id}}</b> ${{x.name}}<div style="font-size:.85em;color:#666">${{x.desc}}</div>`;
            d.onclick=()=>pick(x.id);
            d.ondragstart=e=>{{e.dataTransfer.setData('id',x.id);e.dataTransfer.setData('src','list');d.style.opacity='.5'}};
            d.ondragend=()=>d.style.opacity='1';
            list.appendChild(d);
        }});
        ['s1','s2'].forEach(id=>{{
            const slot=document.getElementById(id);
            slot.ondragover=e=>e.preventDefault();
            slot.ondrop=e=>{{e.preventDefault();
                const src=e.dataTransfer.getData('src'), to=parseInt(slot.dataset.slot);
                if(src==='list') place(e.dataTransfer.getData('id'),to);
                else {{const fr=parseInt(e.dataTransfer.getData('from')); swap(fr,to);}}
            }};
            slot.ondragstart=e=>{{if(!slot.dataset.f) return; e.dataTransfer.setData('from',slot.dataset.slot); e.dataTransfer.setData('src','slot'); slot.style.opacity='.5'}};
            slot.ondragend=()=>slot.style.opacity='1';
        }});
        function pick(id){{if(sel.includes(id))return; if(!sel[0])place(id,1);else place(id,2);}}
        function place(id,sn){{if(sel[sn===1?1:0]===id)sel[sn===1?1:0]=null; sel[sn-1]=id; upd();}}
        function swap(f,t){{const tmp=sel[f-1];sel[f-1]=sel[t-1];sel[t-1]=tmp;upd();}}
        function upd(){{sel.forEach((id,i)=>{{const sl=document.getElementById(`s${{i+1}}`);
            if(id){{const hx=h.find(x=>x.id===id); sl.className='filled'; sl.dataset.f='1'; sl.innerHTML=`<b>${{hx.id}}</b> ${{hx.name}}`;}}
            else {{sl.className=''; delete sl.dataset.f; sl.textContent=i+1;}}
        }}); document.querySelectorAll('.h-item').forEach(it=>it.style.display=sel.includes(it.dataset.id)?'none':'block');
        document.getElementById('btn').disabled=!(sel[0]&&sel[1]);}}
        document.getElementById('btn').onclick=async()=>{{
            const btn=document.getElementById('btn'); btn.disabled=true;
            try{{const r=await fetch('/vote-heuristic',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{h1:sel[0],h2:sel[1]}})}});
            const d=await r.json(); if(d.success){{document.getElementById('res').innerHTML='<span class="success">✅ Збережено #'+d.count+'</span>'; sel=[null,null];upd();}}
            else throw new Error(d.error);}}catch(e){{document.getElementById('res').innerHTML='<span class="error">❌ '+e.message+'</span>';btn.disabled=false;}}
        }};
        </script>"""
        self._send(html("Вибір евристик", content))
    
    def _save_vote(self):
        try:
            ln = int(self.headers.get('Content-Length',0))
            d = json.loads(self.rfile.read(ln).decode())
            h1,h2 = d.get('h1'), d.get('h2')
            if h1==h2 or h1 not in [x['id'] for x in HEURISTICS] or h2 not in [x['id'] for x in HEURISTICS]:
                raise Exception("Невірний вибір")
            db = get_db()
            c = db.heuristic_votes.count_documents({})
            db.heuristic_votes.insert_one({"num":c+1,"h1":h1,"h2":h2,"time":datetime.now().isoformat()})
            self._send_json({"success":True,"count":c+1})
        except Exception as e:
            self._send_json({"error":str(e)})
    
    def _show_protocol(self):
        try:
            db = get_db()
            votes = list(db.heuristic_votes.find({},{'_id':0}).sort("num",-1))
            cnt = {x['id']:0 for x in HEURISTICS}
            for v in votes: cnt[v['h1']]+=1; cnt[v['h2']]+=1
            rank = sorted(cnt.items(), key=lambda x:x[1], reverse=True)
            rows = "".join([f"<tr><td>{v['num']}</td><td>{v['h1']}</td><td>{v['h2']}</td><td>{v['time'][:19]}</td></tr>" for v in votes])
            rrows = "".join([f"<div>{k}: <b>{v} голосів</b></div>" for k,v in rank])
            content = f"<h3>Рейтинг</h3><div style='background:#e6fffa;padding:10px;margin-bottom:15px'>{rrows}</div><table><thead><tr><th>№</th><th>1</th><th>2</th><th>Час</th></tr></thead><tbody>{rows}</tbody></table><a href='/'>← Назад</a>"
            self._send(html("Протокол евристик", content))
        except Exception as e:
            self._send(html("Помилка", f"<p class='error'>{e}</p><a href='/'>Назад</a>"))
    
    def _send(self, html_str):
        self.send_response(200); self.send_header('Content-type','text/html; charset=utf-8'); self.end_headers()
        self.wfile.write(html_str.encode('utf-8'))
    def _send_json(self, d):
        self.send_response(200); self.send_header('Content-type','application/json'); self.end_headers()
        self.wfile.write(json.dumps(d).encode('utf-8'))
