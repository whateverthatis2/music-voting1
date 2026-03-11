from http.server import BaseHTTPRequestHandler
from .utils import GENRES, STUDENT_IDS, html_template, HEURISTICS
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Формуємо список евристик для JS
        heuristics_json = json.dumps(HEURISTICS, ensure_ascii=False)
        
        content = f'''
        <div class="info-box">
            <strong>📋 Лабораторна робота №2:</strong> Оберіть 2 евристики для звуження підмножини жанрів. 
            Перетягніть або клікніть для вибору.
        </div>
        
        <div class="heuristics-container">
            <div class="heuristics-list" id="heuristicList">
                <!-- Заповнюється JS -->
            </div>
            
            <div class="priority-panel">
                <div class="priority-title">🎯 Обрані евристики</div>
                <div class="priority-slots">
                    <div class="priority-slot" id="slot1" data-slot="1">
                        <span class="slot-num">1</span>
                        <span class="slot-text">Клікніть або перетягніть</span>
                    </div>
                    <div class="priority-slot" id="slot2" data-slot="2">
                        <span class="slot-num">2</span>
                        <span class="slot-text">Клікніть або перетягніть</span>
                    </div>
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
        </div>
        
        <style>
            .heuristics-container {{
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .heuristics-list {{
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .heuristic-item {{
                background: #f7fafc;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #e2e8f0;
                cursor: grab;
                transition: all 0.2s;
            }}
            .heuristic-item:hover {{
                border-color: #5a67d8;
                background: #e0e7ff;
            }}
            .heuristic-item.selected {{
                background: #c6f6d5;
                border-color: #48bb78;
            }}
            .heuristic-item.in-priority {{
                opacity: 0.6;
                pointer-events: none;
            }}
            .heuristic-id {{
                font-weight: bold;
                color: #5a67d8;
                margin-right: 8px;
            }}
            .heuristic-name {{
                font-weight: 600;
            }}
            .heuristic-desc {{
                font-size: 0.85em;
                color: #666;
                margin-top: 5px;
            }}
            .priority-panel {{
                background: #fffaf0;
                padding: 20px;
                border-radius: 8px;
                border: 2px solid #ed8936;
            }}
            .priority-title {{
                font-weight: bold;
                margin-bottom: 15px;
                color: #744210;
            }}
            .priority-slots {{
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            .priority-slot {{
                background: white;
                border: 2px dashed #cbd5e0;
                border-radius: 6px;
                padding: 20px;
                text-align: center;
                min-height: 80px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }}
            .priority-slot.filled {{
                border-style: solid;
                border-color: #48bb78;
                background: #f0fff4;
            }}
            .priority-slot .slot-num {{
                font-size: 1.5rem;
                font-weight: bold;
                color: #5a67d8;
            }}
            .priority-slot .slot-text {{
                color: #999;
                font-size: 0.9em;
            }}
            .priority-slot.filled .slot-text {{
                color: #333;
                font-weight: 600;
            }}
            .heuristics-container {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            @media (min-width: 768px) {{
                .heuristics-container {{
                    grid-template-columns: 2fr 1fr;
                }}
            }}
        </style>
        
        <script>
            const heuristics = {heuristics_json};
            let selected = [null, null];
            
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
                    div.style.opacity = '0.5';
                }});
                div.addEventListener('dragend', () => {{
                    div.style.opacity = '1';
                }});
                
                list.appendChild(div);
            }});
            
            // Drop zones
            document.querySelectorAll('.priority-slot').forEach(slot => {{
                slot.addEventListener('dragover', (e) => e.preventDefault());
                slot.addEventListener('drop', (e) => {{
                    e.preventDefault();
                    const id = e.dataTransfer.getData('text/plain');
                    placeHeuristic(id, parseInt(slot.dataset.slot));
                }});
                slot.addEventListener('click', () => {{
                    if (slot.classList.contains('filled')) {{
                        clearSlot(parseInt(slot.dataset.slot));
                    }}
                }});
            }});
            
            function selectHeuristic(id) {{
                if (selected.includes(id)) return;
                
                if (!selected[0]) placeHeuristic(id, 1);
                else if (!selected[1]) placeHeuristic(id, 2);
                else placeHeuristic(id, 2); // Замінити другий
            }}
            
            function placeHeuristic(id, slotNum) {{
                // Звільнити з іншого слота якщо там є
                const otherIdx = slotNum === 1 ? 1 : 0;
                if (selected[otherIdx] === id) {{
                    selected[otherIdx] = null;
                }}
                
                selected[slotNum - 1] = id;
                updateDisplay();
            }}
            
            function clearSlot(slotNum) {{
                selected[slotNum - 1] = null;
                updateDisplay();
            }}
            
            function updateDisplay() {{
                // Оновити слоти
                selected.forEach((id, idx) => {{
                    const slot = document.getElementById(`slot${{idx + 1}}`);
                    const num = slot.querySelector('.slot-num');
                    const text = slot.querySelector('.slot-text');
                    
                    if (id) {{
                        const h = heuristics.find(x => x.id === id);
                        slot.className = 'priority-slot filled';
                        text.innerHTML = `<span class="heuristic-id">${{h.id}}</span> ${{h.name}}`;
                    }} else {{
                        slot.className = 'priority-slot';
                        text.textContent = 'Клікніть або перетягніть';
                    }}
                }});
                
                // Оновити виділення в списку
                document.querySelectorAll('.heuristic-item').forEach(item => {{
                    const id = item.dataset.id;
                    item.classList.toggle('selected', selected.includes(id));
                    item.classList.toggle('in-priority', selected.includes(id));
                }});
                
                // Кнопка
                document.getElementById('submitBtn').disabled = !(selected[0] && selected[1]);
            }}
            
            // Відправка
            document.getElementById('submitBtn').addEventListener('click', async () => {{
                const btn = document.getElementById('submitBtn');
                btn.disabled = true;
                btn.textContent = 'Відправка...';
                
                try {{
                    const response = await fetch('/vote-heuristic', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ h1: selected[0], h2: selected[1] }})
                    }});
                    
                    const result = await response.json();
                    const resDiv = document.getElementById('result');
                    
                    if (result.success) {{
                        resDiv.innerHTML = '✅ Вибір збережено!<br><strong>' + selected[0] + '</strong> + <strong>' + selected[1] + '</strong>';
                        resDiv.style.display = 'block';
                        resDiv.style.background = '#c6f6d5';
                        resDiv.style.color = '#22543d';
                    }} else {{
                        resDiv.textContent = '❌ ' + result.error;
                        resDiv.style.display = 'block';
                        resDiv.style.background = '#fed7d7';
                        resDiv.style.color = '#c53030';
                        btn.disabled = false;
                        btn.textContent = 'Відправити вибір';
                    }}
                }} catch (e) {{
                    alert('Помилка: ' + e.message);
                    btn.disabled = false;
                    btn.textContent = 'Відправити вибір';
                }}
            }});
        </script>
        '''
        
        html = html_template("Лабораторна №2 — Вибір евристик", content)
        self.wfile.write(html.encode('utf-8'))
