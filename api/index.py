from http.server import BaseHTTPRequestHandler
from .utils import GENRES, STUDENT_IDS, html_template, HEURISTICS
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        heuristics_json = json.dumps(HEURISTICS, ensure_ascii=False)
        
        content = f'''
        <div class="info-box">
            <strong>📋 Лабораторна робота №2:</strong> Оберіть 2 евристики для звуження підмножини жанрів. 
            Перетягніть або клікніть для вибору. Обрані евристики можна перетягувати між собою.
        </div>
        
        <div class="heuristics-container">
            <div class="heuristics-list" id="heuristicList">
                <!-- Заповнюється JS -->
            </div>
            
            <div class="priority-panel">
                <div class="priority-title">🎯 Обрані евристики</div>
                <div class="priority-slots">
                    <div class="priority-slot" id="slot1" data-slot="1" draggable="false">
                        <span class="slot-num">1</span>
                        <span class="slot-content">Клікніть або перетягніть</span>
                    </div>
                    <div class="priority-slot" id="slot2" data-slot="2" draggable="false">
                        <span class="slot-num">2</span>
                        <span class="slot-content">Клікніть або перетягніть</span>
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
                grid-template-columns: 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            @media (min-width: 768px) {{
                .heuristics-container {{
                    grid-template-columns: 2fr 1fr;
                }}
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
            .heuristic-item.dragging {{
                opacity: 0.5;
            }}
            .heuristic-item.in-priority {{
                display: none;
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
                padding: 15px;
                min-height: 80px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                position: relative;
            }}
            .priority-slot.filled {{
                border-style: solid;
                border-color: #48bb78;
                background: #f0fff4;
                cursor: grab;
            }}
            .priority-slot.filled.dragging {{
                opacity: 0.5;
            }}
            .priority-slot.drag-over {{
                background: #e0e7ff;
                border-color: #5a67d8;
            }}
            .priority-slot .slot-num {{
                font-size: 1.2rem;
                font-weight: bold;
                color: #5a67d8;
                margin-bottom: 5px;
            }}
            .priority-slot .slot-content {{
                color: #999;
                font-size: 0.9em;
                text-align: center;
            }}
            .priority-slot.filled .slot-content {{
                color: #333;
                font-weight: 600;
            }}
            .priority-slot .heuristic-id {{
                color: #48bb78;
            }}
            .clear-btn {{
                position: absolute;
                top: 5px;
                right: 8px;
                background: #e53e3e;
                color: white;
                border: none;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                font-size: 12px;
                cursor: pointer;
                display: none;
            }}
            .priority-slot.filled:hover .clear-btn {{
                display: block;
            }}
            .controls {{
                text-align: center;
                margin-top: 20px;
            }}
            .result-box {{
                margin-top: 15px;
                padding: 15px;
                border-radius: 6px;
                display: none;
            }}
        </style>
        
        <script>
            const heuristics = {heuristics_json};
            let selected = [null, null]; // [slot1, slot2]
            
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
                
                div.addEventListener('click', () => selectHeuristic(h.id));
                div.addEventListener('dragstart', onDragStart);
                div.addEventListener('dragend', onDragEnd);
                
                list.appendChild(div);
            }});
            
            // Налаштування слотів
            document.querySelectorAll('.priority-slot').forEach(slot => {{
                slot.addEventListener('dragover', onDragOver);
                slot.addEventListener('dragleave', onDragLeave);
                slot.addEventListener('drop', onDrop);
                slot.addEventListener('dragstart', onSlotDragStart);
                slot.addEventListener('dragend', onSlotDragEnd);
            }});
            
            function onDragStart(e) {{
                e.dataTransfer.setData('source', 'list');
                e.dataTransfer.setData('id', this.dataset.id);
                this.classList.add('dragging');
            }}
            
            function onDragEnd() {{
                this.classList.remove('dragging');
                document.querySelectorAll('.priority-slot').forEach(s => s.classList.remove('drag-over'));
            }}
            
            function onSlotDragStart(e) {{
                if (!this.classList.contains('filled')) return;
                e.dataTransfer.setData('source', 'slot');
                e.dataTransfer.setData('fromSlot', this.dataset.slot);
                this.classList.add('dragging');
            }}
            
            function onSlotDragEnd() {{
                this.classList.remove('dragging');
                document.querySelectorAll('.priority-slot').forEach(s => s.classList.remove('drag-over'));
            }}
            
            function onDragOver(e) {{
                e.preventDefault();
                this.classList.add('drag-over');
            }}
            
            function onDragLeave() {{
                this.classList.remove('drag-over');
            }}
            
            function onDrop(e) {{
                e.preventDefault();
                this.classList.remove('drag-over');
                
                const source = e.dataTransfer.getData('source');
                const toSlot = parseInt(this.dataset.slot);
                
                if (source === 'list') {{
                    // Зі списку в слот
                    const id = e.dataTransfer.getData('id');
                    placeFromList(id, toSlot);
                }} else if (source === 'slot') {{
                    // Між слотами
                    const fromSlot = parseInt(e.dataTransfer.getData('fromSlot'));
                    swapSlots(fromSlot, toSlot);
                }}
            }}
            
            function selectHeuristic(id) {{
                if (selected.includes(id)) return;
                
                if (!selected[0]) placeFromList(id, 1);
                else if (!selected[1]) placeFromList(id, 2);
                else placeFromList(id, 2); // Замінити другий
            }}
            
            function placeFromList(id, slotNum) {{
                selected[slotNum - 1] = id;
                updateDisplay();
            }}
            
            function swapSlots(from, to) {{
                const temp = selected[from - 1];
                selected[from - 1] = selected[to - 1];
                selected[to - 1] = temp;
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
                    const content = slot.querySelector('.slot-content');
                    
                    if (id) {{
                        const h = heuristics.find(x => x.id === id);
                        slot.className = 'priority-slot filled';
                        slot.draggable = true;
                        content.innerHTML = `<span class="heuristic-id">${{h.id}}</span> ${{h.name}}`;
                        
                        // Кнопка очищення
                        let clearBtn = slot.querySelector('.clear-btn');
                        if (!clearBtn) {{
                            clearBtn = document.createElement('button');
                            clearBtn.className = 'clear-btn';
                            clearBtn.textContent = '×';
                            clearBtn.onclick = (e) => {{
                                e.stopPropagation();
                                clearSlot(idx + 1);
                            }};
                            slot.appendChild(clearBtn);
                        }}
                    }} else {{
                        slot.className = 'priority-slot';
                        slot.draggable = false;
                        content.textContent = 'Клікніть або перетягніть';
                        
                        const clearBtn = slot.querySelector('.clear-btn');
                        if (clearBtn) clearBtn.remove();
                    }}
                }});
                
                // Оновити список
                document.querySelectorAll('.heuristic-item').forEach(item => {{
                    item.classList.toggle('in-priority', selected.includes(item.dataset.id));
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
                        resDiv.innerHTML = `✅ Вибір #${{result.vote_num}} збережено!<br><strong>${{selected[0]}}</strong> → <strong>${{selected[1]}}</strong>`;
                        resDiv.style.cssText = 'display:block;background:#c6f6d5;color:#22543d;';
                        
                        // Очистити після успіху
                        selected = [null, null];
                        updateDisplay();
                        btn.textContent = 'Відправити вибір';
                    }} else {{
                        throw new Error(result.error);
                    }}
                }} catch (e) {{
                    resDiv.textContent = '❌ ' + e.message;
                    resDiv.style.cssText = 'display:block;background:#fed7d7;color:#c53030;';
                    btn.disabled = false;
                    btn.textContent = 'Відправити вибір';
                }}
            }});
        </script>
        '''
        
        html = html_template("Лабораторна №2 — Вибір евристик", content)
        self.wfile.write(html.encode('utf-8'))
