from http.server import BaseHTTPRequestHandler
from .utils import html_template
import json

# 10 об'єктів для ранжування (твої жанри або нові)
RANKING_OBJECTS = [
    "Фанк", "Рок", "Електронна", "Інді", "Реп", 
    "R&B/Soul", "Панк", "Транс", "Блюз", "Латино"
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        objects_json = json.dumps(RANKING_OBJECTS, ensure_ascii=False)
        
        content = f'''
        <div class="info-box">
            <strong>📊 Агрегування ранжувань:</strong> Розташуйте 10 жанрів у порядку пріоритету (від 1 до 10). 
            Перетягуйте для зміни порядку. Потрібно зібрати 5-8 ранжувань для компромісного результату.
        </div>
        
        <div class="ranking-container">
            <div class="objects-pool" id="objectsPool">
                <!-- Початково порожньо, всі в списку ранжування -->
            </div>
            
            <div class="ranking-list" id="rankingList">
                <div class="ranking-title">🎯 Ваше ранжування (перетягайте для зміни порядку)</div>
                <div class="rank-slots" id="rankSlots">
                    <!-- 10 слотів -->
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button id="submitBtn" disabled>Зберегти ранжування</button>
            <button id="clearBtn" style="background:#e53e3e;">Очистити</button>
            <div id="result" class="result-box"></div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="countRankings">0</div>
                <div>Ранжувань зібрано</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">5-8</div>
                <div>Потрібно</div>
            </div>
        </div>
        
        <div class="links">
            <a href="/aggregated-rankings">📋 Компромісне ранжування</a>
            <a href="/">← На головну</a>
        </div>
        
        <style>
            .ranking-container {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .objects-pool {{
                display: none; /* Всі об'єкти одразу в ранжуванні */
            }}
            .ranking-list {{
                background: #fffaf0;
                padding: 20px;
                border-radius: 8px;
                border: 2px solid #ed8936;
            }}
            .ranking-title {{
                font-weight: bold;
                margin-bottom: 15px;
                color: #744210;
            }}
            .rank-slots {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .rank-slot {{
                display: flex;
                align-items: center;
                gap: 15px;
                padding: 12px;
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                cursor: grab;
                transition: all 0.2s;
            }}
            .rank-slot:hover {{
                border-color: #5a67d8;
                background: #f7fafc;
            }}
            .rank-slot.dragging {{
                opacity: 0.5;
                border-color: #5a67d8;
            }}
            .rank-num {{
                width: 30px;
                height: 30px;
                background: #5a67d8;
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                flex-shrink: 0;
            }}
            .rank-slot.top-3 .rank-num {{
                background: #ffd700;
                color: #744210;
            }}
            .rank-slot.top-3 {{
                background: #fffbeb;
                border-color: #ffd700;
            }}
            .object-name {{
                flex-grow: 1;
                font-weight: 500;
            }}
            .controls {{
                text-align: center;
                margin: 20px 0;
                display: flex;
                gap: 10px;
                justify-content: center;
            }}
            .stats {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
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
            const objects = {objects_json};
            let currentRanking = [];
            
            // Ініціалізація — всі об'єкти в списку у випадковому порядку
            function init() {{
                currentRanking = [...objects].sort(() => Math.random() - 0.5);
                renderRanking();
                updateSubmitButton();
            }}
            
            function renderRanking() {{
                const container = document.getElementById('rankSlots');
                container.innerHTML = '';
                
                currentRanking.forEach((obj, idx) => {{
                    const slot = document.createElement('div');
                    slot.className = 'rank-slot' + (idx < 3 ? ' top-3' : '');
                    slot.draggable = true;
                    slot.dataset.index = idx;
                    slot.dataset.object = obj;
                    
                    slot.innerHTML = `
                        <span class="rank-num">${{idx + 1}}</span>
                        <span class="object-name">${{obj}}</span>
                    `;
                    
                    slot.addEventListener('dragstart', onDragStart);
                    slot.addEventListener('dragend', onDragEnd);
                    slot.addEventListener('dragover', onDragOver);
                    slot.addEventListener('drop', onDrop);
                    
                    container.appendChild(slot);
                }});
            }}
            
            let draggedIndex = null;
            
            function onDragStart(e) {{
                draggedIndex = parseInt(this.dataset.index);
                this.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            }}
            
            function onDragEnd() {{
                this.classList.remove('dragging');
                document.querySelectorAll('.rank-slot').forEach(s => s.classList.remove('drag-over'));
            }}
            
            function onDragOver(e) {{
                e.preventDefault();
                this.classList.add('drag-over');
            }}
            
            function onDrop(e) {{
                e.preventDefault();
                this.classList.remove('drag-over');
                
                const targetIndex = parseInt(this.dataset.index);
                if (draggedIndex === targetIndex) return;
                
                // Обмін місцями
                const temp = currentRanking[draggedIndex];
                currentRanking[draggedIndex] = currentRanking[targetIndex];
                currentRanking[targetIndex] = temp;
                
                renderRanking();
            }}
            
            function updateSubmitButton() {{
                document.getElementById('submitBtn').disabled = currentRanking.length !== 10;
            }}
            
            // Очистити
            document.getElementById('clearBtn').addEventListener('click', () => {{
                currentRanking = [];
                renderRanking();
                updateSubmitButton();
            }});
            
            // Відправка
            document.getElementById('submitBtn').addEventListener('click', async () => {{
                if (currentRanking.length !== 10) {{
                    alert('Розташуйте всі 10 об\'єктів!');
                    return;
                }}
                
                const btn = document.getElementById('submitBtn');
                btn.disabled = true;
                btn.textContent = 'Збереження...';
                
                try {{
                    const response = await fetch('/save-ranking', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ ranking: currentRanking }})
                    }});
                    
                    const result = await response.json();
                    const resDiv = document.getElementById('result');
                    
                    if (result.success) {{
                        resDiv.innerHTML = `✅ Ранжування #${{result.count}} збережено!<br><small>${{currentRanking.slice(0,3).join(', ')}}...</small>`;
                        resDiv.style.cssText = 'display:block;background:#c6f6d5;color:#22543d;';
                        document.getElementById('countRankings').textContent = result.count;
                        
                        // Нове випадкове ранжування
                        setTimeout(init, 1500);
                    }} else {{
                        throw new Error(result.error);
                    }}
                }} catch (e) {{
                    resDiv.textContent = '❌ ' + e.message;
                    resDiv.style.cssText = 'display:block;background:#fed7d7;color:#c53030;';
                }}
                
                btn.disabled = false;
                btn.textContent = 'Зберегти ранжування';
            }});
            
            // Завантажити кількість
            async function loadCount() {{
                try {{
                    const response = await fetch('/ranking-count');
                    const data = await response.json();
                    document.getElementById('countRankings').textContent = data.count;
                }} catch (e) {{}}
            }}
            
            init();
            loadCount();
        </script>
        '''
        
        html = html_template("Агрегування ранжувань", content)
        self.wfile.write(html.encode('utf-8'))
