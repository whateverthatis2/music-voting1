from http.server import BaseHTTPRequestHandler
import json
from .utils import load_db, HEURISTICS, STUDENT_IDS

# Сховище голосів за евристики (в пам'яті для простоти)
heuristic_votes = {}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Формуємо список евристик для JS
        heuristics_json = json.dumps(HEURISTICS, ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вибір евристик | Лаб. №2</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 1.5rem;
            margin-bottom: 10px;
            color: #333;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }}
        .container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .panel {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            min-height: 300px;
        }}
        .panel-title {{
            font-weight: bold;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ddd;
        }}
        .panel-1 .panel-title {{ border-color: #ffd700; }}
        .panel-2 .panel-title {{ border-color: #c0c0c0; }}
        
        .heuristic-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .heuristic-item {{
            background: #f0f0f0;
            padding: 12px;
            border-radius: 6px;
            cursor: grab;
            border: 2px solid transparent;
            transition: all 0.2s;
        }}
        .heuristic-item:hover {{
            background: #e8e8e8;
        }}
        .heuristic-item.dragging {{
            opacity: 0.5;
        }}
        .heuristic-item.selected {{
            border-color: #5a67d8;
            background: #e0e7ff;
        }}
        .heuristic-item.in-priority {{
            background: #c6f6d5;
        }}
        .heuristic-id {{
            font-weight: bold;
            color: #5a67d8;
            margin-right: 8px;
        }}
        .heuristic-name {{
            font-size: 0.95rem;
        }}
        .heuristic-desc {{
            font-size: 0.8rem;
            color: #666;
            margin-top: 4px;
        }}
        
        .priority-slots {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 200px;
        }}
        .priority-slot {{
            border: 2px dashed #ccc;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            color: #999;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}
        .priority-slot.filled {{
            border-style: solid;
            border-color: #5a67d8;
            background: #f0f4ff;
            color: #333;
        }}
        .priority-slot .slot-number {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #5a67d8;
            margin-bottom: 5px;
        }}
        
        .controls {{
            margin-top: 20px;
            text-align: center;
        }}
        button {{
            background: #5a67d8;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
        }}
        button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .result {{
            margin-top: 15px;
            padding: 15px;
            border-radius: 6px;
            display: none;
        }}
        .result.success {{
            background: #c6f6d5;
            display: block;
        }}
        .result.error {{
            background: #fed7d7;
            display: block;
        }}
        .voted-list {{
            margin-top: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
        }}
        .voted-list h3 {{
            margin-bottom: 10px;
        }}
        .vote-entry {{
            padding: 8px;
            border-bottom: 1px solid #eee;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <h1>Вибір евристик звуження</h1>
    <p class="subtitle">Оберіть 2 евристики для відсіювання жанрів (перетягніть або клікніть)</p>
    
    <div class="container">
        <div class="panel">
            <div class="panel-title">📋 Доступні евристики</div>
            <div class="heuristic-list" id="heuristicList">
                <!-- Заповнюється JS -->
            </div>
        </div>
        
        <div class="panel">
            <div class="panel-title">🎯 Обрані пріоритети</div>
            <div class="priority-slots">
                <div class="priority-slot" id="slot1" data-slot="1">
                    <span class="slot-number">1</span>
                    <span>Перетягніть сюди</span>
                </div>
                <div class="priority-slot" id="slot2" data-slot="2">
                    <span class="slot-number">2</span>
                    <span>Перетягніть сюди</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="controls">
        <select id="expertId">
            <option value="">-- Ваш ID --</option>
            {''.join([f'<option value="{sid}">{sid}</option>' for sid in STUDENT_IDS])}
        </select>
        <br><br>
        <button id="submitBtn" disabled>Відправити</button>
        <div id="result" class="result"></div>
    </div>
    
    <div class="voted-list" id="votedList" style="display:none;">
        <h3>🗳️ Протокол голосування</h3>
        <div id="votesContainer"></div>
    </div>

    <script>
        const heuristics = {heuristics_json};
        let selected = [null, null]; // [перший, другий]
        
        // Ініціалізація списку
        const list = document.getElementById('heuristicList');
        heuristics.forEach(h => {{
            const div = document.createElement('div');
            div.className = 'heuristic-item';
            div.draggable = true;
            div.dataset.id = h.id;
            div.innerHTML = `
                <span class="heuristic-id">${{h.id}}</span>
                <span class="heuristic-name">${{h.name}}</span>
                <div class="heuristic-desc">${{h.desc}}</div>
            `;
            
            // Клік для вибору
            div.addEventListener('click', () => selectHeuristic(h.id));
            
            // Drag and drop
            div.addEventListener('dragstart', (e) => {{
                e.dataTransfer.setData('text/plain', h.id);
                div.classList.add('dragging');
            }});
            div.addEventListener('dragend', () => {{
                div.classList.remove('dragging');
            }});
            
            list.appendChild(div);
        }});
        
        // Drop zones
        document.querySelectorAll('.priority-slot').forEach(slot => {{
            slot.addEventListener('dragover', (e) => e.preventDefault());
            slot.addEventListener('drop', (e) => {{
                e.preventDefault();
                const id = e.dataTransfer.getData('text/plain');
                const slotNum = parseInt(slot.dataset.slot);
                placeHeuristic(id, slotNum);
            }});
            slot.addEventListener('click', () => {{
                if (slot.classList.contains('filled')) {{
                    // При кліку на заповнений слот — звільняємо
                    const slotNum = parseInt(slot.dataset.slot);
                    selected[slotNum - 1] = null;
                    updateDisplay();
                }}
            }});
        }});
        
        function selectHeuristic(id) {{
            // Якщо вже вибраний — ігноруємо
            if (selected.includes(id)) return;
            
            // Шукаємо перший вільний слот
            if (!selected[0]) {{
                placeHeuristic(id, 1);
            }} else if (!selected[1]) {{
                placeHeuristic(id, 2);
            }} else {{
                // Обидва зайняті — замінюємо другий
                placeHeuristic(id, 2);
            }}
        }}
        
        function placeHeuristic(id, slotNum) {{
            // Якщо вже в іншому слоті — переміщуємо
            const otherSlot = slotNum === 1 ? 1 : 0;
            const currentSlot = slotNum - 1;
            
            if (selected[otherSlot] === id) {{
                selected[otherSlot] = null;
            }}
            
            selected[currentSlot] = id;
            updateDisplay();
        }}
        
        function updateDisplay() {{
            // Оновлюємо слоти
            selected.forEach((id, idx) => {{
                const slot = document.getElementById(`slot${{idx + 1}}`);
                if (id) {{
                    const h = heuristics.find(x => x.id === id);
                    slot.className = 'priority-slot filled';
                    slot.innerHTML = `
                        <span class="slot-number">${{idx + 1}}</span>
                        <div>
                            <span class="heuristic-id">${{h.id}}</span>
                            <span>${{h.name}}</span>
                            <div style="font-size:0.8rem;color:#666;margin-top:4px;">${{h.desc}}</div>
                        </div>
                    `;
                }} else {{
                    slot.className = 'priority-slot';
                    slot.innerHTML = `
                        <span class="slot-number">${{idx + 1}}</span>
                        <span>Перетягніть сюди</span>
                    `;
                }}
            }});
            
            // Оновлюємо виділення в списку
            document.querySelectorAll('.heuristic-item').forEach(item => {{
                const id = item.dataset.id;
                if (selected.includes(id)) {{
                    item.classList.add('in-priority');
                }} else {{
                    item.classList.remove('in-priority');
                }}
            }});
            
            // Кнопка відправки
            document.getElementById('submitBtn').disabled = !(selected[0] && selected[1]);
        }}
        
        // Відправка
        document.getElementById('submitBtn').addEventListener('click', async () => {{
            const expertId = document.getElementById('expertId').value;
            if (!expertId) {{
                showResult('Оберіть ваш ID', false);
                return;
            }}
            
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            
            try {{
                const response = await fetch('/vote-heuristic', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        expert_id: expertId,
                        h1: selected[0],
                        h2: selected[1]
                    }})
                }});
                
                const result = await response.json();
                if (result.success) {{
                    showResult('✅ Голос зараховано!', true);
                    loadVotedList();
                }} else {{
                    showResult('❌ ' + result.error, false);
                    btn.disabled = false;
                }}
            }} catch (e) {{
                showResult('❌ Помилка з\'єднання', false);
                btn.disabled = false;
            }}
        }});
        
        function showResult(text, isSuccess) {{
            const r = document.getElementById('result');
            r.textContent = text;
            r.className = 'result ' + (isSuccess ? 'success' : 'error');
        }}
        
        async function loadVotedList() {{
            try {{
                const response = await fetch('/heuristic-results');
                const data = await response.json();
                
                const container = document.getElementById('votesContainer');
                container.innerHTML = data.votes.map(v => `
                    <div class="vote-entry">
                        <strong>${{v.expert}}</strong>: ${{v.h1}} + ${{v.h2}}
                    </div>
                `).join('');
                
                document.getElementById('votedList').style.display = 'block';
            }} catch (e) {{
                console.error('Не вдалося завантажити протокол');
            }}
        }}
        
        // Завантажити протокол при старті
        loadVotedList();
    </script>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
