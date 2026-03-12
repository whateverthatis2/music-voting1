from http.server import BaseHTTPRequestHandler
from .utils import get_db, html_template
import random
import copy

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
        
        objects = ["Фанк", "Рок", "Електронна", "Інді", "Реп", 
                   "R&B/Soul", "Панк", "Транс", "Блюз", "Латино"]
        
        # === ГЕНЕТИЧНИЙ АЛГОРИТМ ===
        ga_result, ga_log = genetic_algorithm(rankings, objects, generations=50)
        
        # === МЕТОД БОРДА (для порівняння) ===
        borda_result = borda_method(rankings, objects)
        
        # Таблиця порівняння
        comparison_rows = ""
        for i, (ga_obj, borda_obj) in enumerate(zip(ga_result, borda_result)):
            match = "✓" if ga_obj == borda_obj else "✗"
            comparison_rows += f"""
            <tr>
                <td>{i+1}</td>
                <td><strong>{ga_obj}</strong></td>
                <td>{borda_obj}</td>
                <td>{match}</td>
            </tr>"""
        
        # Лог ГА
        log_html = "<div class='ga-log'><h4>Еволюція ГА:</h4>"
        for gen, fitness in ga_log[::10]:  # Кожне 10-те покоління
            log_html += f"<p>Покоління {gen}: фітнес = {fitness:.2f}</p>"
        log_html += "</div>"
        
        content = f'''
        <div class="info-box">
            <strong>📊 Агрегування методом генетичного алгоритму</strong><br>
            Зібрано {len(rankings)} ранжувань. ГА знайшов оптимальне компромісне ранжування.
        </div>
        
        <h3>🏆 Результат генетичного алгоритму</h3>
        <table class="result-table">
            <thead>
                <tr><th>Ранг</th><th>Жанр (ГА)</th></tr>
            </thead>
            <tbody>
                {''.join([f'<tr class="{"top-3" if i < 3 else ""}"><td>{i+1}</td><td><strong>{obj}</strong></td></tr>' for i, obj in enumerate(ga_result)])}
            </tbody>
        </table>
        
        {log_html}
        
        <h3>📊 Порівняння з методом Борда</h3>
        <table class="compare-table">
            <thead>
                <tr><th>Ранг</th><th>Генетичний алгоритм</th><th>Метод Борда</th><th>Співпадіння</th></tr>
            </thead>
            <tbody>
                {comparison_rows}
            </tbody>
        </table>
        
        <h3>📋 Вихідні ранжування ({len(rankings)})</h3>
        <div class="table-scroll">
            <table class="all-rankings">
                <thead>
                    <tr><th>№</th>{''.join([f'<th>{o[:4]}</th>' for o in objects])}</tr>
                </thead>
                <tbody>
                    {''.join([f"<tr><td>#{r['num']}</td>{''.join([f'<td>{r[chr(39)]ranking[chr(39)].index(o)+1}</td>' for o in objects])}</tr>" for r in rankings])}
                </tbody>
            </table>
        </div>
        
        <div class="links">
            <a href="/rankings">← Додати ще</a>
            <a href="/">На головну</a>
        </div>
        
        <style>
            .result-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .result-table th, .result-table td {{ padding: 15px; border-bottom: 2px solid #e2e8f0; }}
            .result-table th {{ background: #5a67d8; color: white; }}
            .result-table tr.top-3 {{ background: #fffbeb; font-size: 1.2em; }}
            .compare-table {{ width: 100%; margin: 20px 0; border-collapse: collapse; }}
            .compare-table th {{ background: #4c51bf; color: white; padding: 12px; }}
            .compare-table td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: center; }}
            .ga-log {{ background: #f0fff4; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            .all-rankings {{ font-size: 0.8em; }}
            .all-rankings td, .all-rankings th {{ padding: 6px; border: 1px solid #ddd; text-align: center; }}
            .table-scroll {{ overflow-x: auto; }}
        </style>
        '''
        
        html = html_template("Генетичний алгоритм — агрегування", content)
        self.wfile.write(html.encode('utf-8'))

# === ГЕНЕТИЧНИЙ АЛГОРИТМ ===
def genetic_algorithm(rankings, objects, generations=50, population_size=20):
    """
    ГА для знаходження компромісного ранжування
    Хромосома: перестановка 10 об'єктів
    Фітнес: узгодженість з експертними ранжуваннями (Кендалл тау або співпадіння позицій)
    """
    
    def fitness(individual):
        # Сума відстаней Кендалла до всіх експертних ранжувань
        total_score = 0
        for expert_ranking in rankings:
            # Чим менше відстань, тим краще
            distance = kendall_distance(individual, expert_ranking['ranking'])
            total_score += 1 / (1 + distance)  # Нормування
        return total_score
    
    def kendall_distance(rank1, rank2):
        # Кількість неузгоджених пар
        distance = 0
        for i in range(len(rank1)):
            for j in range(i+1, len(rank1)):
                # Позиції в rank2
                pos_i = rank2.index(rank1[i])
                pos_j = rank2.index(rank1[j])
                if (i < j and pos_i > pos_j) or (i > j and pos_i < pos_j):
                    distance += 1
        return distance
    
    # Ініціалізація популяції
    population = []
    for _ in range(population_size):
        ind = objects.copy()
        random.shuffle(ind)
        population.append(ind)
    
    # Додати експертні ранжування в популяцію (елітизм)
    for r in rankings[:3]:
        population.append(r['ranking'].copy())
    
    log = []
    
    # Еволюція
    for gen in range(generations):
        # Оцінка фітнесу
        fitnesses = [fitness(ind) for ind in population]
        best_fitness = max(fitnesses)
        log.append((gen, best_fitness))
        
        # Селекція (турнір)
        new_population = []
        
        # Елітизм: зберегти найкращого
        best_idx = fitnesses.index(best_fitness)
        new_population.append(population[best_idx].copy())
        
        while len(new_population) < population_size:
            # Турнірний вибір батьків
            p1 = tournament_select(population, fitnesses)
            p2 = tournament_select(population, fitnesses)
            
            # Схрещування (PMX)
            child = pmx_crossover(p1, p2)
            
            # Мутація (swap)
            child = mutate(child, rate=0.2)
            
            new_population.append(child)
        
        population = new_population
    
    # Результат
    final_fitnesses = [fitness(ind) for ind in population]
    best_idx = final_fitnesses.index(max(final_fitnesses))
    return population[best_idx], log

def tournament_select(population, fitnesses, k=3):
    """Турнірна селекція"""
    selected = random.sample(range(len(population)), k)
    best = max(selected, key=lambda i: fitnesses[i])
    return population[best]

def pmx_crossover(p1, p2):
    """Частково відображене схрещування для перестановок"""
    size = len(p1)
    cx1, cx2 = sorted(random.sample(range(size), 2))
    
    child = [None] * size
    
    # Копіюємо сегмент з p1
    child[cx1:cx2] = p1[cx1:cx2]
    
    # Заповнюємо решту з p2 з урахуванням відображення
    used = set(child[cx1:cx2])
    for i in list(range(cx2, size)) + list(range(0, cx1)):
        val = p2[i]
        while val in used:
            # Знаходимо відображення
            idx_in_p2 = p2.index(val)
            val = p1[idx_in_p2]
        child[i] = val
        used.add(val)
    
    return child

def mutate(individual, rate=0.2):
    """Мутація обміном двох позицій"""
    if random.random() < rate:
        i, j = random.sample(range(len(individual)), 2)
        individual[i], individual[j] = individual[j], individual[i]
    return individual

# === МЕТОД БОРДА (для порівняння) ===
def borda_method(rankings, objects):
    """Класичний метод Борда для порівняння"""
    scores = {obj: 0 for obj in objects}
    
    for r in rankings:
        for idx, obj in enumerate(r['ranking']):
            points = 10 - idx  # 10 за 1-ше, 1 за 10-те
            scores[obj] += points
    
    return [obj for obj, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
