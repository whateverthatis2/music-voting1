# -*- coding: utf-8 -*-
"""
HTML-шаблони лабораторної.

Стиль свідомо стриманий — академічний колірний градієнт, чітка типографіка,
таблиці із зебра-розміткою, ніяких емоджі-надлишку. Розмітка зібрана
у ваніль-HTML без зовнішніх залежностей, щоб сторінка завантажувалася
і працювала навіть при «холодному» Vercel.
"""

from __future__ import annotations

from typing import Iterable, Sequence


CSS = r"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  background:#f1f5f9;color:#0f172a;line-height:1.55;font-size:15px}
a{color:#4338ca;text-decoration:none}
a:hover{text-decoration:underline}
.app{max-width:1240px;margin:0 auto;padding:24px}
header.topbar{background:linear-gradient(135deg,#312e81 0%,#4338ca 60%,#6366f1 100%);
  color:#fff;border-radius:14px;padding:24px 28px;margin-bottom:22px;
  box-shadow:0 14px 40px -16px rgba(49,46,129,.55)}
header.topbar h1{font-size:1.55rem;letter-spacing:.2px}
header.topbar p{opacity:.85;margin-top:4px;font-size:.95rem}
nav.tabs{display:flex;flex-wrap:wrap;gap:6px;margin-top:18px}
nav.tabs a{background:rgba(255,255,255,.13);color:#fff;padding:8px 14px;
  border-radius:999px;font-size:.88rem;font-weight:500;transition:background .15s}
nav.tabs a:hover{background:rgba(255,255,255,.25);text-decoration:none}
nav.tabs a.active{background:#fff;color:#312e81}
.card{background:#fff;border-radius:12px;padding:22px 26px;margin-bottom:18px;
  box-shadow:0 1px 2px rgba(15,23,42,.05),0 6px 22px -12px rgba(15,23,42,.18);
  border:1px solid #e2e8f0}
.card h2{font-size:1.2rem;margin-bottom:6px;color:#1e1b4b}
.card h3{font-size:1.02rem;margin:18px 0 8px;color:#312e81}
.card p{color:#334155}
.muted{color:#64748b;font-size:.9rem}
.lead{color:#475569;margin-bottom:14px}
.kbd{font-family:'SFMono-Regular',Menlo,Consolas,monospace;background:#eef2ff;
  border-radius:4px;padding:1px 6px;font-size:.86em;color:#3730a3}
.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.78rem;
  font-weight:600;letter-spacing:.2px}
.tag.green{background:#dcfce7;color:#166534}
.tag.red{background:#fee2e2;color:#991b1b}
.tag.amber{background:#fef3c7;color:#92400e}
.tag.indigo{background:#e0e7ff;color:#3730a3}
.tag.slate{background:#e2e8f0;color:#1e293b}
.grid{display:grid;gap:18px}
.grid.cols-2{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.grid.cols-3{grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.stat{background:#eef2ff;border-radius:10px;padding:14px 16px;
  border-left:4px solid #4f46e5}
.stat .v{font-size:1.55rem;font-weight:700;color:#312e81}
.stat .l{font-size:.82rem;color:#475569;text-transform:uppercase;letter-spacing:.6px}
table{width:100%;border-collapse:collapse;margin-top:10px;background:#fff;
  font-size:.88rem;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #e2e8f0;
  vertical-align:middle}
th{background:#eef2ff;color:#312e81;font-weight:600;text-transform:uppercase;
  letter-spacing:.4px;font-size:.74rem}
tbody tr:nth-child(even){background:#f8fafc}
tbody tr:hover{background:#eef2ff}
table.compact th,table.compact td{padding:6px 8px;font-size:.82rem}
table.matrix td{font-family:'SFMono-Regular',Menlo,Consolas,monospace;
  text-align:center;font-variant-numeric:tabular-nums}
table.matrix th{text-align:center}
table.matrix td.zero{color:#94a3b8}
table.matrix td.head{background:#f8fafc;color:#475569;font-weight:600;text-align:left}
.median{background:#dcfce7 !important;font-weight:600}
.alert{padding:14px 16px;border-radius:8px;border-left:4px solid;margin-bottom:12px}
.alert.info{background:#eff6ff;border-color:#3b82f6;color:#1e3a8a}
.alert.warn{background:#fffbeb;border-color:#f59e0b;color:#92400e}
.alert.error{background:#fef2f2;border-color:#ef4444;color:#991b1b}
.alert.ok{background:#ecfdf5;border-color:#10b981;color:#065f46}
.ranking{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.ranking span.rk{display:inline-flex;align-items:center;gap:6px;
  background:#f1f5f9;color:#0f172a;border:1px solid #e2e8f0;
  padding:5px 11px;border-radius:8px;font-size:.86rem;font-weight:500}
.ranking span.rk b{color:#4338ca;font-size:.78rem}
.arrow{color:#94a3b8;font-size:.85em;font-weight:bold}
.btn{display:inline-flex;align-items:center;gap:6px;background:#4f46e5;
  color:#fff;padding:10px 18px;border:none;border-radius:8px;font-weight:600;
  cursor:pointer;font-size:.92rem;text-decoration:none;transition:background .15s}
.btn:hover{background:#4338ca;text-decoration:none;color:#fff}
.btn.secondary{background:#fff;color:#4338ca;border:1px solid #c7d2fe}
.btn.secondary:hover{background:#eef2ff}
.btn[disabled]{opacity:.5;cursor:not-allowed}
.note{font-size:.85rem;color:#64748b;margin-top:8px;font-style:italic}
.code-block{background:#0f172a;color:#f1f5f9;padding:14px 18px;border-radius:8px;
  font-family:'SFMono-Regular',Menlo,Consolas,monospace;font-size:.82rem;
  overflow-x:auto;margin-top:10px;line-height:1.6}
.subexperts{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.subexperts .e{background:#eef2ff;border:1px solid #c7d2fe;color:#3730a3;
  padding:4px 10px;border-radius:6px;font-size:.8rem}
.bar{display:flex;align-items:center;gap:8px;margin:3px 0}
.bar .lbl{flex:0 0 90px;font-size:.82rem;color:#475569}
.bar .track{flex:1;height:14px;background:#eef2ff;border-radius:7px;overflow:hidden}
.bar .fill{height:100%;background:linear-gradient(90deg,#6366f1,#312e81);
  border-radius:7px}
.bar .v{flex:0 0 36px;text-align:right;font-size:.82rem;color:#312e81;font-weight:600}
.foot{text-align:center;color:#64748b;padding:18px 8px;font-size:.85rem}
.kpi{display:flex;gap:14px;flex-wrap:wrap;margin-top:8px}
.kpi .item{background:#fff;border:1px solid #e2e8f0;border-radius:8px;
  padding:10px 14px;min-width:130px}
.kpi .item .l{color:#64748b;font-size:.74rem;text-transform:uppercase;letter-spacing:.5px}
.kpi .item .v{color:#0f172a;font-size:1.18rem;font-weight:700;margin-top:2px}
input[type=password],input[type=text]{width:100%;padding:10px 12px;
  border:1px solid #cbd5e1;border-radius:8px;font-size:.95rem}
form.inline{display:flex;gap:8px;align-items:center}
"""


# ---------------------------------------------------------------------------
# Набори вкладок для сторінок
# ---------------------------------------------------------------------------
LAB4_TABS = [
    ("home_l4",       "/lab4",          "Огляд"),
    ("data",          "/data",          "Дані Лаб.1-2"),
    ("distributed",   "/distributed",   "Розподілений перебір"),
    ("satisfaction",  "/satisfaction",  "Індекси задоволеності"),
    ("large",         "/large",         "n ≫ 12 · ГА"),
    ("protocol",      "/protocol",      "Протокол"),
]

LAB5_TABS = [
    ("home_l5",       "/lab5",          "Огляд Лаб.5"),
]

LAB6_TABS = [
    ("home_l6",       "/lab6",          "Огляд Лаб.6"),
]

LAB7_TABS = [
    ("home_l7",       "/lab7",          "Огляд Лаб.7"),
]

LAB8_TABS = [
    ("home_l8",       "/lab8",          "Огляд Лаб.8"),
]

HUB_TABS = [
    ("hub",           "/",              "Усі лабораторні"),
    ("hub_l4",        "/lab4",          "Лаб.4"),
    ("hub_l5",        "/lab5",          "Лаб.5"),
    ("hub_l6",        "/lab6",          "Лаб.6"),
    ("hub_l7",        "/lab7",          "Лаб.7"),
    ("hub_l8",        "/lab8",          "Лаб.8"),
]


_HEADERS = {
    0: ("ІОД РІС · лабораторні роботи",
        "Інтелектуальна обробка даних в розподілених інформаційних середовищах · КН-41"),
    4: ("Лабораторна робота №4 — розподілені обчислення компромісних ранжувань",
        "Інтелектуальна обробка даних в розподілених інформаційних середовищах · КН-41"),
    5: ("Лабораторна робота №5 — характеристики систем функціональних пристроїв",
        "Інтелектуальна обробка даних в розподілених інформаційних середовищах · КН-41"),
    6: ("Лабораторна робота №6 — характеристики систем ФП (продовження)",
        "Інтелектуальна обробка даних в розподілених інформаційних середовищах · КН-41"),
    7: ("Лабораторна робота №7 — максимальне прискорення і ефективність системи",
        "Інтелектуальна обробка даних в розподілених інформаційних середовищах · КН-41"),
    8: ("Лабораторна робота №8 — максимальне прискорення системи (закони Амдала 2 і 3)",
        "Інтелектуальна обробка даних в розподілених інформаційних середовищах · КН-41"),
}


# ---------------------------------------------------------------------------
# Базовий каркас сторінки
# ---------------------------------------------------------------------------
def page(title: str, body: str, active: str = "",
         lab_num: int = 4, tabs: list | None = None) -> str:
    if tabs is None:
        tabs = LAB4_TABS
    h1, sub = _HEADERS.get(lab_num, _HEADERS[4])
    title_suffix = "ІОД РІС" if lab_num == 0 else f"Лабораторна №{lab_num}"
    nav_html = "".join(
        f'<a href="{href}" class="{ "active" if key == active else "" }">{name}</a>'
        for key, href, name in tabs
    )
    return f"""<!DOCTYPE html>
<html lang="uk"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {title_suffix}</title>
<style>{CSS}</style></head>
<body><div class="app">
<header class="topbar">
  <h1>{h1}</h1>
  <p>{sub}</p>
  <nav class="tabs">{nav_html}</nav>
</header>
{body}
<div class="foot">Грущенко Василь · Київ — 2026 · кафедра інтелектуальних технологій</div>
</div></body></html>"""


# ---------------------------------------------------------------------------
# Компоненти-рендерери
# ---------------------------------------------------------------------------
def ranking_chips(ranking: Sequence[str]) -> str:
    items = "".join(
        f'<span class="rk"><b>{i + 1}</b>{obj}</span>'
        f'{"<span class=arrow>›</span>" if i < len(ranking) - 1 else ""}'
        for i, obj in enumerate(ranking)
    )
    return f'<div class="ranking">{items}</div>'


def matrix_table(headers: Sequence[str], rows: Iterable[Sequence],
                 row_labels: Sequence[str] = (), highlight_rows=()) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = []
    for i, row in enumerate(rows):
        cells = []
        if row_labels:
            cells.append(f'<td class="head">{row_labels[i]}</td>')
        for v in row:
            cls = "zero" if v == 0 else ""
            cells.append(f'<td class="{cls}">{v}</td>')
        cls_tr = "median" if i in highlight_rows else ""
        body_rows.append(f'<tr class="{cls_tr}">{"".join(cells)}</tr>')
    th_pre = "<th></th>" if row_labels else ""
    return (f'<table class="matrix compact"><thead><tr>{th_pre}{head}</tr></thead>'
            f'<tbody>{"".join(body_rows)}</tbody></table>')


def table(headers: Sequence[str], rows: Iterable[Sequence]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        for r in rows
    )
    return (f"<table><thead><tr>{head}</tr></thead>"
            f"<tbody>{body_rows}</tbody></table>")


def stat(label: str, value) -> str:
    return f'<div class="stat"><div class="v">{value}</div><div class="l">{label}</div></div>'


def alert(text: str, kind: str = "info") -> str:
    return f'<div class="alert {kind}">{text}</div>'


def bar_chart(items: Sequence[tuple], maximum: float | None = None) -> str:
    """items: список (label, value)."""
    if not items:
        return ""
    mx = maximum or max(v for _, v in items) or 1
    rows = []
    for lbl, v in items:
        pct = max(0, min(100, 100 * v / mx))
        rows.append(
            f'<div class="bar"><div class="lbl">{lbl}</div>'
            f'<div class="track"><div class="fill" style="width:{pct:.1f}%"></div></div>'
            f'<div class="v">{v}</div></div>'
        )
    return "".join(rows)
