# -*- coding: utf-8 -*-
"""
Точка входу serverless-функції Vercel — Лабораторна №4.

Маршрути:
    /              — огляд лабораторної та підсумкові показники;
    /data          — вхідні дані Лаб.1-2 + матриці п.1.2 та п.1.3;
    /distributed   — схема декомпозиції, розподілений прямий перебір,
                     порівняння з централізованим (= результат Лаб.3);
    /satisfaction  — обране A*/R*, відстані d^j, індекси задоволеності s^j;
    /large         — Ситуація Б (n>>12): випадкові трійки, ГА,
                     порівняння централізованого vs розподіленого;
    /protocol      — захищений паролем журнал подій (POST з паролем);
    /protocol.txt  — текстовий протокол обчислень;
    /healthz       — JSON для перевірки стану сховища.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from . import data as D
from . import templates as T
from . import storage as S
from . import algorithms as A
from . import lab4 as L4
from . import lab5 as L5


# ---------------------------------------------------------------------------
# Кеш обчислень — щоб важкі речі рахувалися один раз на cold-start
# ---------------------------------------------------------------------------
_cache: dict = {}


def _centralized():
    if "cen" not in _cache:
        _cache["cen"] = L4.centralized_enumerate(D.OBJECTS, D.EXPERT_TRIPLES)
    return _cache["cen"]


def _distributed():
    if "dis" not in _cache:
        res = L4.distributed_enumerate(D.OBJECTS, D.EXPERT_TRIPLES, n_workers=4)
        _cache["dis"] = res
        S.save_ranking(
            source="lab4-distributed",
            ranking=res["best_sum_rank"],
            cost=res["best_sum_value"],
            max_d=res["best_max_value"],
            method="distributed_brute_force",
        )
    return _cache["dis"]


def _chosen_compromise():
    """Обране A*/R* — за замовчуванням перша Σ-медіана з розподіленого перебору."""
    if "chosen" not in _cache:
        dis = _distributed()
        ranking = dis["best_sum_rank"]
        rank_vec = A.ranking_to_rank_vector(D.OBJECTS, ranking)
        _cache["chosen"] = {"ranking": ranking, "rank_vec": rank_vec}
    return _cache["chosen"]


def _satisfactions():
    if "sat" not in _cache:
        chosen = _chosen_compromise()
        rows = L4.compute_satisfactions(
            D.EXPERTS, D.EXPERT_TRIPLES_LAB1, chosen["ranking"])
        _cache["sat"] = rows
    return _cache["sat"]


def _ga_suite():
    if "ga" not in _cache:
        _cache["ga"] = L4.ga_comparison_suite()
    return _cache["ga"]


def _ga_demo():
    if "gademo" not in _cache:
        _cache["gademo"] = L4.single_ga_demo()
    return _cache["gademo"]


# ---------------------------------------------------------------------------
# Сторінка /
# ---------------------------------------------------------------------------
def render_home() -> str:
    cen = _centralized()
    dis = _distributed()
    sat = _satisfactions()
    avg_s = sum(r["s"] for r in sat) / len(sat)

    coincide = (cen["best_sum_rank"] == dis["best_sum_rank"]
                and cen["best_sum_value"] == dis["best_sum_value"])

    body = f"""
<div class="card">
  <h2>Постановка задачі</h2>
  <p class="lead">Виконати розподілені обчислення компромісних ранжувань
     об'єктів за результатами преференційного голосування з Лаб.1-2 та
     обчислити індекси задоволеності експертів колективним розв'язком
     (Ситуація А, n = {len(D.OBJECTS)}). Додатково — для n ≫ 12 (Ситуація Б)
     застосувати еволюційний алгоритм у централізованому та розподіленому
     режимах, оцінити час та якість.</p>
  <div class="grid cols-3">
    {T.stat("Об'єктів (повний набір)",   len(D.FULL_OBJECTS))}
    {T.stat("Об'єктів після евристик",   len(D.OBJECTS))}
    {T.stat("Експертів (з викладачем)",  len(D.EXPERTS))}
    {T.stat("Перестановок n!",           f"{cen['n_perm']:,}".replace(",", " "))}
    {T.stat("Σ-медіана", cen["best_sum_value"])}
    {T.stat("Сер. індекс задоволеності", f"{avg_s:.1f}%")}
  </div>
</div>

<div class="card">
  <h2>Колективне ранжування A*</h2>
  {T.ranking_chips(dis["best_sum_rank"])}
  <p class="muted">Σ d (Кук) = <span class="kbd">{dis["best_sum_value"]}</span> ·
     max d = <span class="kbd">{dis["best_max_value"]}</span></p>
  {T.alert(_coincidence_alert(coincide, cen, dis), "ok" if coincide else "warn")}
</div>
"""
    return T.page("Огляд", body, active="home_l4")


def _coincidence_alert(ok: bool, cen, dis) -> str:
    if ok:
        return ("Розподілений прямий перебір збігся з результатом централізованого "
                f"перебору (Лаб.3): Σ d = {cen['best_sum_value']}, "
                "ранжування ідентичне. Декомпозиція коректна.")
    return ("Розбіжність між розподіленим та централізованим результатами — "
            "це не повинно статися при коректній декомпозиції; перевірте код.")


# ---------------------------------------------------------------------------
# Сторінка /data
# ---------------------------------------------------------------------------
def render_data() -> str:
    pmat = A.preference_matrix(D.OBJECTS, D.EXPERT_TRIPLES)
    rmat = A.expanded_rank_matrix(D.OBJECTS, D.EXPERT_TRIPLES)

    triples_rows = []
    for r_idx in range(3):
        triples_rows.append([t[r_idx] for t in D.EXPERT_TRIPLES])
    triple_headers = [str(i + 1) for i in range(len(D.EXPERT_TRIPLES))]

    pmat_headers = [f"o{j+1}" for j in range(len(D.OBJECTS))]
    pmat_rows_lbl = ["1-ше місце", "2-ге місце", "3-тє місце", "Σ згадувань"]
    rmat_headers = [str(i + 1) for i in range(len(D.EXPERT_TRIPLES))]

    obj_chips = "".join(
        f'<span class="rk"><b>o{i+1}</b>{o}</span>'
        for i, o in enumerate(D.OBJECTS)
    )
    exp_chips = "".join(
        f'<span class="e">{e}</span>' for e in D.EXPERTS
    )

    heur_rows = [
        [h["id"], h["name"], h["votes"], h["rule"]] for h in D.HEURISTICS
    ]
    removed_rows = [
        [r["step"], r["heuristic"],
         ", ".join(r["removed"]) if r["removed"] else "—",
         r["left"]]
        for r in D.REMOVED_BY_HEURISTICS
    ]

    # Оригінальні трійки Лаб.1 з підсвіткою видалених евристиками об'єктів
    objects_set = set(D.OBJECTS)
    lab1_rows = []
    for j, (expert, t) in enumerate(zip(D.EXPERTS, D.EXPERT_TRIPLES_LAB1), 1):
        cells = []
        for k, obj in enumerate(t):
            if obj in objects_set:
                cells.append(obj)
            else:
                cells.append(f'<span class="tag red">{obj} ✗</span>')
        lab1_rows.append([j, expert, *cells])

    body = f"""
<div class="card">
  <h2>1. Перелік об'єктів</h2>
  <h3>Повний набір (Лаб.1 — 20 жанрів)</h3>
  <p class="muted">{", ".join(D.FULL_OBJECTS)}</p>
  <h3>Робоча підмножина після евристик Лаб.2 (n = {len(D.OBJECTS)})</h3>
  <div class="ranking">{obj_chips}</div>
</div>

<div class="card">
  <h2>2. Список експертів (20 + викладач)</h2>
  <div class="subexperts">{exp_chips}</div>
</div>

<div class="card">
  <h2>3. Множинні порівняння експертів (звужений набір, n = {len(D.OBJECTS)})</h2>
  <p class="lead">Кожен стовпчик — експерт; рядки — місця 1, 2, 3 у трійці.
     Ці трійки використовуються для обчислення компромісного ранжування
     прямим перебором.</p>
  {T.matrix_table(triple_headers, triples_rows, row_labels=["1", "2", "3"])}
</div>

<div class="card">
  <h2>4. Оригінальні трійки Лаб.1</h2>
  <p class="lead">Трійки до застосування евристик Лаб.2. Об'єкти,
     відмічені <span class="tag red">червоним</span>, видалені евристиками
     і не входять до робочої підмножини. Саме для таких трійок у Лаб.4
     застосовується штраф d<sup>j</sup> = d<sup>l</sup> + (n-3).</p>
  {T.table(["#", "Експерт", "1-ше", "2-ге", "3-тє"], lab1_rows)}
</div>

<div class="card" id="matrix">
  <h2>5. Матриця статистики переваг (п.1.2)</h2>
  <p class="lead">Скільки експертів поставили об'єкт на позиції 1/2/3
     та сумарна кількість згадувань.</p>
  {T.matrix_table(pmat_headers, pmat, row_labels=pmat_rows_lbl)}
</div>

<div class="card">
  <h2>6. Розгорнута матриця рангів (п.1.3)</h2>
  <p class="lead">Рядки — об'єкти; стовпчики — експерти. Значення = ранг
     об'єкта (1, 2, 3) у трійці експерта; 0 — не названо.</p>
  {T.matrix_table(rmat_headers, rmat,
                  row_labels=[f"o{i+1} {o}" for i, o in enumerate(D.OBJECTS)])}
</div>

<div class="card">
  <h2>7. Евристики звуження (Лаб.2)</h2>
  {T.table(["ID", "Назва", "Голоси", "Правило"], heur_rows)}
  <h3>Хід застосування евристик</h3>
  {T.table(["Крок", "Евристика", "Прибрано", "Залишилось"], removed_rows)}
</div>
"""
    return T.page("Дані Лаб.1-2", body, active="data")


# ---------------------------------------------------------------------------
# Сторінка /distributed
# ---------------------------------------------------------------------------
def render_distributed() -> str:
    cen = _centralized()
    dis = _distributed()

    coincide = (cen["best_sum_rank"] == dis["best_sum_rank"]
                and cen["best_sum_value"] == dis["best_sum_value"])

    branches_rows = [
        [b["first"], b["count"],
         b["best_sum"], " › ".join(b["all_best_sum"][0]),
         b["best_max"], " › ".join(b["all_best_max"][0])]
        for b in dis["branches"]
    ]

    speedup_real = round(cen["elapsed"] / max(dis["elapsed"], 0.0001), 2)
    speedup_ideal = dis["n_workers"]

    n = len(D.OBJECTS)
    n_minus_1_fact = L4._factorial(n - 1)

    body = f"""
<div class="card">
  <h2>1. Схема декомпозиції прямого перебору</h2>
  <p class="lead">Декомпозиція за фіксованим першим об'єктом: для кожного
     з n = {n} об'єктів утворюється окрема гілка перебору, в якій цей об'єкт
     стоїть на 1-й позиції, а решта (n−1) = {n - 1} об'єктів переставляються
     всіма можливими способами. Гілки виконуються паралельно
     (ThreadPoolExecutor, {dis["n_workers"]} потоків — по числу віртуальних
     "вузлів" розподіленої системи).</p>

  <h3>Фактично оброблено перестановок</h3>
  <div class="grid cols-3">
    {T.stat("Очікувано n!",   dis["n_factorial_expected"])}
    {T.stat("Перебрано",      dis["n_perm_total"])}
    {T.stat("Гілок",          len(dis["branches"]))}
  </div>
</div>

<div class="card">
  <h2>2. Результат розподіленого перебору по гілках</h2>
  <p class="lead">Кожен рядок — одна гілка декомпозиції. У кожній гілці
     знайдено локальні Σ- та max-медіани; глобальна медіана — мінімум по
     всіх гілках.</p>
  {T.table(
      ["Фікс. 1-й об'єкт", "(n-1)!", "Лок. min Σ d", "Лок. Σ-ранжування",
       "Лок. min max", "Лок. max-ранжування"],
      branches_rows
  )}

  <h3>Глобальне Σ-медіанне ранжування</h3>
  {T.ranking_chips(dis["best_sum_rank"])}
  <p class="muted">Σ d = <span class="kbd">{dis["best_sum_value"]}</span></p>

  <h3>Глобальне max-медіанне ранжування</h3>
  {T.ranking_chips(dis["best_max_rank"])}
  <p class="muted">max d = <span class="kbd">{dis["best_max_value"]}</span></p>

  {_alt_medians_html(dis)}
</div>

<div class="card">
  <h2>3. Порівняння з результатом Лаб.3 (централізований перебір)</h2>
  {T.table(
      ["Метрика", "Централізований (Лаб.3)", "Розподілений (Лаб.4)"],
      [
        ["Σ d (мінімум)",       cen["best_sum_value"], dis["best_sum_value"]],
        ["max d (мінімум)",     cen["best_max_value"], dis["best_max_value"]],
        ["Σ-ранжування",
         " › ".join(cen["best_sum_rank"]),
         " › ".join(dis["best_sum_rank"])],
        ["Перестановок",        cen["n_perm"],         dis["n_perm_total"]],
        ["Час, секунди",        cen["elapsed"],        dis["elapsed"]],
      ]
  )}
  {T.alert(_coincidence_alert(coincide, cen, dis), "ok" if coincide else "warn")}
</div>

<div class="card">
  <h2>4. Аналіз часу обчислень</h2>
  <p class="lead">Реальний speedup на Vercel обмежений GIL (Python-потоки
     серіалізують CPU-навантаження); відображено фактичний час та
     теоретичну верхню межу T_центр / W при ідеальному розпаралелюванні.</p>
  <div class="grid cols-3">
    {T.stat("T централіз., с",    cen["elapsed"])}
    {T.stat("T розподіл., с",     dis["elapsed"])}
    {T.stat("Speedup фактичний",  f"×{speedup_real}")}
    {T.stat("Speedup ідеальний",  f"×{speedup_ideal}")}
    {T.stat("Воркерів W",         dis["n_workers"])}
    {T.stat("T ідеал., с",        round(cen["elapsed"] / speedup_ideal, 4))}
  </div>
  <p class="note">На реальній розподіленій системі (окремі процеси/машини)
     speedup наближається до W; на serverless-Python з GIL — нижчий.</p>
</div>
"""
    return T.page("Розподілений перебір", body, active="distributed")


def _alt_medians_html(dis) -> str:
    if len(dis["all_best_sum"]) <= 1:
        return ""
    extras = "".join(
        f'<div style="margin:6px 0">{T.ranking_chips(r)}</div>'
        for r in dis["all_best_sum"][1:6]
    )
    more = (f'<p class="muted">Усього перестановок з Σ d = {dis["best_sum_value"]}: '
            f'<b>{len(dis["all_best_sum"])}</b></p>')
    return f"<h3>Альтернативні Σ-медіани</h3>{extras}{more}"


# ---------------------------------------------------------------------------
# Сторінка /satisfaction
# ---------------------------------------------------------------------------
def render_satisfaction() -> str:
    chosen = _chosen_compromise()
    sat = _satisfactions()
    n = len(chosen["ranking"])
    max_d = 3 * (n - 3)

    avg_s = sum(r["s"] for r in sat) / len(sat)
    min_s = min(r["s"] for r in sat)
    max_s = max(r["s"] for r in sat)
    n_penalty = sum(1 for r in sat if r["removed"])

    rows = []
    for j, r in enumerate(sat, 1):
        triple_str = " › ".join(
            f'<span class="tag red">{o}</span>' if o in r["removed"]
            else o for o in r["triple"]
        )
        removed_str = (", ".join(r["removed"]) if r["removed"]
                       else '<span class="muted">—</span>')
        rows.append([
            j, r["expert"], triple_str, removed_str,
            r["d_partial"], r["d"],
            f'<b>{r["s"]:.2f}%</b>',
        ])

    rank_vec_table = T.table(
        ["Об'єкт", *D.OBJECTS],
        [["Ранг у A*", *chosen["rank_vec"]]]
    )

    bar = T.bar_chart(
        [(r["expert"].replace("Експерт_", "Е"), r["s"]) for r in sat],
        maximum=100,
    )

    body = f"""
<div class="card">
  <h2>1. Обране компромісне ранжування A* / R*</h2>
  <p class="lead">З множини Σ-медіан вибрано перше ранжування, повернене
     розподіленим перебором (відповідає п.7 завдання — «довільне за власним
     рішенням»). При наявності кількох еквівалентних медіан можна обрати
     будь-яку з них без зміни сумарної якості.</p>
  <h3>Вектор номерів об'єктів A*</h3>
  {T.ranking_chips(chosen["ranking"])}
  <h3>Вектор рангів R* (у вихідному порядку об'єктів)</h3>
  {rank_vec_table}
</div>

<div class="card">
  <h2>2. Відстані та індекси задоволеності експертів</h2>
  <p class="lead">d_part — внесок об'єктів, що залишились після евристик;
     d — повна відстань зі штрафом (n−3) за видалені об'єкти.</p>
  {T.table(
      ["#", "Експерт", "Трійка Лаб.1", "Видалено", "d_part", "d", "s, %"],
      rows
  )}
</div>

<div class="card">
  <h2>3. Підсумкові показники задоволеності</h2>
  <div class="grid cols-3">
    {T.stat("Середній індекс s", f"{avg_s:.2f}%")}
    {T.stat("Мінімальний s",     f"{min_s:.2f}%")}
    {T.stat("Максимальний s",    f"{max_s:.2f}%")}
    {T.stat("Експертів зі штрафом", n_penalty)}
    {T.stat("Експертів без втрат",   len(sat) - n_penalty)}
    {T.stat("Експертів усього",      len(sat))}
  </div>
  <h3>Розподіл індексів по експертах</h3>
  {bar}
</div>
"""
    return T.page("Індекси задоволеності", body, active="satisfaction")


# ---------------------------------------------------------------------------
# Сторінка /large
# ---------------------------------------------------------------------------
def render_large() -> str:
    suite = _ga_suite()
    demo = _ga_demo()

    suite_rows = [
        [r["n_alt"], r["n_exp"],
         f'{r["pop_total"]}/{r["n_gen"]}',
         r["centralized_cost"], f'{r["centralized_time"]}s',
         r["distributed_cost"], f'{r["distributed_time"]}s',
         r["improvement"], f'{r["improvement_pct"]}%']
        for r in suite
    ]

    demo_triples_rows = [
        [k + 1, *t] for k, t in enumerate(demo["triples_preview"])
    ]

    cen = demo["centralized"]
    dis = demo["distributed"]
    cen_history = cen["history"]
    dis_history = dis["history"]

    cen_chart = T.bar_chart(
        [(str(i), v) for i, v in enumerate(cen_history)
         if i % max(1, len(cen_history) // 20) == 0],
        maximum=max(cen_history) if cen_history else 1,
    )
    dis_chart = T.bar_chart(
        [(f"e{i}", v) for i, v in enumerate(dis_history)],
        maximum=max(dis_history) if dis_history else 1,
    )

    avg_improvement = sum(r["improvement"] for r in suite) / len(suite)
    avg_improvement_pct = sum(r["improvement_pct"] for r in suite) / len(suite)

    body = f"""
<div class="card">
  <h2>1. Схема розподіленого ГА для n ≫ 12</h2>
  <p class="lead">При n &gt; 12 прямий перебір n! стає непридатним
     (13! ≈ 6.2·10⁹). Для пошуку компромісу застосовуємо генетичний алгоритм:
     PMX-кросовер, swap-мутація, турнірний відбір. У розподіленому варіанті
     використовується <b>острівна модель</b>: K = 4 незалежні популяції,
     кожна еволюціонує паралельно у власному потоці; між епохами найкращий
     індивід острова мігрує по кільцю на сусідній острів і витісняє там
     найгіршого.</p>
  <div class="code-block">Централізований ГА:    1 популяція × pop_total × n_gen поколінь
Розподілений ГА:        K=4 острови × (pop_total/4) × n_gen, міграція раз на епоху
Однакова сумарна обчислювальна робота → чесне порівняння якості</div>
</div>

<div class="card">
  <h2>2. Згенеровані випадкові трійки (приклад)</h2>
  <p class="lead">Демонстраційна задача: n = {demo["n_alt"]} альтернатив,
     n_exp = {demo["n_exp"]} експертів. Об'єкти позначаються o001…o{demo["n_alt"]:03d};
     кожна трійка — випадкова вибірка 3 об'єктів зі збереженням порядку
     (1-ше / 2-ге / 3-тє місце).</p>
  <p class="muted">Перші 10 об'єктів: {", ".join(demo["objects_preview"])}…</p>
  {T.table(["#", "1-ше", "2-ге", "3-тє"], demo_triples_rows)}
  <p class="note">Далі показано 8 з {demo["n_exp"]} згенерованих трійок.</p>
</div>

<div class="card">
  <h2>3. Прогін на демонстраційній задачі</h2>
  {T.table(
      ["Алгоритм", "Σ d (best)", "Час, с", "Параметри"],
      [
        ["Централізований ГА",
         cen["best_cost"], cen["elapsed"],
         f'pop = {cen["params"]["pop_size"]}, gen = {cen["params"]["n_gen"]}'],
        ["Розподілений ГА (4 острови)",
         dis["best_cost"], dis["elapsed"],
         f'pop_island = {dis["params"]["pop_per_island"]}, '
         f'gen = {dis["params"]["n_gen"]}, '
         f'epochs = {dis["params"]["n_epochs"]}'],
      ]
  )}
  <h3>Збіжність централізованого ГА</h3>
  <p class="muted">По осі X — номер покоління; число у кінці смужки —
     <b>Σ d найкращого розв'язку</b>, знайденого алгоритмом до цього покоління.
     Менше — краще. Однакові підряд значення (наприклад 902 → 902 → 902) означають,
     що в цих поколіннях кращого розв'язку не знайдено; стрибок униз
     (902 → 853) — мутація / схрещування знайшли покращення.</p>
  {cen_chart}
  <h3>Збіжність розподіленого ГА (по епохах)</h3>
  <p class="muted">Те саме, але для острівної моделі — точки відповідають
     епохам (між якими відбувається міграція між островами).</p>
  {dis_chart}
</div>

<div class="card">
  <h2>4. Порівняльна таблиця для сітки задач</h2>
  <p class="lead">Сітка n_alt × n_exp = {{20, 50, 100}} × {{10, 20, 30}}.
     Кожен рядок — одна синтетична задача.
     <br><b>Σ d центр.</b> та <b>Σ d розпод.</b> — мінімальна сумарна відстань
     (компроміс), знайдена централізованим і розподіленим ГА відповідно.
     Менше = кращий компроміс.
     <br><b>T центр.</b> та <b>T розпод.</b> — час роботи (у секундах)
     централізованого та розподіленого ГА відповідно (скільки реально тривало
     обчислення).
     <br><b>Δ якості</b> = (Σ d центр.) − (Σ d розпод.) — наскільки розподілений
     ГА знайшов кращий розв'язок (додатне число — розподілений виграв).
     <b>Покращення %</b> — те саме у відсотках відносно Σ d централізованого.</p>
  {T.table(
      ["n_alt", "n_exp", "pop/gen",
       "Σ d центр.", "T центр.",
       "Σ d розпод.", "T розпод.",
       "Δ якості", "Покращення %"],
      suite_rows
  )}
</div>

<div class="card">
  <h2>5. Висновки за п.14-15 завдання</h2>
  <ul style="margin-left:18px;color:#334155;line-height:1.8">
    <li>Середнє покращення розв'язку острівним ГА відносно централізованого
        ГА (за {len(suite)} прогонами): <b>Δ = {avg_improvement:+.2f}</b>
        (<b>{avg_improvement_pct:+.2f}%</b>).</li>
    <li>Острівна модель краща за централізовану з тим самим бюджетом
        обчислень тому, що зберігає більше різноманіття популяції —
        острови сходяться до різних локальних оптимумів, а міграція
        переносить найкращих між островами.</li>
    <li>На Vercel реальний speedup за часом обмежений GIL Python — потоки
        серіалізують CPU-операції. На системі з окремими процесами / вузлами
        прискорення прямо пропорційне числу вузлів (близько ×K = 4 для
        нашої схеми).</li>
  </ul>
</div>
"""
    return T.page("n ≫ 12 · ГА", body, active="large")


# ---------------------------------------------------------------------------
# Сторінка /protocol
# ---------------------------------------------------------------------------
def render_protocol_form(error: str = "") -> str:
    err_html = T.alert(error, "error") if error else ""
    body = f"""
<div class="card">
  <h2>Конфіденційний протокол обчислень</h2>
  <p class="lead">Перегляд журналу подій, збережених ранжувань та результатів
     розподіленого перебору захищено паролем. Текстову версію протоколу
     можна завантажити одразу: <a href="/protocol.txt">protocol.txt</a>.</p>
  {err_html}
  <form method="POST" action="/protocol" class="inline">
    <input type="password" name="password" placeholder="Пароль" required>
    <button class="btn" type="submit">Увійти</button>
  </form>
</div>
"""
    return T.page("Протокол", body, active="protocol")


def render_protocol_view() -> str:
    rankings = S.load_rankings(50)
    events = S.load_events(50)
    status = S.db_status()

    if status["online"]:
        status_alert = T.alert("Сховище MongoDB активне.", "ok")
    else:
        reason = status.get("reason") or "невідомо"
        status_alert = T.alert(
            f"MongoDB недоступний ({reason}). "
            "Дані пишуться в кеш процесу й будуть втрачені після зупинки інстансу.",
            "warn")

    rk_rows = [
        [r.get("time", "")[:19], r.get("source", ""),
         r.get("method", ""), r.get("cost", ""), r.get("max", ""),
         " › ".join(r.get("ranking", []))]
        for r in rankings
    ] or [["—", "—", "—", "—", "—", "—"]]

    ev_rows = [
        [e.get("time", "")[:19], e.get("type", ""), e.get("message", "")]
        for e in events
    ] or [["—", "—", "журнал порожній"]]

    body = f"""
<div class="card">
  <h2>Стан сховища</h2>
  {status_alert}
  <p><a class="btn secondary" href="/protocol.txt">Завантажити .txt</a></p>
</div>

<div class="card">
  <h2>Збережені колективні ранжування</h2>
  {T.table(["Час", "Джерело", "Метод", "Σ d", "max d", "Ранжування"], rk_rows)}
</div>

<div class="card">
  <h2>Журнал подій</h2>
  {T.table(["Час", "Тип", "Повідомлення"], ev_rows)}
</div>
"""
    return T.page("Протокол", body, active="protocol")


# ---------------------------------------------------------------------------
# Текстовий протокол /protocol.txt
# ---------------------------------------------------------------------------
def render_protocol_txt() -> str:
    cen = _centralized()
    dis = _distributed()
    chosen = _chosen_compromise()
    sat = _satisfactions()
    suite = _ga_suite()

    n = len(D.OBJECTS)
    out: list[str] = []
    P = out.append

    P("=" * 78)
    P("ПРОТОКОЛ ЛАБОРАТОРНОЇ РОБОТИ №4")
    P("Розподілені обчислення компромісних ранжувань та визначення")
    P("індексів задоволеності експертів колективним розв'язком")
    P("=" * 78)
    P("")
    P("1. ВХІДНІ ДАНІ (Лаб.1-2)")
    P("-" * 78)
    P(f"Повний набір ({len(D.FULL_OBJECTS)} жанрів): {', '.join(D.FULL_OBJECTS)}")
    P(f"Робоча підмножина (n = {n}): {', '.join(D.OBJECTS)}")
    P(f"Кількість експертів: {len(D.EXPERTS)} (20 студентів + Викладач)")
    P("")
    P("Звужені трійки (для перебору):")
    for j, (e, t) in enumerate(zip(D.EXPERTS, D.EXPERT_TRIPLES), 1):
        P(f"  {j:>2} {e:<14} → {t[0]} > {t[1]} > {t[2]}")
    P("")
    P("Оригінальні трійки Лаб.1 (з можливими видаленими об'єктами):")
    objs = set(D.OBJECTS)
    for j, (e, t) in enumerate(zip(D.EXPERTS, D.EXPERT_TRIPLES_LAB1), 1):
        marks = ["[видалено]" if o not in objs else "" for o in t]
        P(f"  {j:>2} {e:<14} → {t[0]}{marks[0]} > {t[1]}{marks[1]} > {t[2]}{marks[2]}")
    P("")

    P("2. СХЕМА ДЕКОМПОЗИЦІЇ ПЕРЕБОРУ")
    P("-" * 78)
    P(f"n = {n}, n гілок з фіксованим першим об'єктом, кожна (n-1)! = "
      f"{L4._factorial(n - 1)} перестановок.")
    P(f"Σ |Гілка_i| = n · (n-1)! = n! = {cen['n_perm']}  (повне покриття).")
    P("")

    P("3. РЕЗУЛЬТАТИ ПЕРЕБОРУ")
    P("-" * 78)
    P(f"Централізований: Σ d = {cen['best_sum_value']}, "
      f"max d = {cen['best_max_value']}, час = {cen['elapsed']}s")
    P(f"  ранжування: {' > '.join(cen['best_sum_rank'])}")
    P(f"Розподілений ({dis['n_workers']} воркерів): "
      f"Σ d = {dis['best_sum_value']}, max d = {dis['best_max_value']}, "
      f"час = {dis['elapsed']}s")
    P(f"  ранжування: {' > '.join(dis['best_sum_rank'])}")
    P(f"Збіг із Лаб.3: {'ТАК' if cen['best_sum_value'] == dis['best_sum_value'] else 'НІ'}")
    P("")
    P("Гілки розподіленого перебору:")
    for b in dis["branches"]:
        P(f"  fix={b['first']:<12} count={b['count']:>4}  "
          f"локальний Σ_min={b['best_sum']}, max_min={b['best_max']}")
    P("")

    P("4. ОБРАНЕ КОМПРОМІСНЕ РАНЖУВАННЯ A*")
    P("-" * 78)
    P("A* (порядок об'єктів): " + " > ".join(chosen["ranking"]))
    P("R* (вектор рангів):    " + ", ".join(
        f"{o}={r}" for o, r in zip(D.OBJECTS, chosen["rank_vec"])))
    P("")

    P("5. ВІДСТАНІ ТА ІНДЕКСИ ЗАДОВОЛЕНОСТІ")
    P("-" * 78)
    P(f"max d = 3·(n-3) = {3 * (n - 3)}")
    P(f"{'#':>3}  {'Експерт':<14} {'d_part':>6} {'d':>4} {'s, %':>7}  Трійка / видалено")
    for j, r in enumerate(sat, 1):
        rem = ('видалено: ' + ', '.join(r['removed'])) if r['removed'] else ''
        P(f"{j:>3}  {r['expert']:<14} {r['d_partial']:>6} {r['d']:>4} "
          f"{r['s']:>7.2f}  {' > '.join(r['triple'])}  {rem}")
    avg = sum(x["s"] for x in sat) / len(sat)
    P(f"\nСередній індекс задоволеності: {avg:.2f}%")
    P("")

    P("6. СИТУАЦІЯ Б — ГЕНЕТИЧНИЙ АЛГОРИТМ ДЛЯ n >> 12")
    P("-" * 78)
    P(f"{'n_alt':>5} {'n_exp':>5} {'pop/gen':>8} "
      f"{'Σ_центр':>8} {'T_ц,с':>6} {'Σ_розп':>7} {'T_р,с':>6} "
      f"{'Δ':>4} {'Δ%':>7}")
    for r in suite:
        P(f"{r['n_alt']:>5} {r['n_exp']:>5} "
          f"{r['pop_total']}/{r['n_gen']:<6} "
          f"{r['centralized_cost']:>8} {r['centralized_time']:>6} "
          f"{r['distributed_cost']:>7} {r['distributed_time']:>6} "
          f"{r['improvement']:>+4} {r['improvement_pct']:>+7.2f}")
    P("")
    avg_imp = sum(r["improvement_pct"] for r in suite) / len(suite)
    P(f"Середнє покращення розподіленого ГА відносно централізованого: "
      f"{avg_imp:+.2f}%")
    P("")
    P("=" * 78)
    P("Кінець протоколу.")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Хаб на /  — список лабораторних, у які можна перейти
# ---------------------------------------------------------------------------
def render_hub() -> str:
    # Лаб.4: підтягуємо середній індекс задоволеності (це вже кешований
    # результат після першого запиту; для cold-start можна отримати
    # невелику затримку, але це і є очікувана поведінка).
    sat_avg = "—"
    try:
        sat = _satisfactions()
        if sat:
            sat_avg = f"{sum(r['s'] for r in sat) / len(sat):.1f}%"
    except Exception:
        sat_avg = "—"

    # Лаб.5: швидкий розрахунок r для варіанта 8.
    try:
        l5_report = L5.compute(L5.PI_V8)
        l5_total = L5._fmt(l5_report["total_real"])
    except Exception:
        l5_total = "—"

    body = f"""
<div class="card">
  <h2>Лабораторні роботи курсу</h2>
  <p class="lead">Інтелектуальна обробка даних в розподілених інформаційних
     середовищах · спеціальність 122 «Комп'ютерні науки», КН-41.
     Кожна лабораторна — окремий розділ цього додатку.</p>
</div>

<div class="grid cols-2">
  <div class="card">
    <h2>Лабораторна №4</h2>
    <p class="lead">Розподілені обчислення компромісних ранжувань методом
       прямого перебору з декомпозицією; обчислення індексів задоволеності
       експертів колективним розв'язком; евристичне розв'язання для n ≫ 12
       за допомогою генетичного алгоритму (централізовано та острівна модель).</p>
    <div class="kpi">
      <div class="item"><div class="l">Середній індекс s</div><div class="v">{sat_avg}</div></div>
      <div class="item"><div class="l">Об'єктів</div><div class="v">{len(D.OBJECTS)}</div></div>
      <div class="item"><div class="l">Експертів</div><div class="v">{len(D.EXPERTS)}</div></div>
    </div>
    <p style="margin-top:14px"><a class="btn" href="/lab4">Відкрити Лаб.4 →</a></p>
  </div>

  <div class="card">
    <h2>Лабораторна №5</h2>
    <p class="lead">Визначення характеристик систем функціональних пристроїв
       за першим законом Амдала: завантаженості p_i кожного пристрою, реальна
       продуктивність системи, аналіз несумісності та пропозиція значень π,
       при яких система стає сумісною. Інтерактивне введення продуктивностей
       та візуалізація графа.</p>
    <div class="kpi">
      <div class="item"><div class="l">Варіант</div><div class="v">8</div></div>
      <div class="item"><div class="l">Пристроїв</div><div class="v">{L5.N_DEVICES}</div></div>
      <div class="item"><div class="l">Реальна r</div><div class="v">{l5_total}</div></div>
    </div>
    <p style="margin-top:14px"><a class="btn" href="/lab5">Відкрити Лаб.5 →</a></p>
  </div>
</div>
"""
    return T.page("Лабораторні", body, active="hub", lab_num=0, tabs=T.HUB_TABS)


# ---------------------------------------------------------------------------
# Сторінка /lab5 — Лабораторна №5
# ---------------------------------------------------------------------------
def render_lab5(pi=None, error: str = "") -> str:
    if pi is None:
        pi = list(L5.PI_V8)

    try:
        report = L5.compute(pi)
    except ValueError as exc:
        # помилка в π — рендеримо з дефолтними і повідомленням
        report = L5.compute(L5.PI_V8)
        pi = list(L5.PI_V8)
        error = error or f"Помилка у введених даних: {exc}. Показано дефолтні значення."

    # ---- Граф ----
    svg = L5.graph_svg(report)

    # ---- KPI-плити ----
    n_bottlenecks = len(report["bottlenecks"])
    n_underloaded = len(report["incompatibilities"])
    kpi_html = f"""
    <div class="grid cols-3">
      {T.stat("Реальна продуктивність r",  L5._fmt(report["total_real"]))}
      {T.stat("Сума пікових Σπ",           L5._fmt(report["sum_peak"]))}
      {T.stat("Коеф. використання",        f'{report["utilization"]*100:.1f}%')}
      {T.stat("Підсистем",                 len(report["subsystems"]))}
      {T.stat("Бутилок (π=π^(k))",         n_bottlenecks)}
      {T.stat("Недозавантажених",          n_underloaded)}
    </div>
    """

    # ---- Таблиці завантаженостей по підсистемах ----
    sub_blocks = []
    for sub in report["subsystems"]:
        rows = []
        for ld in sub["loads"]:
            tag = ('<span class="tag red">бутилка</span>' if ld["is_min"]
                   else ('<span class="tag green">p=1</span>' if ld["p"] >= 0.9999
                         else '<span class="tag indigo">недозавантаж.</span>'))
            rows.append([
                ld["node"], L5._fmt(ld["pi"]),
                f'{L5._fmt(sub["min_pi"])} / {L5._fmt(ld["pi"])}',
                f'<b>{ld["p"]:.4f}</b>',
                f'{ld["p"]*100:.1f}%',
                tag,
            ])
        sub_blocks.append(f"""
        <h3>Підсистема {sub['id']} · вузли {sub['nodes']} · l={sub['device_count']}</h3>
        <p class="muted">π<sup>({sub['id']})</sup> = min(π_i) =
           <span class="kbd">{L5._fmt(sub['min_pi'])}</span>,
           r<sup>({sub['id']})</sup> = l · π<sup>({sub['id']})</sup> =
           <span class="kbd">{L5._fmt(sub['real_productivity'])}</span></p>
        {T.table(
            ["Вузол",
             "π_i (пікова продуктивність пристрою)",
             "π^(k)/π_i (підрахунок завантаженості)",
             "p_i (завантаженість, частка часу)",
             "p_i, % (% часу пристрій реально працює)",
             "Стан"],
            rows
        )}
        """)
    sub_tables_html = "".join(sub_blocks)

    # ---- Стовпчикова діаграма завантаженостей ----
    bar_items = []
    for sub in report["subsystems"]:
        for ld in sub["loads"]:
            bar_items.append((f'#{ld["node"]} (π={L5._fmt(ld["pi"])})',
                              round(ld["p"] * 100, 1)))
    bar_html = T.bar_chart(bar_items, maximum=100)

    # ---- Несумісність ----
    if report["is_compatible"]:
        incomp_html = T.alert(
            "Система сумісна — у кожній підсистемі всі π_i рівні, "
            "усі завантаженості p_i = 1.", "ok")
    else:
        rows = [
            [f'#{x["node"]}', x["subsys"], L5._fmt(x["pi"]),
             f'{x["p"]*100:.1f}%', f'{x["underload"]*100:.1f}%',
             L5._fmt(x["wasted"])]
            for x in report["incompatibilities"]
        ]
        incomp_table = T.table(
            ["Пристрій",
             "Підсистема",
             "π_i (пікова продуктивність)",
             "p_i (завантаженість)",
             "Простій (1 − p_i)",
             "Втрачено од. (π_i − π^(k))"],
            rows
        )
        causes_html = "<ul style='margin-left:20px;color:#334155;line-height:1.7'>" \
                      + "".join(f"<li>{c}</li>" for c in report["causes"]) \
                      + "</ul>"
        incomp_html = (
            T.alert(
                f"Виявлено несумісність: {len(report['incompatibilities'])} "
                "пристроїв працюють на неповну потужність.", "warn"
            )
            + incomp_table
            + "<h3>Причини несумісності</h3>"
            + causes_html
        )

    # ---- Сумісні значення (пропозиції) ----
    def _sugg_chips(values, label_color):
        chips = []
        for i, v in enumerate(values):
            chips.append(
                f'<span class="rk"><b>π_{i}</b>{L5._fmt(v)}</span>'
            )
        return f'<div class="ranking">{"".join(chips)}</div>'

    down = report["suggestion_down"]
    up = report["suggestion_up"]
    r_down = sum(len(s["nodes"]) * min(down[i] for i in s["nodes"])
                 for s in L5.GRAPH_V8["subsystems"])
    r_up = sum(len(s["nodes"]) * min(up[i] for i in s["nodes"])
               for s in L5.GRAPH_V8["subsystems"])
    sugg_html = f"""
    <h3>Стратегія А · «Зрівняти вниз»</h3>
    <p class="lead">Усі π_i у кожній підсистемі знижуються до min π цієї
       підсистеми — нічого не докуповуємо, але втрачаємо потенціал
       швидших пристроїв. Реальна продуктивність системи лишається
       такою ж: <span class="kbd">r = {L5._fmt(r_down)}</span>, але всі
       p_i = 1.</p>
    {_sugg_chips(down, "down")}
    <form method="POST" action="/lab5" class="inline" style="margin-top:10px">
      {''.join(f'<input type="hidden" name="pi_{i}" value="{L5._fmt(v)}">'
               for i, v in enumerate(down))}
      <button class="btn secondary" type="submit">Застосувати «вниз» до форми ↓</button>
    </form>

    <h3 style="margin-top:18px">Стратегія Б · «Зрівняти вгору»</h3>
    <p class="lead">Усі π_i у кожній підсистемі підвищуються до max π цієї
       підсистеми — потребує апгрейду слабких пристроїв, але дає
       максимальну реальну продуктивність:
       <span class="kbd">r = {L5._fmt(r_up)}</span>, p_i = 1.</p>
    {_sugg_chips(up, "up")}
    <form method="POST" action="/lab5" class="inline" style="margin-top:10px">
      {''.join(f'<input type="hidden" name="pi_{i}" value="{L5._fmt(v)}">'
               for i, v in enumerate(up))}
      <button class="btn" type="submit">Застосувати «вгору» до форми ↑</button>
    </form>
    """

    # ---- Інтерактивна форма введення π ----
    form_inputs = []
    for sub in L5.GRAPH_V8["subsystems"]:
        cells = []
        for n in sub["nodes"]:
            cells.append(
                f'<label style="display:flex;flex-direction:column;gap:2px;'
                f'min-width:90px"><span class="muted" style="font-size:.78rem">'
                f'π<sub>{n}</sub></span>'
                f'<input type="number" name="pi_{n}" step="any" min="0.001" '
                f'value="{L5._fmt(pi[n])}" required style="padding:6px 8px;'
                f'font-size:.9rem"></label>'
            )
        form_inputs.append(
            f'<div style="background:#f8fafc;border:1px solid #e2e8f0;'
            f'border-radius:8px;padding:10px 12px;margin-bottom:10px">'
            f'<b style="color:#312e81">Підсистема {sub["id"]}</b> '
            f'<span class="muted">(вузли {sub["nodes"]})</span>'
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">'
            f'{"".join(cells)}</div></div>'
        )

    form_html = f"""
    <form method="POST" action="/lab5">
      {''.join(form_inputs)}
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
        <button class="btn" type="submit" name="action" value="calc">
          Розрахувати
        </button>
        <a class="btn secondary" href="/lab5">Скинути до варіанта 8</a>
      </div>
    </form>
    """

    # ---- Зборка сторінки ----
    err_html = T.alert(error, "warn") if error else ""

    body = f"""
{err_html}

<div class="card">
  <h2>Постановка задачі</h2>
  <p class="lead">Задано граф системи функціональних пристроїв із
     {L5.N_DEVICES} пристроями у {len(L5.GRAPH_V8['subsystems'])} незалежних
     підсистемах. Відомі пікові продуктивності π_i. <b>Варіант 8</b> →
     Граф ФП=0 (Рисунок 2 з методички), продуктивності зі стовпчика №8
     Таблиці 1.</p>
  <p>За <b>першим законом Амдала</b>, реальна продуктивність кожної
     підсистеми визначається найслабшим пристроєм цієї підсистеми:
     π<sup>(k)</sup> = min{{π_i : i ∈ підсистема k}}. Завантаженість
     пристрою p_i = π<sup>(k)</sup>/π_i; реальна продуктивність системи
     r = Σ<sub>k</sub> l<sub>k</sub> · π<sup>(k)</sup>, де l<sub>k</sub> —
     кількість пристроїв у підсистемі k.</p>
</div>

<div class="card">
  <h2>1. Граф системи функціональних пристроїв</h2>
  <p class="lead">Червоні вузли — бутилки (пристрої з π_i = π<sup>(k)</sup>),
     визначають продуктивність своєї підсистеми. Сині — недозавантажені
     (π_i &gt; π<sup>(k)</sup>). Зелені — повністю завантажені
     (p_i = 1, але не бутилки — рідкий випадок при апгрейді).</p>
  {svg}
</div>

<div class="card">
  <h2>2. Реальна продуктивність системи</h2>
  {kpi_html}
  <p class="muted" style="margin-top:10px">r = Σ l<sub>k</sub>·π<sup>(k)</sup> =
    {' + '.join(f'{s["device_count"]}·{L5._fmt(s["min_pi"])}' for s in report['subsystems'])}
    = <span class="kbd">{L5._fmt(report['total_real'])}</span></p>
</div>

<div class="card">
  <h2>3. Завантаженості усіх пристроїв системи</h2>
  {sub_tables_html}
  <h3 style="margin-top:18px">Розподіл p_i по пристроях</h3>
  {bar_html}
</div>

<div class="card">
  <h2>4. Несумісність системи та її причини</h2>
  {incomp_html}
</div>

<div class="card">
  <h2>5. Запропоновані продуктивності для сумісної системи</h2>
  <p class="lead">Сумісна система = у кожній підсистемі всі π_i рівні,
     отже усі p_i = 1, простоїв немає.</p>
  {sugg_html}
</div>

<div class="card">
  <h2>6. Інтерактивне введення даних</h2>
  <p class="lead">Введіть власні значення пікових продуктивностей π_i і
     натисніть «Розрахувати». Граф ФП фіксований під варіант 8.</p>
  {form_html}
</div>
"""
    return T.page("Лаб.5 · ФП", body, active="home_l5",
                  lab_num=5, tabs=T.LAB5_TABS)


# ---------------------------------------------------------------------------
# Допоміжні функції відповіді
# ---------------------------------------------------------------------------
def _send_html(handler: BaseHTTPRequestHandler, html: str, status: int = 200):
    body = html.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _send_text(handler: BaseHTTPRequestHandler, text: str,
               filename: str = "protocol.txt", status: int = 200):
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Disposition",
                        f'attachment; filename="{filename}"')
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _send_json(handler: BaseHTTPRequestHandler, payload, status: int = 200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _error_page(message: str) -> str:
    body = f"""
<div class="card">
  <h2>Помилка обробки запиту</h2>
  {T.alert(message, "error")}
  <p><a class="btn secondary" href="/">← Повернутися на головну</a></p>
</div>
"""
    return T.page("Помилка", body)


# ---------------------------------------------------------------------------
# HTTP handler — точка входу Vercel
# ---------------------------------------------------------------------------
class handler(BaseHTTPRequestHandler):

    def log_message(self, *_):  # noqa: D401
        return

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path in ("", "/"):
                _send_html(self, render_hub()); return
            if path == "/lab4":
                _send_html(self, render_home()); return
            if path == "/lab5":
                _send_html(self, render_lab5()); return
            if path == "/data":
                _send_html(self, render_data()); return
            if path == "/distributed":
                _send_html(self, render_distributed()); return
            if path == "/satisfaction":
                _send_html(self, render_satisfaction()); return
            if path == "/large":
                _send_html(self, render_large()); return
            if path == "/protocol":
                _send_html(self, render_protocol_form()); return
            if path == "/protocol.txt":
                _send_text(self, render_protocol_txt()); return
            if path == "/healthz":
                _send_json(self, {
                    "ok": True,
                    "db": S.db_status(),
                    "n_objects": len(D.OBJECTS),
                    "n_experts": len(D.EXPERTS),
                    "lab5_devices": L5.N_DEVICES,
                }); return
            _send_html(self, _error_page("Сторінку не знайдено."), 404)
        except Exception as exc:  # pragma: no cover
            _send_html(self, _error_page(f"Внутрішня помилка: {exc}"), 500)

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            if path == "/protocol":
                params = parse_qs(raw)
                pw = params.get("password", [""])[0]
                if pw == D.PROTOCOL_PASSWORD:
                    S.log_event("protocol", "Перегляд протоколу")
                    _send_html(self, render_protocol_view())
                else:
                    _send_html(self, render_protocol_form(
                        "Невірний пароль. Спробуйте ще раз."), 401)
                return
            if path == "/lab5":
                params = parse_qs(raw)
                try:
                    pi = L5.parse_form_pi(params)
                    _send_html(self, render_lab5(pi=pi))
                except ValueError as exc:
                    _send_html(self, render_lab5(error=str(exc)))
                return
            _send_html(self, _error_page("Метод POST для цього шляху не підтримується."), 405)
        except Exception as exc:  # pragma: no cover
            _send_html(self, _error_page(f"Внутрішня помилка: {exc}"), 500)
