from http.server import BaseHTTPRequestHandler
from .utils import GENRES, STUDENT_IDS, html_template

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        options = '\n'.join([f'<option value="{g}">{g}</option>' for g in GENRES])
        id_options = '\n'.join([f'<option value="{sid}">{sid}</option>' for sid in STUDENT_IDS])
        
        content = f'''
        <div class="info-box">
            <strong>📋 Інструкція:</strong> Оберіть ваш ID зі списку. 
            Вкажіть рівно 3 жанри у порядку пріоритету (1 - найвищий). 
            Система згенерує хеш для перевірки вашого голосу без розкриття вибору.
        </div>
        
        <form id="voteForm" onsubmit="return submitVote(event)">
            <div class="form-group">
                <label>🔐 Ваш ID (анонімний):</label>
                <select id="studentId" required>
                    <option value="">-- Оберіть ID --</option>
                    {id_options}
                </select>
                <div class="error" id="idError"></div>
            </div>
            
            <div class="priority-section gold">
                <span class="badge gold">🥇 ПЕРШИЙ ПРІОРИТЕТ</span>
                <label>Найважливіший жанр (3 бали):</label>
                <select id="p1" required onchange="checkUnique()">
                    <option value="">-- Оберіть жанр --</option>
                    {options}
                </select>
            </div>
            
            <div class="priority-section silver">
                <span class="badge silver">🥈 ДРУГИЙ ПРІОРИТЕТ</span>
                <label>Другий за важливістю (2 бали):</label>
                <select id="p2" required onchange="checkUnique()">
                    <option value="">-- Оберіть жанр --</option>
                    {options}
                </select>
            </div>
            
            <div class="priority-section bronze">
                <span class="badge bronze">🥉 ТРЕТІЙ ПРІОРИТЕТ</span>
                <label>Третій за важливістю (1 бал):</label>
                <select id="p3" required onchange="checkUnique()">
                    <option value="">-- Оберіть жанр --</option>
                    {options}
                </select>
            </div>
            
            <button type="submit" id="submitBtn">Відправити голос</button>
        </form>
        
        <div class="result-box" id="resultBox">
            <h2>✅ Голос прийнято!</h2>
            <p>Збережіть ваш приватний хеш:</p>
            <div class="hash-box" id="privateHash"></div>
            <p style="font-size: 0.9em; color: #666;">
                Публічний хеш: <code id="publicHash"></code>
            </p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">21</div>
                <div>Експертів</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">20</div>
                <div>Жанрів</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">3</div>
                <div>Пріоритети</div>
            </div>
        </div>
        
        <div class="links">
            <a href="/results">📊 Результати</a>
            <a href="/protocol" onclick="alert('Потрібен пароль'); return true;">📋 Протокол (захищено)</a>
        </div>
        
        <script>
            function checkUnique() {{
                const p1 = document.getElementById('p1').value;
                const p2 = document.getElementById('p2').value;
                const p3 = document.getElementById('p3').value;
                const values = [p1, p2, p3].filter(v => v);
                const unique = [...new Set(values)];
                if (values.length !== unique.length) {{
                    alert('❌ Жанри не можуть повторюватися!');
                    event.target.value = '';
                }}
            }}
            
            async function submitVote(e) {{
                e.preventDefault();
                const data = {{
                    student_id: document.getElementById('studentId').value,
                    p1: document.getElementById('p1').value,
                    p2: document.getElementById('p2').value,
                    p3: document.getElementById('p3').value
                }};
                
                try {{
                    const response = await fetch('/vote', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        document.getElementById('privateHash').textContent = result.private_hash;
                        document.getElementById('publicHash').textContent = result.public_hash;
                        document.getElementById('resultBox').style.display = 'block';
                        document.getElementById('submitBtn').disabled = true;
                        document.getElementById('idError').style.display = 'none';
                    }} else {{
                        document.getElementById('idError').textContent = result.error;
                        document.getElementById('idError').style.display = 'block';
                    }}
                }} catch (error) {{
                    alert('Помилка: ' + error.message);
                }}
            }}
        </script>
        '''
        
        html = html_template("Експертне опитування", content)

        self.wfile.write(html.encode('utf-8'))
