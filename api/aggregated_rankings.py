from http.server import BaseHTTPRequestHandler
from .utils import get_db, html_template

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        try:
            db = get_db()
            rankings = list(db.rankings.find({}, {'_id': 0}))
        except:
            rankings = []
        
        if len(rankings) < 5:
            html = html_template("Компромісне ранжування", '''
                <div class="error-box">
                    <strong>⚠️ Недостатньо даних</strong><br>
                    Зібрано {} ранжувань, потрібно мінімум 5.<br>
                    <a href="/rankings">← Додати ранжування</a>
                </div>
            '''.format(len(rankings)))
            self.wfile.write(html.encode('utf-8'))
            return
        
        # Метод Борда для агрегування
        objects = ["Фанк", "Рок", "Електронна", "Інді", "Реп", 
                   "R&B/Soul", "Панк", "Транс", "Блюз", "Латино"]
        
        # Підрахунок балів Борда
        scores = {obj: 0 for obj in objects}
        
        for r in rankings:
            for idx, obj in enumerate(r['ranking']):
                # 1-ше місце = 10 балів, 10-те = 1 бал
                points = 10 - idx
                scores[obj] += points
        
        # Сортування
        aggregated = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Таблиця всіх ранжувань
        rankings_rows = ""
        for r in rankings:
            rankings_rows += "<tr>"
            rankings_rows += f"<td>#{r['num']}</td>"
            for obj in objects:
                pos = r['ranking'].index(obj) + 1
                color = "gold" if pos <= 3 else "silver" if pos <= 6 else "#cd7f32"
                rankings_rows += f'<td style="color:{color};font-weight:bold;">{pos}</td>'
            rankings_rows += f"<td>{r['time'][:10]}</td>"
            rankings_rows += "</tr>"
        
        # Компромісне
        agg_rows = ""
        for rank, (obj, score) in enumerate(aggregated, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            agg_rows += f"""
            <tr class="{'top-3' if rank <= 3 else ''}">
                <td>{medal}</td>
                <td><strong>{obj}</strong></td>
                <td>{score}</td>
                <td>{round(score/len(rankings), 1)}</td>
            </tr>"""
        
        content = f'''
        <div class="info-box">
            <strong>📊 Компромісне ранжування:</strong> 
            Метод Борда (10 балів за 1-ше місце, 1 бал за 10-те).
            Зібрано {len(rankings)} ранжувань.
        </div>
        
        <h3>🏆 Компромісний результат</h3>
        <table class="agg-table">
            <thead>
                <tr>
                    <th>Ранг</th>
                    <th>Жанр</th>
                    <th>Сума балів</th>
                    <th>Середній бал</th>
                </tr>
            </thead>
            <tbody>
                {agg_rows}
            </tbody>
        </table>
        
        <h3>📋 Всі ранжування ({len(rankings)})</h3>
        <div class="table-scroll">
            <table class="all-rankings">
                <thead>
                    <tr>
                        <th>№</th>
                        {''.join([f'<th>{o[:4]}</th>' for o in objects])}
                        <th>Дата</th>
                    </tr>
                </thead>
                <tbody>
                    {rankings_rows}
                </tbody>
            </table>
        </div>
        
        <div class="links">
            <a href="/rankings">← Додати ще ранжування</a>
            <a href="/">На головну</a>
        </div>
        
        <style>
            .agg-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 1.1em;
            }}
            .agg-table th, .agg-table td {{
                padding: 15px;
                text-align: left;
                border-bottom: 2px solid #e2e8f0;
            }}
            .agg-table th {{
                background: #5a67d8;
                color: white;
            }}
            .agg-table tr.top-3 {{
                background: #fffbeb;
            }}
            .agg-table tr.top-3 td {{
                font-size: 1.2em;
            }}
            .all-rankings {{
                font-size: 0.85em;
                border-collapse: collapse;
            }}
            .all-rankings th, .all-rankings td {{
                padding: 8px;
                border: 1px solid #ddd;
                text-align: center;
            }}
            .all-rankings th {{
                background: #f7fafc;
            }}
            .table-scroll {{
                overflow-x: auto;
                margin: 20px 0;
            }}
        </style>
        '''
        
        html = html_template("Компромісне ранжування", content)
        self.wfile.write(html.encode('utf-8'))
