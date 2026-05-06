# -*- coding: utf-8 -*-
"""
Лабораторна робота №5 — Визначення характеристик систем
функціональних пристроїв (ФП).

Варіант 8: Граф ФП = 0 (Рисунок 2 з PDF), продуктивності зі стовпчика №8
Таблиці 1.

Реалізовано:
  * Граф системи з трьома незалежними підсистемами та координатами для SVG;
  * compute() — обчислення завантаженостей p_i = π^(k)/π_i, реальної
    продуктивності r = Σ l_k · π^(k) за першим законом Амдала, аналіз
    несумісності та автоматична генерація сумісних значень π;
  * graph_svg() — server-rendered SVG-візуалізація з підсвіткою бутилок;
  * parse_form_pi() — зчитування π з HTML-форми для інтерактивного режиму.

Все на чистому stdlib — без зовнішніх залежностей.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


# ===========================================================================
# 1. Граф системи (варіант 8 → ФП=0, Рисунок 2 з методички)
# ===========================================================================

GRAPH_V8: Dict = {
    "subsystems": [
        {
            "id": 1,
            "nodes": [0, 1, 2, 3, 4, 5],
            "edges": [(2, 1), (1, 0), (1, 3), (0, 4), (3, 4), (4, 5)],
        },
        {
            "id": 2,
            "nodes": [6, 7, 8, 9],
            "edges": [(9, 6), (9, 7), (6, 7), (7, 8)],
        },
        {
            "id": 3,
            "nodes": [10, 11, 12, 13, 14],
            "edges": [(13, 14), (13, 11), (13, 12), (14, 10), (14, 12)],
        },
    ],
    # Координати у "сітці" SVG; одиниця сітки = cell px (за замовчуванням 70).
    # Три підсистеми пліч-о-пліч, наближене відтворення Рис.2 з PDF.
    "layout": {
        # підсистема 1 (X 0.5..2.5)
        2:  (1.5, 0.5),
        1:  (1.5, 1.5),
        0:  (0.5, 2.5),
        3:  (2.5, 2.5),
        4:  (1.5, 3.5),
        5:  (1.5, 4.5),
        # підсистема 2 (X 4.0..6.0)
        9:  (5.0, 0.5),
        6:  (4.0, 2.5),
        7:  (6.0, 2.5),
        8:  (6.0, 4.0),
        # підсистема 3 (X 7.5..10.0)
        13: (8.5, 0.5),
        14: (7.5, 2.0),
        11: (10.0, 2.0),
        10: (7.5, 3.5),
        12: (8.5, 3.5),
    },
}

# Стовпчик №8 з Таблиці 1 методички
PI_V8: List[int] = [7, 6, 9, 12, 8, 5, 6, 8, 4, 8, 7, 6, 9, 12, 5]

N_DEVICES = 15


# ===========================================================================
# 2. Обчислення характеристик системи
# ===========================================================================

def compute(pi: Sequence[float], graph: Dict = GRAPH_V8) -> Dict:
    """
    Повний звіт характеристик системи функціональних пристроїв.

    Параметри:
        pi    — пікові продуктивності всіх N_DEVICES = 15 пристроїв.
        graph — структура графа (за замовчуванням GRAPH_V8 для варіанта 8).

    Алгоритм (перший закон Амдала):
        1. Для кожної підсистеми k:
              π^(k) = min(π_i для i ∈ підсистема_k)   — реальна продуктивність,
              r^(k) = l_k · π^(k)                      — внесок підсистеми,
              p_i   = π^(k) / π_i для всіх i ∈ підсистема — завантаженість.
        2. Реальна продуктивність системи: r = Σ_k r^(k).
        3. Несумісність — пристрої з π_i > π^(k); вони простоюють.
        4. Сумісна система — всі π_i у підсистемі однакові; алгоритм
           пропонує дві стратегії: «вниз» до min та «вгору» до max.
    """
    pi = [float(v) for v in pi]
    if len(pi) != N_DEVICES:
        raise ValueError(f"Очікується {N_DEVICES} значень π, отримано {len(pi)}")
    if any(v <= 0 for v in pi):
        raise ValueError("Усі π_i мають бути > 0")

    subsystems_out: List[Dict] = []
    bottlenecks: List[Dict] = []
    incompatibilities: List[Dict] = []
    causes: List[str] = []
    suggestion_down = list(pi)
    suggestion_up = list(pi)

    total_real = 0.0
    sum_peak = sum(pi)

    for sub in graph["subsystems"]:
        nodes: List[int] = sub["nodes"]
        node_pis = [(n, pi[n]) for n in nodes]
        min_pi = min(p for _, p in node_pis)
        max_pi = max(p for _, p in node_pis)
        min_nodes = [n for n, p in node_pis if p == min_pi]
        l_count = len(nodes)
        sub_real = l_count * min_pi
        total_real += sub_real

        loads: List[Dict] = []
        underload_nodes: List[Tuple[int, float, float]] = []
        for n in nodes:
            p_val = pi[n]
            p_load = min_pi / p_val
            is_min = p_val == min_pi
            wasted = p_val - min_pi
            loads.append({
                "node": n,
                "pi": p_val,
                "p": p_load,
                "is_min": is_min,
                "wasted": wasted,
            })
            if not is_min:
                incompatibilities.append({
                    "subsys": sub["id"],
                    "node": n,
                    "pi": p_val,
                    "p": p_load,
                    "underload": 1.0 - p_load,
                    "wasted": wasted,
                })
                underload_nodes.append((n, p_val, p_load))

        for n in min_nodes:
            bottlenecks.append({"subsys": sub["id"], "node": n, "pi": min_pi})

        for n in nodes:
            suggestion_down[n] = min_pi
            suggestion_up[n] = max_pi

        if underload_nodes:
            details = ", ".join(
                f"вузол {n} (π={_fmt(p)}, p={pl * 100:.1f}%)"
                for n, p, pl in underload_nodes
            )
            min_str = ", ".join(str(n) for n in min_nodes)
            verb = "ють" if len(min_nodes) > 1 else "є"
            i_suffix = "і" if len(min_nodes) > 1 else ""
            causes.append(
                f"Підсистема {sub['id']}: пристрій{i_suffix} {min_str} "
                f"з π={_fmt(min_pi)} обмежу{verb} всю підсистему. "
                f"Інші пристрої простоюють: {details}."
            )

        subsystems_out.append({
            "id": sub["id"],
            "nodes": nodes,
            "min_pi": min_pi,
            "max_pi": max_pi,
            "min_nodes": min_nodes,
            "device_count": l_count,
            "real_productivity": sub_real,
            "loads": loads,
        })

    return {
        "subsystems": subsystems_out,
        "total_real": total_real,
        "sum_peak": sum_peak,
        "utilization": total_real / sum_peak if sum_peak else 0,
        "bottlenecks": bottlenecks,
        "incompatibilities": incompatibilities,
        "causes": causes,
        "suggestion_down": suggestion_down,
        "suggestion_up": suggestion_up,
        "is_compatible": len(incompatibilities) == 0,
    }


def _fmt(v: float) -> str:
    """Друкує число без зайвого .0 для цілих."""
    if float(v).is_integer():
        return str(int(v))
    return f"{v:.2f}"


# ===========================================================================
# 3. Візуалізація графа — server-rendered SVG
# ===========================================================================

def graph_svg(report: Dict, graph: Dict = GRAPH_V8,
              cell: int = 70, pad_x: int = 30, pad_y: int = 36) -> str:
    """
    SVG-зображення графа системи з трьома підсистемами пліч-о-пліч.

    Кольори вузлів:
      бутилка (π = π^(k))         — червоний
      решта при p < 1             — синій
      повністю завантажений ≠ min — зелений (рідкий випадок)
    """
    layout = graph["layout"]
    max_x = max(x for x, _ in layout.values())
    max_y = max(y for _, y in layout.values())
    width = int(pad_x * 2 + (max_x + 0.5) * cell)
    height = int(pad_y * 2 + (max_y + 0.5) * cell)

    load_by_node: Dict[int, Dict] = {}
    for sub in report["subsystems"]:
        for ld in sub["loads"]:
            load_by_node[ld["node"]] = ld

    def node_style(node: int) -> Tuple[str, str, str]:
        ld = load_by_node[node]
        if ld["is_min"]:
            return ("#fee2e2", "#991b1b", "#7f1d1d")
        if ld["p"] >= 0.9999:
            return ("#dcfce7", "#166534", "#14532d")
        return ("#eef2ff", "#4338ca", "#312e81")

    def pix(node: int) -> Tuple[int, int]:
        x, y = layout[node]
        return int(pad_x + x * cell), int(pad_y + y * cell)

    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'style="width:100%;max-width:{width}px;height:auto;'
        f'background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;'
        f'display:block;margin:0 auto">',
        '<defs>'
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>'
        '</marker>'
        '</defs>',
    ]

    for sub_def, sub_rep in zip(graph["subsystems"], report["subsystems"]):
        xs = [layout[n][0] for n in sub_def["nodes"]]
        cx_label = pad_x + (sum(xs) / len(xs)) * cell
        parts.append(
            f'<text x="{cx_label:.0f}" y="22" text-anchor="middle" '
            f'font-size="13" fill="#312e81" font-weight="600">'
            f'Підсистема {sub_def["id"]} · '
            f'π⁽{sub_def["id"]}⁾={_fmt(sub_rep["min_pi"])} · '
            f'l={sub_rep["device_count"]} · '
            f'r⁽{sub_def["id"]}⁾={_fmt(sub_rep["real_productivity"])}'
            f'</text>'
        )

    R = 22
    for sub in graph["subsystems"]:
        for src, dst in sub["edges"]:
            x1, y1 = pix(src)
            x2, y2 = pix(dst)
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
                f'stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>'
            )

    for sub in graph["subsystems"]:
        for n in sub["nodes"]:
            cx, cy = pix(n)
            bg, stroke, tcolor = node_style(n)
            ld = load_by_node[n]
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{R}" '
                f'fill="{bg}" stroke="{stroke}" stroke-width="2"/>'
            )
            parts.append(
                f'<text x="{cx}" y="{cy + 1}" text-anchor="middle" '
                f'dominant-baseline="middle" font-weight="700" font-size="14" '
                f'fill="{tcolor}">{n}</text>'
            )
            parts.append(
                f'<text x="{cx}" y="{cy + R + 14}" text-anchor="middle" '
                f'font-size="11" fill="#334155">π={_fmt(ld["pi"])}</text>'
            )

    parts.append('</svg>')
    return "".join(parts)


# ===========================================================================
# 4. Парсинг HTML-форми (для інтерактивного режиму)
# ===========================================================================

def parse_form_pi(form: Dict[str, List[str]]) -> List[float]:
    """
    Зчитує π_0..π_(N-1) із результатів urllib.parse.parse_qs.
    Повертає список значень або кидає ValueError із зрозумілим повідомленням.
    """
    out: List[float] = []
    for i in range(N_DEVICES):
        key = f"pi_{i}"
        val_list = form.get(key, [])
        if not val_list:
            raise ValueError(f"Поле π_{i} відсутнє у формі")
        raw = val_list[0].strip().replace(",", ".")
        try:
            v = float(raw)
        except ValueError:
            raise ValueError(f"π_{i}: «{raw}» — не число")
        if v <= 0:
            raise ValueError(f"π_{i}: значення має бути > 0 (отримано {raw})")
        out.append(v)
    return out
