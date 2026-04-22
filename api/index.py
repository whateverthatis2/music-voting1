# -*- coding: utf-8 -*-
"""
Точка входу serverless-функції Vercel.

Маршрути:
    /            — огляд лабораторної
    /data        — вхідні дані з Лаб.1-2 + матриці п.1.2 та п.1.3
    /enumerate   — прямий перебір n! та пошук медіан
    /aco         — мурашиний алгоритм + порівняння з прямим перебором
    /scaling     — масштабне дослідження ACO (20/50/100 × 10/20/30)
    /protocol    — захищений паролем журнал подій
    /healthz     — JSON для перевірки стану сховища
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from . import data as D
from . import templates as T
from . import storage as S
from . import algorithms as A
from . import aco as ACO


# ---------------------------------------------------------------------------
# Кеш обчислень — щоб важкі речі рахувалися один раз на cold-start
# ---------------------------------------------------------------------------
_cache: dict = {}


def _enum_results():
    if "enum" not in _cache:
        _cache["enum"] = A.enumerate_all(D.OBJECTS, D.EXPERT_TRIPLES, keep_top=10)
    return _cache["enum"]


def _aco_results():
    if "aco" not in _cache:
        res = ACO.ant_colony(D.OBJECTS, D.EXPERT_TRIPLES,
                             n_ants=30, n_iter=80, seed=2026)
        _cache["aco"] = res
        S.save_aco_run({
            "objects": list(D.OBJECTS),
            "n_experts": len(D.EXPERT_TRIPLES),
            "best_ranking": res["best_ranking"],
            "best_cost": res["best_cost"],
            "best_max": res["best_max"],
            "params": res["params"],
            "elapsed": res["elapsed"],
        })
    return _cache["aco"]


def _scaling_results():
    if "scaling" not in _cache:
        _cache["scaling"] = ACO.scaling_test()
    return _cache["scaling"]


# ---------------------------------------------------------------------------
# Сторінка /
# ---------------------------------------------------------------------------
def render_home() -> str:
    enum = _enum_results()
    aco_res = _aco_results()

    body = f"""
<div class="card">
  <h2>Постановка задачі</h2>
  <p class="lead">Визначити колективне ранжування об'єктів у розподіленій
     організаційній системі на основі експертної інформації, зібраної
     під час Лабораторних робіт №1-2.</p>
  <div class="grid cols-3">
    {T.stat("Об'єктів (повний набір)",   len(D.FULL_OBJECTS))}
    {T.stat("Об'єктів після евристик",   len(D.OBJECTS))}
    {T.stat("Експертів (з викладачем)",  len(D.EXPERTS))}
    {T.stat("Перестановок n!",           f"{enum['n_perm']:,}".replace(",", " "))}
    {T.stat("Медіан мін-сума",           len(enum["all_best_sum"]))}
    {T.stat("Медіан мін-макс",           len(enum["all_best_max"]))}
  </div>
</div>

<div class="card">
  <h2>Колективне ранжування (медіана Кемені — Снела)</h2>
  <h3>Прямий перебір — мінімум суми відстаней</h3>
  {T.ranking_chips(enum["best_sum_rank"])}
  <p class="muted">Сумарна відстань Кука: <span class="kbd">{enum["best_sum_value"]}</span></p>

  <h3>Прямий перебір — мінімум максимуму відстаней</h3>
  {T.ranking_chips(enum["best_max_rank"])}
  <p class="muted">Максимальна відстань: <span class="kbd">{enum["best_max_value"]}</span></p>

  <h3>Мурашиний алгоритм (на тих самих даних)</h3>
  {T.ranking_chips(aco_res["best_ranking"])}
  <p class="muted">Сума відстаней: <span class="kbd">{aco_res["best_cost"]}</span> ·
     максимум: <span class="kbd">{aco_res["best_max"]}</span> ·
     ітерацій: <span class="kbd">{len(aco_res["history"])}</span> ·
     час: <span class="kbd">{aco_res["elapsed"]}s</span></p>
  {_aco_match_alert(enum, aco_res)}
</div>

<div class="card">
  <h2>Послідовність виконання</h2>
  <ol style="margin-left:18px;color:#334155;line-height:1.8">
    <li>Зчитати множинні порівняння експертів з Лаб.1 та евристики Лаб.2 →
        <a href="/data">Дані Лаб.1-2</a>.</li>
    <li>Побудувати матрицю статистики переваг (п.1.2) та розгорнуту матрицю
        рангів (п.1.3) → <a href="/data#matrix">Матриці</a>.</li>
    <li>Згенерувати 7! = 5040 перестановок та обчислити відстані Кука
        (п.2) → <a href="/enumerate">Прямий перебір</a>.</li>
    <li>Знайти мінімуми суми та максимуму — медіани Кемені — Снела
        (п.3, п.10).</li>
    <li>Запустити мурашиний алгоритм та порівняти з еталоном
        (п.16) → <a href="/aco">Мурашиний алгоритм</a>.</li>
    <li>Дослідити поведінку ACO для 20/50/100 альтернатив (п.17) →
        <a href="/scaling">Масштабування</a>.</li>
  </ol>
</div>
"""
    return T.page("Огляд", body, active="home")


def _aco_match_alert(enum, aco_res):
    if aco_res["best_cost"] is None:
        return T.alert("Мурашиний алгоритм не встиг завершитися.", "warn")
    if aco_res["best_cost"] == enum["best_sum_value"]:
        return T.alert(
            "Мурашиний алгоритм збігся з результатом прямого перебору "
            f"(сумарна відстань = {enum['best_sum_value']}). "
            "Це підтверджує коректність обох методів.", "ok")
    delta = aco_res["best_cost"] - enum["best_sum_value"]
    return T.alert(
        f"Мурашиний алгоритм відхилився від прямого перебору на Δ = {delta}. "
        "Збільшення параметрів n_ants, n_iter або alpha/beta зазвичай усуває розрив.",
        "warn")


# ---------------------------------------------------------------------------
# Сторінка /data
# ---------------------------------------------------------------------------
def render_data() -> str:
    pmat = A.preference_matrix(D.OBJECTS, D.EXPERT_TRIPLES)
    rmat = A.expanded_rank_matrix(D.OBJECTS, D.EXPERT_TRIPLES)
    borda = A.borda_score(pmat)

    # 1. Множинні порівняння у вигляді експертів × 3 рядки (як п.1.1)
    triples_rows = []
    for r_idx in range(3):
        triples_rows.append([t[r_idx] for t in D.EXPERT_TRIPLES])
    triple_headers = [str(i + 1) for i in range(len(D.EXPERT_TRIPLES))]

    # 2. Матриця 1.2
    pmat_headers = [f"o{j+1}" for j in range(len(D.OBJECTS))]
    pmat_rows_lbl = ["1-ше місце", "2-ге місце", "3-тє місце", "Σ згадувань"]

    # 3. Матриця 1.3
    rmat_headers = [str(i + 1) for i in range(len(D.EXPERT_TRIPLES))]

    # Список об'єктів та експертів
    obj_chips = "".join(
        f'<span class="rk"><b>o{i+1}</b>{o}</span>'
        for i, o in enumerate(D.OBJECTS)
    )
    exp_chips = "".join(
        f'<span class="e">{e}</span>' for e in D.EXPERTS
    )

    # Heuristics
    heur_rows = [
        [h["id"], h["name"], h["votes"], h["rule"]] for h in D.HEURISTICS
    ]
    removed_rows = [
        [r["step"], r["heuristic"],
         ", ".join(r["removed"]) if r["removed"] else "—",
         r["left"]]
        for r in D.REMOVED_BY_HEURISTICS
    ]

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
  <h2>3. Множинні порівняння експертів (п.1.1)</h2>
  <p class="lead">Кожен стовпчик — експерт; рядки — місця 1, 2, 3 у трійці.</p>
  {T.matrix_table(triple_headers, triples_rows,
                  row_labels=["1", "2", "3"])}
</div>

<div class="card" id="matrix">
  <h2>4. Матриця статистики переваг (п.1.2)</h2>
  <p class="lead">Скільки експертів поставили об'єкт на позиції 1/2/3
     та сумарна кількість згадувань.</p>
  {T.matrix_table(pmat_headers, pmat,
                  row_labels=pmat_rows_lbl)}
  <h3>Рейтинг Борда (3·1-ше + 2·2-ге + 1·3-тє)</h3>
  {T.bar_chart(list(zip(D.OBJECTS, borda)))}
</div>

<div class="card">
  <h2>5. Розгорнута матриця рангів (п.1.3)</h2>
  <p class="lead">Рядки — об'єкти; стовпчики — експерти. Значення = ранг
     об'єкта (1, 2, 3) у трійці експерта; 0 — не названо.</p>
  {T.matrix_table(rmat_headers, rmat,
                  row_labels=[f"o{i+1} {o}" for i, o in enumerate(D.OBJECTS)])}
</div>

<div class="card">
  <h2>6. Евристики звуження (Лаб.2)</h2>
  {T.table(["ID", "Назва", "Голоси", "Правило"], heur_rows)}
  <h3>Хід застосування евристик</h3>
  {T.table(["Крок", "Евристика", "Прибрано", "Залишилось"], removed_rows)}
</div>
"""
    return T.page("Дані", body, active="data")


# ---------------------------------------------------------------------------
# Сторінка /enumerate
# ---------------------------------------------------------------------------
def render_enumerate() -> str:
    enum = _enum_results()

    # Демонстраційна таблиця (п.9)
    sample_headers = ["#", "Перестановка", "Σ d", "max d",
                      *[f"e{i+1}" for i in range(min(8, len(D.EXPERT_TRIPLES)))]]
    sample_rows = []
    for k, sp in enumerate(enum["sample_perms"], 1):
        ranking_str = " › ".join(sp["ranking"])
        cells = [k, ranking_str, sp["sum"], sp["max"],
                 *sp["dists"][:8]]
        sample_rows.append(cells)

    # Топ-10 по сумі та по максимуму
    top_sum_rows = [
        [i + 1, " › ".join(r), s, m]
        for i, (s, m, r) in enumerate(enum["top_sum"])
    ]
    top_max_rows = [
        [i + 1, " › ".join(r), s, m]
        for i, (s, m, r) in enumerate(enum["top_max"])
    ]

    # Відновлення з вектора рангів (п.11)
    rank_vec = A.ranking_to_rank_vector(D.OBJECTS, enum["best_sum_rank"])
    recovered = A.recover_ranking_from_ranks(D.OBJECTS, rank_vec)

    # Альтернативні медіани
    alt_sum_html = ""
    if len(enum["all_best_sum"]) > 1:
        alt_sum_html = "<h3>Інші перестановки з тим самим Σ</h3>" + "".join(
            f'<div style="margin:6px 0">{T.ranking_chips(r)}</div>'
            for r in enum["all_best_sum"][1:6]
        )
    alt_max_html = ""
    if len(enum["all_best_max"]) > 1:
        alt_max_html = (
            f'<p class="muted">Усього перестановок з тим же максимумом: '
            f'<b>{len(enum["all_best_max"])}</b></p>')

    body = f"""
<div class="card">
  <h2>Прямий перебір {len(D.OBJECTS)}! = {enum["n_perm"]:,} перестановок</h2>
  <p class="lead">Для кожної перестановки об'єктів обчислюється відстань Кука
     до трійки кожного з {len(D.EXPERT_TRIPLES)} експертів за евристикою E1
     (поміркованої взаємності):
     <span class="kbd">d = |1 − r(i₁)| + |2 − r(i₂)| + |3 − r(i₃)|</span>.
     Далі знаходимо суму та максимум по експертах.</p>
  <div class="kpi">
    <div class="item"><div class="l">Σ-медіана</div><div class="v">{enum["best_sum_value"]}</div></div>
    <div class="item"><div class="l">max-медіана</div><div class="v">{enum["best_max_value"]}</div></div>
    <div class="item"><div class="l">Кількість Σ-медіан</div><div class="v">{len(enum["all_best_sum"])}</div></div>
    <div class="item"><div class="l">Кількість max-медіан</div><div class="v">{len(enum["all_best_max"])}</div></div>
  </div>
</div>

<div class="card">
  <h2>Медіана Кемені — мінімум суми відстаней</h2>
  {T.ranking_chips(enum["best_sum_rank"])}
  <p class="muted">Σ d = <span class="kbd">{enum["best_sum_value"]}</span></p>
  {alt_sum_html}
</div>

<div class="card">
  <h2>Мінімаксна медіана — мінімум максимуму</h2>
  {T.ranking_chips(enum["best_max_rank"])}
  <p class="muted">max d = <span class="kbd">{enum["best_max_value"]}</span></p>
  {alt_max_html}
</div>

<div class="card">
  <h2>Демонстрація обчислень (п.9 завдання)</h2>
  <p class="lead">Перевірка коректності алгоритму на кількох обраних
     перестановках. Колонки e₁…e₈ — відстані до перших восьми експертів.</p>
  {T.table(sample_headers, sample_rows)}
</div>

<div class="card">
  <h2>Топ-10 перестановок за сумою відстаней</h2>
  {T.table(["#", "Ранжування", "Σ d", "max d"], top_sum_rows)}
  <h3>Топ-10 перестановок за максимумом</h3>
  {T.table(["#", "Ранжування", "Σ d", "max d"], top_max_rows)}
</div>

<div class="card">
  <h2>Відновлення ранжування з вектора рангів (п.11)</h2>
  <p class="lead">Для медіани Σ обчислимо вектор рангів об'єктів у вихідному
     порядку <span class="kbd">{", ".join(D.OBJECTS)}</span> та відновимо
     з нього ранжування (зворотна операція).</p>
  {T.table(
      ["Об'єкт", *D.OBJECTS],
      [["Ранг у медіані", *rank_vec]]
  )}
  <p class="muted">Відновлене ранжування:</p>
  {T.ranking_chips(recovered)}
</div>
"""
    return T.page("Прямий перебір", body, active="enumerate")


# ---------------------------------------------------------------------------
# Сторінка /aco
# ---------------------------------------------------------------------------
def render_aco() -> str:
    enum = _enum_results()
    aco_res = _aco_results()

    history = aco_res["history"]
    chart_items = [
        (str(i + 1) if i in (0, len(history) // 2, len(history) - 1) else "",
         h)
        for i, h in enumerate(history)
    ]

    delta = (aco_res["best_cost"] - enum["best_sum_value"]
             if aco_res["best_cost"] is not None else None)
    match_pct = (100.0 * sum(1 for a, b in zip(
        aco_res["best_ranking"], enum["best_sum_rank"]) if a == b)
        / max(1, len(D.OBJECTS)))

    body = f"""
<div class="card">
  <h2>Особливості застосування мурашиного алгоритму для задач ранжування</h2>
  <p class="lead">Для пошуку медіани Кемені — Снела використано позиційну
     модифікацію Ant Colony Optimization (ACO) у дусі Ant System / ASrank.
     Кожна мурашка послідовно «розставляє» об'єкти по позиціях у ранжуванні,
     керуючись:</p>
  <ul style="margin-left:18px;color:#334155;line-height:1.8">
    <li><b>феромонною матрицею</b> τ[k][j] — накопиченою «привабливістю»
        ставити об'єкт <i>j</i> на позицію <i>k</i>;</li>
    <li><b>евристичною інформацією</b> η[j] — рейтингом Борда
        (3 за 1-ше, 2 за 2-ге, 1 за 3-тє місце від експерта);</li>
    <li><b>правилом вибору</b>
        P(j | k) ∝ τ[k][j]<sup>α</sup> · η[j]<sup>β</sup>;</li>
    <li><b>випаровуванням</b> τ ← (1 − ρ)·τ після кожної ітерації;</li>
    <li><b>відкладанням феромону</b> Δτ = Q / (1 + cost), плюс елітарне
        підкріплення найкращого розв'язку циклу.</li>
  </ul>
  <p class="lead">Перевага ACO над прямим перебором — поліноміальна складність
     O(n_iter · n_ants · n²). Для n ≤ 10 перебір швидший, але вже при
     n ≥ 13 факторіал перевершує мільярд, тоді як ACO зберігає лінійну
     залежність від часу.</p>
</div>

<div class="card">
  <h2>Прогін на робочих даних (n = {len(D.OBJECTS)})</h2>
  <div class="grid cols-3">
    {T.stat("Сумарна відстань Σ d", aco_res["best_cost"])}
    {T.stat("Максимальна відстань",  aco_res["best_max"])}
    {T.stat("Час, секунди",          aco_res["elapsed"])}
  </div>
  <h3>Знайдене ранжування</h3>
  {T.ranking_chips(aco_res["best_ranking"])}
  <p class="note">Параметри: α = {aco_res["params"]["alpha"]},
     β = {aco_res["params"]["beta"]}, ρ = {aco_res["params"]["rho"]},
     n_ants = {aco_res["params"]["n_ants"]},
     n_iter = {aco_res["params"]["n_iter"]}.</p>
</div>

<div class="card">
  <h2>Порівняння з прямим перебором (п.16 завдання)</h2>
  {T.table(
      ["Метрика", "Прямий перебір", "Мурашиний алгоритм"],
      [
        ["Σ d (ціль)",     enum["best_sum_value"], aco_res["best_cost"]],
        ["max d",          enum["best_max_value"], aco_res["best_max"]],
        ["Збіг рангів, %", "100.00",
         f"{match_pct:.2f}"],
        ["Час, с",         "≤ 1.0",                aco_res["elapsed"]],
      ]
  )}
  {T.alert(_aco_match_text(delta), "ok" if delta == 0 else "warn")}
  <h3>Збіжність по ітераціях</h3>
  {T.bar_chart([(f"i{i+1}", h) for i, h in enumerate(history[:30])],
               maximum=max(history) if history else 1)}
  <p class="note">Показано перші 30 ітерацій (всього {len(history)}).</p>
</div>
"""
    return T.page("Мурашиний алгоритм", body, active="aco")


def _aco_match_text(delta) -> str:
    if delta is None:
        return "Алгоритм не завершився за відведений час."
    if delta == 0:
        return ("Мурашиний алгоритм точно збігся з оптимумом, знайденим прямим "
                "перебором — медіана Кемені відтворена.")
    return (f"Мурашиний алгоритм відстає від еталону на Δ = {delta}. "
            "Збільшення параметрів покращить результат.")


# ---------------------------------------------------------------------------
# Сторінка /scaling
# ---------------------------------------------------------------------------
def render_scaling() -> str:
    rows = _scaling_results()
    table_rows = [
        [r["n_alt"], r["n_exp"], r["n_ants"], r["n_iter"],
         r["best_cost"], r["best_max"],
         f"{r['elapsed']}s", r["iterations_done"]]
        for r in rows
    ]
    body = f"""
<div class="card">
  <h2>Масштабне дослідження ACO (п.17 завдання)</h2>
  <p class="lead">Прогін мурашиного алгоритму на синтетичних даних
     для 20, 50, 100 альтернатив × 10, 20, 30 експертів. Кожен експерт —
     випадкова трійка з повного набору об'єктів.</p>
  {T.table(
      ["Альтернатив", "Експертів", "n_ants", "n_iter",
       "Σ d", "max d", "Час", "Виконано ітерацій"],
      table_rows
  )}
  {T.alert(
      "Параметри ACO зменшуються зі зростанням n, щоб укластися в "
      "10-секундний timeout serverless-функції Vercel. На локальній "
      "машині рекомендується піднімати n_iter та n_ants у 2-3 рази "
      "для отримання якіснішого розв'язку.", "info")}
</div>

<div class="card">
  <h2>Інтерпретація</h2>
  <p>Час прогону зростає приблизно як O(n_iter · n_ants · n²) — поліноміально
     по n, тоді як прямий перебір потребував би n! операцій. Уже при
     n = 13 факторіал перевершує мільярд (≈ 6.2·10⁹), що недосяжно для
     інтерактивної відповіді. Мурашиний алгоритм при цьому залишається
     практично застосовним до n ≈ 100-200.</p>
  <p>Зростання якості розв'язку (нижче Σ d) спостерігається переважно
     у перших 20-30 ітераціях; після того алгоритм стабілізується,
     що відображає типову поведінку ASrank.</p>
</div>
"""
    return T.page("Масштабування", body, active="scaling")


# ---------------------------------------------------------------------------
# Сторінка /protocol
# ---------------------------------------------------------------------------
def render_protocol_form(error: str = "") -> str:
    err_html = T.alert(error, "error") if error else ""
    body = f"""
<div class="card">
  <h2>Конфіденційний протокол</h2>
  <p class="lead">Перегляд журналу подій, ранжувань та прогонів
     мурашиного алгоритму захищено паролем.</p>
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
    aco_runs = S.load_aco_runs(20)
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

    aco_rows = [
        [r.get("time", "")[:19],
         r.get("n_experts", ""),
         r.get("best_cost", ""),
         r.get("best_max", ""),
         f"{r.get('elapsed', '')}s",
         " › ".join(r.get("best_ranking", []))]
        for r in aco_runs
    ] or [["—", "—", "—", "—", "—", "—"]]

    ev_rows = [
        [e.get("time", "")[:19], e.get("type", ""), e.get("message", "")]
        for e in events
    ] or [["—", "—", "журнал порожній"]]

    body = f"""
<div class="card">
  <h2>Стан сховища</h2>
  {status_alert}
</div>

<div class="card">
  <h2>Збережені колективні ранжування</h2>
  {T.table(["Час", "Джерело", "Метод", "Σ d", "max d", "Ранжування"], rk_rows)}
</div>

<div class="card">
  <h2>Прогони мурашиного алгоритму</h2>
  {T.table(["Час", "Експертів", "Σ d", "max d", "Час прогону", "Найкраще ранжування"],
           aco_rows)}
</div>

<div class="card">
  <h2>Журнал подій</h2>
  {T.table(["Час", "Тип", "Повідомлення"], ev_rows)}
</div>
"""
    return T.page("Протокол", body, active="protocol")


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

    # Vercel сам логує — придушимо stderr-шум
    def log_message(self, *_):  # noqa: D401
        return

    def do_GET(self):  # noqa: N802 (потрібно саме `do_GET`)
        path = urlparse(self.path).path
        try:
            if path in ("", "/"):
                _send_html(self, render_home()); return
            if path == "/data":
                _send_html(self, render_data()); return
            if path == "/enumerate":
                _send_html(self, render_enumerate()); return
            if path == "/aco":
                _send_html(self, render_aco()); return
            if path == "/scaling":
                _send_html(self, render_scaling()); return
            if path == "/protocol":
                _send_html(self, render_protocol_form()); return
            if path == "/healthz":
                _send_json(self, {
                    "ok": True,
                    "db": S.db_status(),
                    "n_objects": len(D.OBJECTS),
                    "n_experts": len(D.EXPERTS),
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
            _send_html(self, _error_page("Метод POST для цього шляху не підтримується."), 405)
        except Exception as exc:  # pragma: no cover
            _send_html(self, _error_page(f"Внутрішня помилка: {exc}"), 500)
