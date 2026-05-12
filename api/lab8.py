# -*- coding: utf-8 -*-
"""
Лабораторна робота №8 — Визначення максимального прискорення для
системи (2-й і 3-й закони Амдала).

На відміну від Лаб.5/6/7 — тут НЕМАЄ графа алгоритму. Це чисто числова
задача: відома частка паралельних обчислень (1−β) і кількість
процесорів l, треба знайти прискорення S_l та діапазон l для заданих
відсотків від теоретичного максимуму S_max.

Формули (закони Амдала):
    β       = 1 − (1−β)                        — частка послідовних обчислень
    S_max   = 1 / β                            — 3-й закон Амдала
    S_l     = l / (β·l + (1−β))                — 2-й закон Амдала
    E_l     = S_l / l                          — ефективність

Зворотна задача (знайти l за заданим a):
    S_l ≥ a · S_max
    l ≥ a · (1−β) / (β · (1−a))

Для Лаб.8 ще треба: «знайти несумісність, причини, запропонувати
сумісний/несумісний варіант».

Варіант 8 з Таблиці 1: (1−β)=0.75, l=12, потрібно 85%-95%.
  S_max = 4, S_12 = 3.2 = 80% (< 85% → несумісність).
  Сумісний діапазон l ∈ [17, 57].
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


# ===========================================================================
# 1. Варіанти з Таблиць 1-3 (всього 30 варіантів)
# ===========================================================================
# Кожен варіант: (parallel_share, l, a1_percent, a2_percent)

VARIANTS: Dict[int, Dict] = {
    # Таблиця 1 (варіанти 1-10)
    1:  {"parallel_share": 0.75, "l":  6, "a1": 60, "a2": 95},
    2:  {"parallel_share": 0.33, "l": 10, "a1": 80, "a2": 90},
    3:  {"parallel_share": 0.30, "l":  7, "a1": 15, "a2": 20},
    4:  {"parallel_share": 0.25, "l":  8, "a1": 85, "a2": 90},
    5:  {"parallel_share": 0.60, "l": 20, "a1": 70, "a2": 85},
    6:  {"parallel_share": 0.70, "l":  9, "a1": 85, "a2": 90},
    7:  {"parallel_share": 0.40, "l": 11, "a1": 15, "a2": 25},
    8:  {"parallel_share": 0.75, "l": 12, "a1": 85, "a2": 95},
    9:  {"parallel_share": 0.50, "l": 14, "a1": 75, "a2": 85},
    10: {"parallel_share": 0.65, "l":  9, "a1": 65, "a2": 90},
    # Таблиця 2 (варіанти 11-20)
    11: {"parallel_share": 0.50, "l": 16, "a1": 85, "a2": 90},
    12: {"parallel_share": 0.65, "l": 12, "a1": 15, "a2": 25},
    13: {"parallel_share": 0.60, "l": 17, "a1": 85, "a2": 95},
    14: {"parallel_share": 0.70, "l": 18, "a1": 75, "a2": 85},
    15: {"parallel_share": 0.65, "l": 14, "a1": 65, "a2": 90},
    16: {"parallel_share": 0.75, "l":  7, "a1": 60, "a2": 95},
    17: {"parallel_share": 0.45, "l": 13, "a1": 80, "a2": 90},
    18: {"parallel_share": 0.35, "l": 15, "a1": 15, "a2": 20},
    19: {"parallel_share": 0.50, "l": 11, "a1": 85, "a2": 90},
    20: {"parallel_share": 0.65, "l":  8, "a1": 70, "a2": 85},
    # Таблиця 3 (варіанти 21-30)
    21: {"parallel_share": 0.75, "l":  8, "a1": 80, "a2": 90},
    22: {"parallel_share": 0.45, "l": 20, "a1": 15, "a2": 20},
    23: {"parallel_share": 0.35, "l":  9, "a1": 85, "a2": 90},
    24: {"parallel_share": 0.50, "l": 11, "a1": 70, "a2": 85},
    25: {"parallel_share": 0.65, "l": 12, "a1": 85, "a2": 90},
    26: {"parallel_share": 0.50, "l": 10, "a1": 70, "a2": 85},
    27: {"parallel_share": 0.65, "l": 16, "a1": 60, "a2": 95},
    28: {"parallel_share": 0.60, "l": 12, "a1": 80, "a2": 90},
    29: {"parallel_share": 0.70, "l": 17, "a1": 15, "a2": 20},
    30: {"parallel_share": 0.55, "l": 18, "a1": 85, "a2": 90},
}

DEFAULT_VARIANT = 8


# ===========================================================================
# 2. Обчислення характеристик системи
# ===========================================================================

def compute(parallel_share: float, l: int,
            a1_percent: float, a2_percent: float) -> Dict:
    """
    Повертає словник усіх характеристик за законами Амдала.

    parallel_share — частка паралельних обчислень (1-β), у частках одиниці
    l              — кількість процесорів
    a1_percent, a2_percent — потрібний діапазон % від S_max (наприклад, 85, 95)
    """
    if not (0 < parallel_share < 1):
        raise ValueError(
            f"Частка паралельних має бути в (0, 1), отримано {parallel_share}")
    if l < 1:
        raise ValueError(f"l має бути ≥ 1 (отримано {l})")
    if not (0 < a1_percent < 100) or not (0 < a2_percent < 100):
        raise ValueError(
            f"a1 і a2 мають бути в (0%, 100%) — отримано {a1_percent}/{a2_percent}")
    if a1_percent > a2_percent:
        raise ValueError(
            f"a1 має бути ≤ a2 (отримано {a1_percent} > {a2_percent})")

    beta = 1.0 - parallel_share
    a1 = a1_percent / 100.0
    a2 = a2_percent / 100.0

    # 3-й закон Амдала
    S_max = 1.0 / beta if beta > 0 else float("inf")

    # 2-й закон Амдала
    S_l = l / (beta * l + (1 - beta))
    E_l = S_l / l

    # Поточний % від S_max
    S_l_ratio = S_l / S_max  # = β·l/(β·l + 1-β) = l/(l + (1-β)/β)

    # Зворотна задача:
    #   мінімальне l для S_l ≥ a · S_max:  l ≥ a · (1-β) / (β · (1-a))
    #   максимальне l для S_l ≤ a · S_max: l ≤ a · (1-β) / (β · (1-a))
    # (та сама формула, але різні округлення вгору/вниз)
    # Невелика корекція проти floating-point round-off (напр. 57.0 → 56.9999...)
    _EPS = 1e-9

    def l_min_for(a: float):
        if a >= 1.0:
            return float("inf")
        return math.ceil(a * (1 - beta) / (beta * (1 - a)) - _EPS)

    def l_max_for(a: float):
        if a >= 1.0:
            return float("inf")
        return math.floor(a * (1 - beta) / (beta * (1 - a)) + _EPS)

    l_compat_min = l_min_for(a1)  # перше l, яке досягає a1·S_max
    l_compat_max = l_max_for(a2)  # останнє l, яке ще ≤ a2·S_max
    # Якщо a2 близько до 1.0 — l_compat_max = ∞

    # Чи поточне l входить у [l_compat_min, l_compat_max]?
    is_compatible = (l_compat_min <= l) and (
        l_compat_max is None or l <= l_compat_max
    )

    # Категорія несумісності
    if is_compatible:
        compat_status = "compatible"
        compat_reason = (
            f"Поточне l = {l} забезпечує S_l = {S_l:.4f} = "
            f"{S_l_ratio*100:.2f}% від S_max — це у заданому діапазоні "
            f"[{a1_percent}%, {a2_percent}%]."
        )
    elif S_l_ratio < a1:
        compat_status = "too_few"
        compat_reason = (
            f"Поточне l = {l} дає S_l = {S_l:.4f} = "
            f"{S_l_ratio*100:.2f}% від S_max — це МЕНШЕ за нижню межу "
            f"{a1_percent}% (= {a1*S_max:.4f}). Не вистачає процесорів. "
            f"Мінімум треба l = {l_compat_min}."
        )
    else:  # S_l_ratio > a2
        compat_status = "too_many"
        compat_reason = (
            f"Поточне l = {l} дає S_l = {S_l:.4f} = "
            f"{S_l_ratio*100:.2f}% від S_max — це БІЛЬШЕ за верхню межу "
            f"{a2_percent}% (= {a2*S_max:.4f}). Надмір процесорів — частина "
            f"з них простоює. Максимум l = {l_compat_max}."
        )

    # Запропонувати сумісний варіант (зміна l)
    suggestion_l = l_compat_min  # мінімум, що задовольняє умову (економно)

    # Запропонувати сумісний варіант (зміна β при тому ж l)
    # Хочемо S_l/S_max = a1 при заданому l:
    # l/(l + (1-β)/β) = a1
    # l = a1 · l + a1 · (1-β)/β
    # l(1-a1) = a1 · (1-β)/β
    # β · l(1-a1) = a1·(1-β)
    # β · l(1-a1) + a1·β = a1
    # β · (l(1-a1) + a1) = a1
    # β = a1 / (l(1-a1) + a1)
    suggestion_beta = a1 / (l * (1 - a1) + a1) if l * (1 - a1) + a1 > 0 else None
    suggestion_parallel = 1 - suggestion_beta if suggestion_beta else None

    # Несумісний варіант (для випадку коли поточний СУМІСНИЙ)
    # Просто візьмемо l поза діапазоном
    if is_compatible:
        non_compat_l = max(1, l_compat_min - 1) if l_compat_min > 1 else (
            l_compat_max + 1 if l_compat_max else l + 100
        )
    else:
        non_compat_l = l  # вже несумісний

    # Збір таблиці S_l для різних l (для графіка)
    # вибираємо інформативні значення: 1, 2, 5, 10, given_l, l_compat_min, l_compat_max, 100
    s_table_l_values = sorted(set([
        1, 2, 5, 10,
        l,
        l_compat_min,
        l_compat_max if l_compat_max else 100,
        50, 100, 1000,
    ]))
    s_table_l_values = [v for v in s_table_l_values if v >= 1]
    s_table = []
    for sv in s_table_l_values:
        sv_S = sv / (beta * sv + (1 - beta))
        sv_ratio = sv_S / S_max
        s_table.append({
            "l": sv,
            "S_l": sv_S,
            "ratio": sv_ratio,
            "is_current": sv == l,
            "is_l_min": sv == l_compat_min,
            "is_l_max": (l_compat_max is not None and sv == l_compat_max),
        })

    return {
        "parallel_share": parallel_share,
        "beta": beta,
        "l": l,
        "a1": a1,
        "a2": a2,
        "a1_percent": a1_percent,
        "a2_percent": a2_percent,
        "S_max": S_max,
        "S_l": S_l,
        "E_l": E_l,
        "S_l_ratio": S_l_ratio,
        "S_at_a1": a1 * S_max,
        "S_at_a2": a2 * S_max,
        "l_compat_min": l_compat_min,
        "l_compat_max": l_compat_max,
        "is_compatible": is_compatible,
        "compat_status": compat_status,
        "compat_reason": compat_reason,
        "suggestion_l": suggestion_l,
        "suggestion_parallel": suggestion_parallel,
        "suggestion_beta": suggestion_beta,
        "non_compat_l": non_compat_l,
        "s_table": s_table,
    }


# ===========================================================================
# 3. Візуалізація: SVG-графік S_l(l) з межами
# ===========================================================================

def plot_svg(report: Dict, width: int = 720, height: int = 320,
             pad_l: int = 50, pad_r: int = 30, pad_t: int = 30,
             pad_b: int = 40) -> str:
    """
    SVG-графік S_l як функції l. Показує:
      — криву S_l(l) від l=1 до l_max_x
      — асимптоту S_max (горизонтальна пунктирна)
      — рівні a1·S_max та a2·S_max (горизонтальні штрихові)
      — поточне значення l (вертикальна) та точка на кривій
      — межі сумісного діапазону l_min, l_max
    """
    beta = report["beta"]
    S_max = report["S_max"]
    l = report["l"]
    a1, a2 = report["a1"], report["a2"]
    l_min = report["l_compat_min"]
    l_max = report["l_compat_max"] or (l_min + 50)

    # Діапазон по X: від 1 до max(l_max+10, 2·l, 50)
    x_range = max(int(l_max) + 10 if l_max != float("inf") else 100,
                  2 * l, 50)
    # Діапазон по Y: від 0 до S_max·1.05
    y_range = S_max * 1.1

    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    def x_to_px(xv: float) -> float:
        return pad_l + (xv - 1) / (x_range - 1) * plot_w

    def y_to_px(yv: float) -> float:
        return pad_t + plot_h - (yv / y_range) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'style="width:100%;max-width:{width}px;height:auto;'
        f'background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;'
        f'display:block;margin:0 auto">',
    ]

    # Сітка та осі
    # Y-розмітка: 0, S_at_a1, S_at_a2, S_max
    y_marks = [
        (0, "0", "#94a3b8", "1,2"),
        (a1 * S_max, f"a₁·S_max = {a1*S_max:.2f}", "#f59e0b", "4,3"),
        (a2 * S_max, f"a₂·S_max = {a2*S_max:.2f}", "#f59e0b", "4,3"),
        (S_max, f"S_max = {S_max:.2f}", "#dc2626", "6,4"),
    ]
    for yv, label, color, dash in y_marks:
        py = y_to_px(yv)
        parts.append(
            f'<line x1="{pad_l}" y1="{py:.0f}" '
            f'x2="{width-pad_r}" y2="{py:.0f}" '
            f'stroke="{color}" stroke-width="1" stroke-dasharray="{dash}"/>'
        )
        parts.append(
            f'<text x="{width-pad_r-4}" y="{py-4:.0f}" '
            f'text-anchor="end" font-size="10" fill="{color}" '
            f'font-weight="600">{label}</text>'
        )

    # Вертикальні лінії: l, l_min, l_max
    x_marks = [
        (l, f"l = {l}", "#4338ca", "0"),
        (l_min, f"l_min = {l_min}", "#0891b2", "4,3"),
    ]
    if l_max != float("inf") and l_max != l_min:
        x_marks.append((l_max, f"l_max = {l_max}", "#0891b2", "4,3"))
    for xv, label, color, dash in x_marks:
        if xv > x_range:
            continue
        px = x_to_px(xv)
        parts.append(
            f'<line x1="{px:.0f}" y1="{pad_t}" '
            f'x2="{px:.0f}" y2="{pad_t+plot_h}" '
            f'stroke="{color}" stroke-width="1.2" '
            f'stroke-dasharray="{dash}" opacity="0.7"/>'
        )
        parts.append(
            f'<text x="{px+3:.0f}" y="{pad_t+12}" '
            f'font-size="10" fill="{color}" font-weight="600">{label}</text>'
        )

    # Заштрихована «сумісна» зона: між l_min і l_max
    if l_max != float("inf") and l_max > l_min:
        x1_px = x_to_px(l_min)
        x2_px = x_to_px(min(l_max, x_range))
        y_top = y_to_px(a2 * S_max)
        y_bot = y_to_px(a1 * S_max)
        parts.append(
            f'<rect x="{x1_px:.0f}" y="{y_top:.0f}" '
            f'width="{x2_px-x1_px:.0f}" height="{y_bot-y_top:.0f}" '
            f'fill="#10b981" fill-opacity="0.12" stroke="none"/>'
        )

    # Крива S_l(l)
    points = []
    n_steps = 200
    for i in range(n_steps + 1):
        xv = 1 + i * (x_range - 1) / n_steps
        yv = xv / (beta * xv + (1 - beta))
        points.append(f"{x_to_px(xv):.0f},{y_to_px(yv):.0f}")
    parts.append(
        f'<polyline points="{" ".join(points)}" '
        f'fill="none" stroke="#4338ca" stroke-width="2"/>'
    )

    # Точка на поточному l
    if l <= x_range:
        px = x_to_px(l)
        py = y_to_px(report["S_l"])
        parts.append(
            f'<circle cx="{px:.0f}" cy="{py:.0f}" r="5" '
            f'fill="#4338ca" stroke="#fff" stroke-width="2"/>'
        )

    # Осі
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t+plot_h}" '
        f'x2="{width-pad_r}" y2="{pad_t+plot_h}" '
        f'stroke="#475569" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{pad_l}" y1="{pad_t}" '
        f'x2="{pad_l}" y2="{pad_t+plot_h}" '
        f'stroke="#475569" stroke-width="1.5"/>'
    )
    # Підписи осей
    parts.append(
        f'<text x="{width-pad_r}" y="{pad_t+plot_h+22}" '
        f'text-anchor="end" font-size="11" fill="#475569">'
        f'l (процесорів)</text>'
    )
    parts.append(
        f'<text x="{pad_l-8}" y="{pad_t-8}" '
        f'font-size="11" fill="#475569">S_l</text>'
    )

    parts.append('</svg>')
    return "".join(parts)


# ===========================================================================
# 4. Парсинг HTML-форми
# ===========================================================================

def parse_form(form: Dict[str, List[str]]) -> Tuple[int, float, int, float, float]:
    """Зчитує (variant_id, parallel_share, l, a1, a2). Кидає ValueError."""
    var_id = int(form.get("variant", [str(DEFAULT_VARIANT)])[0])
    if var_id not in VARIANTS:
        raise ValueError(f"Невідомий варіант: {var_id}")

    def _float(key: str) -> float:
        raw = form.get(key, [""])[0].strip().replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"{key}: «{raw}» — не число")

    def _int(key: str) -> int:
        raw = form.get(key, [""])[0].strip()
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"{key}: «{raw}» — не ціле число")

    parallel = _float("parallel_share")
    l = _int("l")
    a1 = _float("a1")
    a2 = _float("a2")
    return var_id, parallel, l, a1, a2
