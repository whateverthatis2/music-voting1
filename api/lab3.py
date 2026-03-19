from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
from .utils import html_template, get_db, GENRES
import json
from itertools import permutations
import random

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/lab3':
            self._show_main()
        elif path == '/lab3/matrix':
            self._show_matrix()
        elif path == '/lab3/bruteforce':
            self._brute_force()
        elif path == '/lab3/genetic':
            self._genetic_algorithm()
        else:
            self.send_error(404)
    
    def _show_main(self):
        content = """
        <h2>📊 Лабораторна робота №3</h2>
        <div class="info-box">
            <strong>Мета:</strong> Визначення колективного ранжування об'єктів
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px">
            <a href="/lab3/matrix" style="padding:20px;background:#5a67d8;color:white;text-align:center;border-radius:8px;text-decoration:none">
                <h3>📋 Матриця переваг</h3>
            </a>
            <a href="/lab3/bruteforce" style="padding:20px;background:#48bb78;color:white;text-align:center;border-radius:8px;text-decoration:none">
                <h3>🔄 Прямий перебір</h3>
            </a>
            <a href="/lab3/genetic" style="padding:20px;background:#ed8936;color:white;text-align:center;border-radius:8px;text-decoration:none">
                <h3>🧬 Генетичний алгоритм</h3>
            </a>
            <a href="/" style="padding:20px;background:#718096;color:white;text-align:center;border-radius:8px;text-decoration:none">
                <h3>← На головну</h3>
            </a>
        </div>
        """
        self._send(html_template("Лаб №3", content))
    
    def _show_matrix(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
            
            # Отримуємо ядро лідерів з Лаб 2
            leaders = self._get_leaders_from_lab2(db)
            
            # Будуємо матрицю
            matrix = self._build_preference_matrix(votes, leaders)
            
            # Формуємо HTML
            rows = ""
            for i, genre1 in enumerate(leaders):
                row = f"<tr><td><strong>{genre1}</strong></td>"
                for j, genre2 in enumerate(leaders):
                    if i == j:
                        row += f"<td>-</td>"
                    else:
                        count = matrix.get((genre1, genre2), 0)
                        color = "#c6f6d5" if count > len(votes)/2 else "#fed7d7"
                        row += f"<td style='background:{color}'>{count}</td>"
                row += "</tr>"
                rows += row
            
            content = f"""
            <h2>📋 Матриця попарних переваг</h2>
            <p>Кожен елемент показує, скільки експертів віддали перевагу рядку над стовпцем</p>
            <table style='width:100%;border-collapse:collapse;margin:20px 0'>
                <thead><tr><th>А vs B</th>{''.join([f'<th>{g}</th>' for g in leaders])}</tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div class="links">
                <a href="/lab3">← Назад</a>
                <a href="/lab3/bruteforce">→ Прямий перебір</a>
            </div>
            """
            self._send(html_template("Матриця переваг", content))
        except Exception as e:
            self._send(html_template("Помилка", f"<p class='error'>{str(e)}</p>"))
    
    def _get_leaders_from_lab2(self, db):
        # Отримуємо результати Лаб 1
        scores = {g: 0 for g in GENRES}
        votes = list(db.votes.find({}, {'_id': 0}))
        
        for v in votes:
            prefs = v.get('preferences', [])
            if len(prefs) > 0: scores[prefs[0]] += 3
            if len(prefs) > 1: scores[prefs[1]] += 2
            if len(prefs) > 2: scores[prefs[2]] += 1
        
        # Беремо топ-10 (або менше, якщо застосовували евристики)
        sorted_genres = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        leaders = [g for g, s in sorted_genres if s > 0][:10]
        return leaders
    
    def _build_preference_matrix(self, votes, leaders):
        matrix = {}
        for v in votes:
            prefs = v.get('preferences', [])
            # Для кожної пари в преференціях
            for i in range(len(prefs)):
                for j in range(i+1, len(prefs)):
                    a, b = prefs[i], prefs[j]
                    if a in leaders and b in leaders:
                        matrix[(a, b)] = matrix.get((a, b), 0) + 1
        return matrix
    
    def _cook_distance(self, ranking, expert_prefs, leaders):
        """Відстань Кука між ранжуванням та експертним вибором"""
        dist = 0
        ranks = {g: i for i, g in enumerate(ranking)}
        
        for pref in expert_prefs:
            if len(pref) >= 3:
                a, b, c = pref[0], pref[1], pref[2]
                if a in ranks and b in ranks and c in ranks:
                    # Перевіряємо порядок
                    if not (ranks[a] < ranks[b] < ranks[c]):
                        dist += 1
        return dist
    
    def _brute_force(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
            leaders = self._get_leaders_from_lab2(db)
            
            if len(leaders) > 10:
                self._send(html_template("Помилка", 
                    f"<p>Занадто багато об'єктів: {len(leaders)}. Застосуйте евристики з Лаб 2!</p>"))
                return
            
            best_ranking = None
            best_sum = float('inf')
            all_perms = list(permutations(leaders))
            
            results = []
            for perm in all_perms:
                total_dist = 0
                for v in votes:
                    prefs = [v.get('preferences', [])]
                    total_dist += self._cook_distance(perm, prefs, leaders)
                
                results.append((perm, total_dist))
                if total_dist < best_sum:
                    best_sum = total_dist
                    best_ranking = perm
            
            # Сортуємо результати
            results.sort(key=lambda x: x[1])
            
            # Формуємо таблицю топ-10
            rows = ""
            for i, (perm, dist) in enumerate(results[:10]):
                rows += f"<tr><td>{i+1}</td><td>{' → '.join(perm)}</td><td>{dist}</td></tr>"
            
            content = f"""
            <h2>🔄 Прямий перебір ({len(all_perms)} перестановок)</h2>
            <div class="info-box">
                <strong>Найкраще ранжування:</strong><br>
                {'<br>'.join([f"{i+1}. {g}" for i, g in enumerate(best_ranking)])}
            </div>
            <h3>Топ-10 перестановок</h3>
            <table><thead><tr><th>№</th><th>Ранжування</th><th>Сума відстаней</th></tr></thead><tbody>{rows}</tbody></table>
            <div class="links">
                <a href="/lab3">← Назад</a>
                <a href="/lab3/genetic">→ Генетичний алгоритм</a>
            </div>
            """
            self._send(html_template("Прямий перебір", content))
        except Exception as e:
            self._send(html_template("Помилка", f"<p class='error'>{str(e)}</p>"))
    
    def _genetic_algorithm(self):
        try:
            db = get_db()
            votes = list(db.votes.find({}, {'_id': 0}))
            leaders = self._get_leaders_from_lab2(db)
            
            # Параметри ГА
            POP_SIZE = 20
            GENERATIONS = 50
            MUTATION_RATE = 0.3
            
            # Ініціалізація популяції
            population = [list(leaders) for _ in range(POP_SIZE)]
            for p in population:
                random.shuffle(p)
            
            def fitness(ranking):
                total = 0
                for v in votes:
                    prefs = [v.get('preferences', [])]
                    total += self._cook_distance(ranking, prefs, leaders)
                return total
            
            best_ever = None
            best_ever_fit = float('inf')
            
            for gen in range(GENERATIONS):
                # Оцінка
                fits = [fitness(p) for p in population]
                
                # Зберігаємо найкращого
                best_idx = fits.index(min(fits))
                if fits[best_idx] < best_ever_fit:
                    best_ever_fit = fits[best_idx]
                    best_ever = population[best_idx].copy()
                
                # Селекція (турнірна)
                new_pop = [population[best_idx].copy()]  # Еліта
                while len(new_pop) < POP_SIZE:
                    t1, t2 = random.sample(range(POP_SIZE), 2)
                    parent = population[t1 if fits[t1] < fits[t2] else t2].copy()
                    
                    # Мутація
                    if random.random() < MUTATION_RATE:
                        i, j = random.sample(range(len(parent)), 2)
                        parent[i], parent[j] = parent[j], parent[i]
                    
                    new_pop.append(parent)
                
                population = new_pop
            
            content = f"""
            <h2>🧬 Генетичний алгоритм</h2>
            <div class="info-box">
                <strong>Параметри:</strong><br>
                Розмір популяції: {POP_SIZE}<br>
                Поколінь: {GENERATIONS}<br>
                Ймовірність мутації: {MUTATION_RATE}
            </div>
            <div class="info-box" style="background:#c6f6d5">
                <strong>Результат ГА:</strong><br>
                {'<br>'.join([f"{i+1}. {g}" for i, g in enumerate(best_ever)])}<br>
                <strong>Фітнес: {best_ever_fit}</strong>
            </div>
            <div class="links">
                <a href="/lab3">← Назад</a>
                <a href="/lab3/bruteforce">← Прямий перебір</a>
            </div>
            """
            self._send(html_template("Генетичний алгоритм", content))
        except Exception as e:
            self._send(html_template("Помилка", f"<p class='error'>{str(e)}</p>"))
    
    def _send(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
