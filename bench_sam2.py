#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench_sam2.py — Генерація бенчмаркових даних для Самостійної роботи №2.

Запустити з кореня проекту:
    python bench_sam2.py

Результати:
    sam2_bench_full.json  — n=8..12, exp=10/20/30/50
    sam2_large.json       — n=100/200/500, exp=10/20/30
"""

import json
import math
import sys
import time
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from api.algorithms import evaluate_ranking
from api.lab4 import (
    distributed_genetic_algorithm,
    genetic_algorithm,
    generate_random_problem,
)

# ──────────────────────────────────────────────────────────────────────────────
# Таймаут для повного перебору (секунд); None = без обмеження
TIMEOUT_BY_N = {8: None, 9: None, 10: 30, 11: 20, 12: 15}

# Максимальна кількість ітерацій перевірки таймауту
CHECK_EVERY = 20_000


# ──────────────────────────────────────────────────────────────────────────────
def run_centralized_bf(objects, triples, timeout_s):
    """
    Повний перебір з можливим таймаутом.
    Повертає dict з результатами + метаданими повноти.
    """
    n_perm = math.factorial(len(objects))
    t0 = time.perf_counter()

    best_sum = float("inf")
    best_sum_rank = None
    best_max = float("inf")
    best_max_rank = None
    n_eq_sum = 0
    n_eq_max = 0
    n_checked = 0

    for perm in permutations(objects):
        s, m, _ = evaluate_ranking(perm, triples)
        n_checked += 1
        if s < best_sum:
            best_sum = s
            best_sum_rank = list(perm)
            n_eq_sum = 1
        elif s == best_sum:
            n_eq_sum += 1
        if m < best_max:
            best_max = m
            best_max_rank = list(perm)
            n_eq_max = 1
        elif m == best_max:
            n_eq_max += 1

        if timeout_s and n_checked % CHECK_EVERY == 0:
            if time.perf_counter() - t0 > timeout_s:
                break

    t_elapsed = round(time.perf_counter() - t0, 4)
    is_complete = n_checked >= n_perm

    if is_complete:
        t_est = t_elapsed
    else:
        t_est = round(t_elapsed * n_perm / n_checked, 1)

    return {
        "n_perm": n_perm,
        "n_checked": n_checked,
        "bf_complete": is_complete,
        "t_cen": t_elapsed,
        "t_cen_est": t_est,
        "best_sum": best_sum if is_complete else None,
        "best_max": best_max if is_complete else None,
        "n_eq_sum": n_eq_sum if is_complete else None,
        "n_eq_max": n_eq_max if is_complete else None,
        "best_sum_rank": best_sum_rank,
        "best_max_rank": best_max_rank,
    }


def run_distributed_bf(objects, triples):
    """
    Розподілений перебір через ThreadPoolExecutor (4 воркери).
    Запускається лише для n=8,9 де повний перебір практичний.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    n = len(objects)
    t0 = time.perf_counter()

    def branch(first_idx):
        rest = [o for i, o in enumerate(objects) if i != first_idx]
        fixed = objects[first_idx]
        b_sum = float("inf")
        b_max = float("inf")
        for perm in permutations(rest):
            ranking = (fixed,) + perm
            s, m, _ = evaluate_ranking(ranking, triples)
            if s < b_sum:
                b_sum = s
            if m < b_max:
                b_max = m
        return b_sum, b_max

    best_sum = float("inf")
    best_max = float("inf")
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(branch, i) for i in range(n)]
        for fut in as_completed(futures):
            b_sum, b_max = fut.result()
            if b_sum < best_sum:
                best_sum = b_sum
            if b_max < best_max:
                best_max = b_max

    return round(time.perf_counter() - t0, 4)


# ──────────────────────────────────────────────────────────────────────────────
# Параметри GA для різних n
def ga_params(n_obj):
    if n_obj <= 9:
        return dict(pop_size=50, n_gen=40)
    if n_obj <= 11:
        return dict(pop_size=40, n_gen=35)
    return dict(pop_size=30, n_gen=30)


def dis_ga_params(n_obj):
    if n_obj <= 9:
        return dict(n_islands=4, pop_per_island=13, n_gen=40, n_epochs=5)
    if n_obj <= 11:
        return dict(n_islands=4, pop_per_island=10, n_gen=35, n_epochs=5)
    return dict(n_islands=4, pop_per_island=8, n_gen=30, n_epochs=5)


# ──────────────────────────────────────────────────────────────────────────────
def bench_small():
    """n=8..12, exp=10/20/30/50"""

    # Завантажити існуючі BF дані для n=8,9 (вже обчислені раніше)
    existing_bf = {}
    bf_path = ROOT / "sam2_bench_fast.json"
    if bf_path.exists():
        for row in json.loads(bf_path.read_text(encoding="utf-8")):
            existing_bf[(row["n_obj"], row["n_exp"])] = row

    configs = [(n, e) for n in [8, 9, 10, 11, 12] for e in [10, 20, 30, 50]]
    results = []

    # Оцінки часу для n=11,12 на основі scaling n!/9! * t_9
    # t_9_base[n_exp] з існуючих даних
    t9_base = {
        10: 16.73, 20: 33.89, 30: 55.41, 50: 86.62
    }

    for n_obj, n_exp in configs:
        seed = n_obj * 100 + n_exp
        objects, triples = generate_random_problem(n_obj, n_exp, seed=seed)
        timeout = TIMEOUT_BY_N[n_obj]

        print(f"\n{'='*50}")
        print(f"n_obj={n_obj}, n_exp={n_exp}, seed={seed}")

        # ── Brute-force ──────────────────────────────────────────────────────
        if n_obj in (8, 9) and (n_obj, n_exp) in existing_bf:
            # Беремо вже обчислені BF результати
            ex = existing_bf[(n_obj, n_exp)]
            bf = {
                "n_perm": ex["n_perm"],
                "n_checked": ex["n_perm"],
                "bf_complete": True,
                "t_cen": ex["t_cen"],
                "t_cen_est": ex["t_cen"],
                "best_sum": ex["best_sum"],
                "best_max": ex["best_max"],
                "n_eq_sum": ex["n_eq_sum"],
                "n_eq_max": ex["n_eq_max"],
                "best_sum_rank": ex["best_sum_rank"],
                "best_max_rank": None,
            }
            t_dis = ex["t_dis"]
            print(f"  BF: loaded from cache (complete), t_cen={bf['t_cen']}s, t_dis={t_dis}s")
        elif n_obj <= 10:
            print(f"  BF centralized (timeout={timeout}s)...")
            bf = run_centralized_bf(objects, triples, timeout)
            print(f"  BF: checked={bf['n_checked']}/{bf['n_perm']}, complete={bf['bf_complete']}, t={bf['t_cen']}s, est={bf['t_cen_est']}s")

            t_dis = None
            if n_obj <= 9:
                print(f"  BF distributed...")
                t_dis = run_distributed_bf(objects, triples)
                print(f"  BF distributed: t_dis={t_dis}s")
        else:
            # n=11,12: BF нереальний → оцінка масштабуванням n!/9! * t_9
            scale = math.factorial(n_obj) / math.factorial(9)
            t_est_base = t9_base.get(n_exp, t9_base[50])
            t_cen_est = round(t_est_base * scale, 0)
            bf = {
                "n_perm": math.factorial(n_obj),
                "n_checked": 0,
                "bf_complete": False,
                "t_cen": None,
                "t_cen_est": t_cen_est,
                "best_sum": None,
                "best_max": None,
                "n_eq_sum": None,
                "n_eq_max": None,
                "best_sum_rank": None,
                "best_max_rank": None,
            }
            t_dis = None
            t_dis_est = round(t_cen_est, 0)
            print(f"  BF: infeasible, estimated t_cen={t_cen_est}s")

        # ── GA централізований ───────────────────────────────────────────────
        print(f"  GA centralized...")
        p = ga_params(n_obj)
        ga_cen = genetic_algorithm(objects, triples, seed=seed, **p)
        print(f"  GA cen: cost={ga_cen['best_cost']}, t={ga_cen['elapsed']}s")

        # ── GA розподілений ──────────────────────────────────────────────────
        print(f"  GA distributed...")
        dp = dis_ga_params(n_obj)
        ga_dis = distributed_genetic_algorithm(objects, triples, seed=seed, **dp)
        print(f"  GA dis: cost={ga_dis['best_cost']}, t={ga_dis['elapsed']}s")

        row = {
            "n_obj": n_obj,
            "n_exp": n_exp,
            "seed": seed,
            # BF
            "n_perm": bf["n_perm"],
            "bf_complete": bf["bf_complete"],
            "t_cen": bf["t_cen"],
            "t_cen_est": bf["t_cen_est"],
            "t_dis": t_dis,
            "best_sum": bf["best_sum"],
            "best_max": bf["best_max"],
            "n_eq_sum": bf["n_eq_sum"],
            "n_eq_max": bf["n_eq_max"],
            "best_sum_rank": bf["best_sum_rank"],
            # GA
            "ga_cen_cost": ga_cen["best_cost"],
            "ga_cen_time": ga_cen["elapsed"],
            "ga_cen_rank": ga_cen["best_ranking"],
            "ga_cen_history": ga_cen["history"],
            "ga_dis_cost": ga_dis["best_cost"],
            "ga_dis_time": ga_dis["elapsed"],
            "ga_dis_rank": ga_dis["best_ranking"],
            "ga_dis_history": ga_dis["history"],
        }
        results.append(row)

    out = ROOT / "sam2_bench_full.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ sam2_bench_full.json written ({len(results)} rows)")
    return results


def bench_large():
    """n=100/200/500, exp=10/20/30 — тільки GA"""
    configs = [
        (100, 10), (100, 20), (100, 30),
        (200, 10), (200, 20), (200, 30),
        (500, 10), (500, 20), (500, 30),
    ]
    results = []

    for n_obj, n_exp in configs:
        seed = n_obj * 100 + n_exp
        objects, triples = generate_random_problem(n_obj, n_exp, seed=seed)

        print(f"\n{'='*50}")
        print(f"LARGE n_obj={n_obj}, n_exp={n_exp}")

        # Адаптивні параметри GA
        if n_obj <= 100:
            pop, gens, eps = 30, 60, 6
        elif n_obj <= 200:
            pop, gens, eps = 24, 50, 5
        else:
            pop, gens, eps = 18, 40, 4

        print(f"  GA centralized (pop={pop}, gen={gens})...")
        ga_cen = genetic_algorithm(
            objects, triples, pop_size=pop, n_gen=gens, seed=seed, time_limit=15.0
        )
        print(f"  cen: cost={ga_cen['best_cost']}, t={ga_cen['elapsed']}s")

        print(f"  GA distributed (n_islands=4, pop={pop//4 or 5}, gen={gens}, eps={eps})...")
        ga_dis = distributed_genetic_algorithm(
            objects, triples,
            n_islands=4, pop_per_island=max(pop // 4, 5),
            n_gen=gens, n_epochs=eps,
            seed=seed, time_limit=15.0
        )
        print(f"  dis: cost={ga_dis['best_cost']}, t={ga_dis['elapsed']}s")

        results.append({
            "n_obj": n_obj,
            "n_exp": n_exp,
            "seed": seed,
            "ga_cen_cost": ga_cen["best_cost"],
            "ga_cen_time": ga_cen["elapsed"],
            "ga_cen_history": ga_cen["history"],
            "ga_dis_cost": ga_dis["best_cost"],
            "ga_dis_time": ga_dis["elapsed"],
            "ga_dis_history": ga_dis["history"],
        })

    out = ROOT / "sam2_large.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ sam2_large.json written ({len(results)} rows)")
    return results


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("=== Sam2 benchmark: generating data ===\n")
    t_start = time.perf_counter()

    bench_small()
    bench_large()

    total = round(time.perf_counter() - t_start, 1)
    print(f"\n=== Done! Total time: {total}s ===")
