# -*- coding: utf-8 -*-
"""
Лабораторна робота №7 — Визначення максимально можливого
прискорення і ефективності системи (закони Амдала).

Варіант 8 → Рисунок №4 (за таблицею варіантів з PDF).

Постановка задачі:
  Усі пристрої однакові, прості, універсальні. Алгоритм має паралельну форму
  висоти m і ширини q, всього N операцій, із них n послідовних.

Формули:
  β   = n / N                              — частка послідовних обчислень
  R_s = s / (β·s + (1 − β))                — 2-й закон Амдала (прискорення на s проц.)
  E_s = R_s / s                            — ефективність системи з s процесорів
  R_max = N/m  (досягається при s = q)
  R_∞ ≤ 1/β                                — 3-й закон Амдала (теоретична межа)

Усі п'ять графів з PDF Лаб.7 представлені у структурованому вигляді:
  — tiers: список ярусів (кожен ярус = список вузлів, що виконуються паралельно)
  — edges: список орієнтованих ребер (між послідовними ярусами)

Сама структура tiers однозначно дає N, n, q, m:
  N = total nodes
  n = кількість ярусів з шириною 1 (послідовні операції)
  q = max(len(tier))
  m = len(tiers)
"""

from __future__ import annotations

from typing import Dict, List, Tuple


# ===========================================================================
# 1. Усі п'ять графів з PDF Лаб.7
# ===========================================================================

def _build_diamond(in_node: str, parallel: List[str], out_node: str
                   ) -> List[Tuple[str, str]]:
    """Ребра діаманта: in → кожен паралельний → out."""
    return [(in_node, p) for p in parallel] + [(p, out_node) for p in parallel]


def _build_chain_diamond(in_node: str, chains: List[List[str]],
                         out_node: str) -> List[Tuple[str, str]]:
    """
    Ребра діаманта з ланцюгами: in → перший вузол кожного ланцюга;
    усередині ланцюга — послідовно; останній вузол ланцюга → out.
    """
    edges: List[Tuple[str, str]] = []
    for chain in chains:
        edges.append((in_node, chain[0]))
        for a, b in zip(chain[:-1], chain[1:]):
            edges.append((a, b))
        edges.append((chain[-1], out_node))
    return edges


# Рисунок 1 — приклад з методички (для перевірки): N=15, n=6, q=3
_FIG1_TIERS = [
    ["a"], ["b"],
    ["c1", "c2", "c3"],
    ["d"],
    ["e1", "e2", "e3"],
    ["f"],
    ["g1", "g2", "g3"],
    ["h"], ["i"],
]
_FIG1_EDGES = (
    [("a", "b")] +
    _build_diamond("b", ["c1", "c2", "c3"], "d") +
    _build_diamond("d", ["e1", "e2", "e3"], "f") +
    _build_diamond("f", ["g1", "g2", "g3"], "h") +
    [("h", "i")]
)

# Рисунок 2 — N=16, n=5, q=4 (1 input + diamond[4×2] + middle + diamond[3])
_FIG2_TIERS = [
    ["a"], ["b"],
    ["c1", "c2", "c3", "c4"],
    ["d1", "d2", "d3", "d4"],
    ["e"], ["f"],
    ["g1", "g2", "g3"],
    ["h"],
]
_FIG2_EDGES = (
    [("a", "b")] +
    _build_chain_diamond("b",
                         [["c1", "d1"], ["c2", "d2"], ["c3", "d3"], ["c4", "d4"]],
                         "e") +
    [("e", "f")] +
    _build_diamond("f", ["g1", "g2", "g3"], "h")
)

# Рисунок 3 — N=16, n=4, q=4
_FIG3_TIERS = [
    ["a"],
    ["b1", "b2", "b3", "b4"],
    ["c"], ["d"],
    ["e1", "e2", "e3", "e4"],
    ["f1", "f2", "f3", "f4"],
    ["g"],
]
_FIG3_EDGES = (
    _build_diamond("a", ["b1", "b2", "b3", "b4"], "c") +
    [("c", "d")] +
    _build_chain_diamond("d",
                         [["e1", "f1"], ["e2", "f2"], ["e3", "f3"], ["e4", "f4"]],
                         "g")
)

# Рисунок 4 — варіант 8: N=17, n=5, q=4 (= Fig.3 + 1 trailing node)
_FIG4_TIERS = [
    ["a"],
    ["b1", "b2", "b3", "b4"],
    ["c"], ["d"],
    ["e1", "e2", "e3", "e4"],
    ["f1", "f2", "f3", "f4"],
    ["g"], ["h"],
]
_FIG4_EDGES = (
    _build_diamond("a", ["b1", "b2", "b3", "b4"], "c") +
    [("c", "d")] +
    _build_chain_diamond("d",
                         [["e1", "f1"], ["e2", "f2"], ["e3", "f3"], ["e4", "f4"]],
                         "g") +
    [("g", "h")]
)

# Рисунок 5 — N=17, n=5, q=4 (1 input + middle + diamond[4] + middle + diamond[4×2])
_FIG5_TIERS = [
    ["a"], ["b"],
    ["c1", "c2", "c3", "c4"],
    ["d"], ["e"],
    ["f1", "f2", "f3", "f4"],
    ["g1", "g2", "g3", "g4"],
    ["h"],
]
_FIG5_EDGES = (
    [("a", "b")] +
    _build_diamond("b", ["c1", "c2", "c3", "c4"], "d") +
    [("d", "e")] +
    _build_chain_diamond("e",
                         [["f1", "g1"], ["f2", "g2"], ["f3", "g3"], ["f4", "g4"]],
                         "h")
)


def _figure(idx: int, title: str, tiers, edges) -> Dict:
    N = sum(len(t) for t in tiers)
    n = sum(1 for t in tiers if len(t) == 1)
    q = max(len(t) for t in tiers)
    m = len(tiers)
    return {
        "id": idx,
        "title": title,
        "tiers": tiers,
        "edges": list(edges),
        "N": N, "n": n, "q": q, "m": m,
    }


FIGURES: Dict[int, Dict] = {
    1: _figure(1, "Рис.1 · приклад з методички", _FIG1_TIERS, _FIG1_EDGES),
    2: _figure(2, "Рис.2 · граф системи 2",       _FIG2_TIERS, _FIG2_EDGES),
    3: _figure(3, "Рис.3 · граф системи 3",       _FIG3_TIERS, _FIG3_EDGES),
    4: _figure(4, "Рис.4 · граф системи 4 (варіант 8)", _FIG4_TIERS, _FIG4_EDGES),
    5: _figure(5, "Рис.5 · граф системи 5",       _FIG5_TIERS, _FIG5_EDGES),
}

# Варіант 8 з таблиці PDF: рисунок 4
DEFAULT_FIGURE = 4


# ===========================================================================
# 2. Обчислення характеристик (закони Амдала)
# ===========================================================================

def compute(N: int, n: int, s: int) -> Dict:
    """
    Повертає словник з усіма характеристиками системи.

    Формули:
      β   = n / N
      R_s = s / (β·s + 1 − β)              — 2-й закон Амдала
      E_s = R_s / s
      R_∞ = 1 / β   (при β > 0)           — 3-й закон Амдала
    """
    N = int(N)
    n = int(n)
    s = int(s)
    if N <= 0:
        raise ValueError(f"N має бути > 0 (отримано {N})")
    if not (0 <= n <= N):
        raise ValueError(f"n має бути в [0, {N}] (отримано {n})")
    if s < 1:
        raise ValueError(f"s має бути ≥ 1 (отримано {s})")

    beta = n / N
    n_par = N - n  # кількість паралельних операцій
    denom = beta * s + (1 - beta)
    R_s = s / denom if denom > 0 else float("inf")
    E_s = R_s / s
    R_inf = 1.0 / beta if beta > 0 else float("inf")

    # «Ідеальний» час: послідовно n + паралельно (N-n)/s
    T_seq_total = N             # на 1 проц.
    T_par_on_s = n + n_par / s  # на s проц., поточно при ідеальному завантаженні
    R_check = T_seq_total / T_par_on_s if T_par_on_s > 0 else 0
    # R_check має дорівнювати R_s (це той самий результат через еквівалентну формулу)

    return {
        "N": N,
        "n": n,
        "n_par": n_par,
        "s": s,
        "beta": beta,
        "beta_str": f"{n}/{N}",
        "R_s": R_s,
        "E_s": E_s,
        "R_inf": R_inf,
        "T_seq": T_seq_total,
        "T_par": T_par_on_s,
        "R_check": R_check,  # для self-test, має == R_s
    }


# ===========================================================================
# 3. SVG-візуалізація графа алгоритму
# ===========================================================================

def graph_svg(figure: Dict, cell_x: int = 90, cell_y: int = 60,
              pad_x: int = 30, pad_y: int = 30, R: int = 18) -> str:
    """
    Малює граф алгоритму як SVG: тиери — стовпчики зліва направо;
    кожен вузол — кружечок з номером (для зручності — за порядком обходу).

    Кольори:
      послідовні (одинокі в ярусі) — амбер (вузьке місце для паралелізму)
      паралельні                    — індиго
    """
    tiers: List[List[str]] = figure["tiers"]
    edges: List[Tuple[str, str]] = figure["edges"]
    n_tiers = len(tiers)
    max_h = max(len(t) for t in tiers)

    width = pad_x * 2 + (n_tiers - 1) * cell_x
    height = pad_y * 2 + max(0, max_h - 1) * cell_y

    # позиції вузлів
    pos: Dict[str, Tuple[int, int]] = {}
    is_sequential: Dict[str, bool] = {}
    label_order: Dict[str, int] = {}
    counter = 1
    for i, tier in enumerate(tiers):
        x = pad_x + i * cell_x
        center_y = pad_y + (max_h - 1) * cell_y / 2
        for j, node in enumerate(tier):
            offset = (j - (len(tier) - 1) / 2) * cell_y
            pos[node] = (int(x), int(center_y + offset))
            is_sequential[node] = (len(tier) == 1)
            label_order[node] = counter
            counter += 1

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'style="width:100%;max-width:{width}px;height:auto;'
        f'background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;'
        f'display:block;margin:0 auto">',
        '<defs>'
        '<marker id="arrow7" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>'
        '</marker>'
        '</defs>',
    ]

    # ребра
    for src, dst in edges:
        x1, y1 = pos[src]
        x2, y2 = pos[dst]
        dx, dy = x2 - x1, y2 - y1
        dist = (dx * dx + dy * dy) ** 0.5 or 1.0
        ux, uy = dx / dist, dy / dist
        sx = x1 + ux * R
        sy = y1 + uy * R
        ex = x2 - ux * R
        ey = y2 - uy * R
        parts.append(
            f'<line x1="{sx:.0f}" y1="{sy:.0f}" '
            f'x2="{ex:.0f}" y2="{ey:.0f}" '
            f'stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow7)"/>'
        )

    # вузли
    for node, (cx, cy) in pos.items():
        if is_sequential[node]:
            bg, stroke, tcolor = ("#fef3c7", "#92400e", "#78350f")
        else:
            bg, stroke, tcolor = ("#eef2ff", "#4338ca", "#312e81")
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{R}" '
            f'fill="{bg}" stroke="{stroke}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{cx}" y="{cy + 1}" text-anchor="middle" '
            f'dominant-baseline="middle" font-weight="700" font-size="12" '
            f'fill="{tcolor}">{label_order[node]}</text>'
        )

    parts.append('</svg>')
    return "".join(parts)


# ===========================================================================
# 4. Парсинг HTML-форми
# ===========================================================================

def parse_form(form: Dict[str, List[str]]) -> Tuple[int, int, int, int]:
    """Зчитує (figure_id, N, n, s) з форми. figure_id 1..5; N, n, s — int > 0."""
    fig_id = int(form.get("figure", [str(DEFAULT_FIGURE)])[0])
    if fig_id not in FIGURES:
        raise ValueError(f"Невідомий рисунок: {fig_id}")

    def _int(key: str) -> int:
        raw = form.get(key, [""])[0].strip()
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"{key}: «{raw}» — не ціле число")

    N = _int("N")
    n = _int("n")
    s = _int("s")
    return fig_id, N, n, s
