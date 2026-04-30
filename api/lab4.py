# -*- coding: utf-8 -*-
"""
Лабораторна робота №4 — розподілені обчислення компромісних ранжувань
та визначення індексів задоволеності експертів.

Реалізовано:
  * розподілений прямий перебір з декомпозицією за першим об'єктом;
  * послідовний (централізований) перебір — для бенчмарка часу;
  * обчислення відстані Кука з компенсацією за видалені евристиками
    об'єкти за правилом п.9 завдання: d^j = d^l + (n-3);
  * індекс задоволеності експерта s^j = (1 - d^j/((n-3)·3))·100%;
  * генерація випадкових експертних трійок для n>>12;
  * генетичний алгоритм (PMX-кросовер, swap-мутація, турнір);
  * розподілений (острівний) генетичний алгоритм з міграцією.

Вся «розподіленість» на Vercel реалізована через ThreadPoolExecutor —
serverless-середовище не дозволяє multiprocessing/MPI. Декомпозиція задачі
коректна; реальний speedup визначається GIL та інфраструктурою. Для
ілюстрації окремо виводимо «ідеальний» час T_ideal = T_центр / W.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import permutations
from typing import Dict, List, Sequence, Tuple

from .algorithms import evaluate_ranking


# ===========================================================================
# 1. Розподілений прямий перебір з декомпозицією по першому елементу
# ===========================================================================
def _enum_branch(objects: Sequence[str],
                 triples: Sequence[Sequence[str]],
                 first_idx: int) -> Dict:
    """
    Гілка декомпозиції: фіксуємо objects[first_idx] на 1-й позиції та
    перебираємо (n-1)! перестановок решти. Повертає локальні Σ- та max-медіани.
    """
    rest = [o for i, o in enumerate(objects) if i != first_idx]
    fixed = objects[first_idx]
    best_sum = float("inf")
    best_max = float("inf")
    all_best_sum: List[List[str]] = []
    all_best_max: List[List[str]] = []
    count = 0
    for perm in permutations(rest):
        ranking = [fixed, *perm]
        s, m, _ = evaluate_ranking(ranking, triples)
        count += 1
        if s < best_sum:
            best_sum = s
            all_best_sum = [ranking]
        elif s == best_sum:
            all_best_sum.append(ranking)
        if m < best_max:
            best_max = m
            all_best_max = [ranking]
        elif m == best_max:
            all_best_max.append(ranking)
    return {
        "first": fixed,
        "count": count,
        "best_sum": best_sum,
        "best_max": best_max,
        "all_best_sum": all_best_sum,
        "all_best_max": all_best_max,
    }


def distributed_enumerate(objects: Sequence[str],
                          triples: Sequence[Sequence[str]],
                          n_workers: int = 4) -> Dict:
    """
    Декомпозиція: n гілок (по фіксованому 1-му об'єкту) розподіляються між
    n_workers потоками. Кожна гілка обробляє (n-1)! перестановок.
    Σ розмірів гілок = n · (n-1)! = n!  → доводимо повне покриття.
    """
    n = len(objects)
    started = time.time()
    branches: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max(1, n_workers)) as ex:
        futures = [ex.submit(_enum_branch, objects, triples, i)
                   for i in range(n)]
        for f in futures:
            branches.append(f.result())
    elapsed = round(time.time() - started, 4)

    best_sum = min(b["best_sum"] for b in branches)
    best_max_v = min(b["best_max"] for b in branches)
    all_best_sum: List[List[str]] = []
    all_best_max: List[List[str]] = []
    for b in branches:
        if b["best_sum"] == best_sum:
            all_best_sum.extend(b["all_best_sum"])
        if b["best_max"] == best_max_v:
            all_best_max.extend(b["all_best_max"])

    return {
        "n_workers": n_workers,
        "branches": branches,
        "n_perm_total": sum(b["count"] for b in branches),
        "n_factorial_expected": _factorial(n),
        "best_sum_value": best_sum,
        "best_sum_rank": all_best_sum[0] if all_best_sum else [],
        "best_max_value": best_max_v,
        "best_max_rank": all_best_max[0] if all_best_max else [],
        "all_best_sum": all_best_sum,
        "all_best_max": all_best_max,
        "elapsed": elapsed,
    }


def centralized_enumerate(objects: Sequence[str],
                          triples: Sequence[Sequence[str]]) -> Dict:
    """Послідовний перебір — еталон та бенчмарк часу."""
    started = time.time()
    best_sum = float("inf")
    best_max = float("inf")
    best_sum_rank: List[str] = []
    best_max_rank: List[str] = []
    n_perm = 0
    for perm in permutations(objects):
        ranking = list(perm)
        s, m, _ = evaluate_ranking(ranking, triples)
        n_perm += 1
        if s < best_sum:
            best_sum = s
            best_sum_rank = ranking
        if m < best_max:
            best_max = m
            best_max_rank = ranking
    return {
        "n_perm": n_perm,
        "best_sum_value": best_sum,
        "best_sum_rank": best_sum_rank,
        "best_max_value": best_max,
        "best_max_rank": best_max_rank,
        "elapsed": round(time.time() - started, 4),
    }


def _factorial(n: int) -> int:
    f = 1
    for i in range(2, n + 1):
        f *= i
    return f


# ===========================================================================
# 2. Індекси задоволеності експертів (п.7-11 завдання)
# ===========================================================================
def expert_distance_lab4(triple_lab1: Sequence[str],
                         ranking_compromise: Sequence[str]) -> Tuple[int, int, List[str]]:
    """
    Відстань Кука від оригінальної (Лаб.1) трійки експерта до компромісного
    ранжування з n об'єктів.

    Повертає (d_total, d_partial, removed_objects).
      d_partial — сума |k - pos(obj)| по об'єктах, які залишилися
                  у компромісному ранжуванні;
      removed   — список об'єктів, видалених евристиками Лаб.2 (їх немає
                  в ranking_compromise);
      d_total   — d_partial + (n-3) за кожен видалений об'єкт (п.9 завдання).
    """
    n = len(ranking_compromise)
    pos = {obj: i + 1 for i, obj in enumerate(ranking_compromise)}
    d_partial = 0
    removed: List[str] = []
    for k, obj in enumerate(triple_lab1):
        if obj in pos:
            d_partial += abs(pos[obj] - (k + 1))
        else:
            removed.append(obj)
    d_total = d_partial + (n - 3) * len(removed)
    return d_total, d_partial, removed


def satisfaction_index(d_value: int, n: int) -> float:
    """s^j = (1 - d^j / ((n-3)·3))·100 %."""
    max_d = 3 * (n - 3)
    if max_d <= 0:
        return 100.0
    s = (1.0 - d_value / max_d) * 100.0
    return max(0.0, min(100.0, s))


def compute_satisfactions(experts: Sequence[str],
                          triples_lab1: Sequence[Sequence[str]],
                          ranking_compromise: Sequence[str]) -> List[Dict]:
    """Повертає по одному рядку на експерта з усіма показниками."""
    n = len(ranking_compromise)
    rows: List[Dict] = []
    for expert, triple in zip(experts, triples_lab1):
        d, d_partial, removed = expert_distance_lab4(triple, ranking_compromise)
        s = satisfaction_index(d, n)
        rows.append({
            "expert": expert,
            "triple": list(triple),
            "removed": removed,
            "d_partial": d_partial,
            "d": d,
            "s": round(s, 2),
        })
    return rows


# ===========================================================================
# 3. Ситуація Б: випадкові ранжування для n>>12
# ===========================================================================
def generate_random_problem(n_alt: int, n_exp: int, seed: int = 42):
    """Генерує n_alt об'єктів (o001…) та n_exp випадкових трійок-ранжувань."""
    rng = random.Random(seed)
    objects = [f"o{i + 1:03d}" for i in range(n_alt)]
    triples = [tuple(rng.sample(objects, 3)) for _ in range(n_exp)]
    return objects, triples


# ===========================================================================
# 4. Генетичний алгоритм (еволюційний — п.13-15 завдання)
# ===========================================================================
def _ga_pmx(p1: List[str], p2: List[str], rng: random.Random) -> List[str]:
    """Partially Mapped Crossover для перестановок."""
    n = len(p1)
    a, b = sorted(rng.sample(range(n), 2))
    child: List = [None] * n
    child[a:b + 1] = p1[a:b + 1]
    used = set(child[a:b + 1])
    for i in list(range(0, a)) + list(range(b + 1, n)):
        x = p2[i]
        guard = 0
        while x in used and guard < n:
            j = p1.index(x)
            x = p2[j]
            guard += 1
        if x not in used:
            child[i] = x
            used.add(x)
    leftovers = [o for o in p2 if o not in used]
    li = 0
    for i in range(n):
        if child[i] is None:
            child[i] = leftovers[li]
            li += 1
    return child


def _ga_swap_mutation(perm: List[str], rng: random.Random,
                      p_mut: float = 0.2) -> List[str]:
    if rng.random() < p_mut:
        i, j = rng.sample(range(len(perm)), 2)
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def _ga_tournament(pop: List[List[str]], fitness: List[int],
                   rng: random.Random, k: int = 3) -> List[str]:
    candidates = rng.sample(range(len(pop)), k)
    winner = min(candidates, key=lambda i: fitness[i])
    return pop[winner]


def genetic_algorithm(objects: Sequence[str],
                      triples: Sequence[Sequence[str]],
                      pop_size: int = 50,
                      n_gen: int = 30,
                      p_mut: float = 0.2,
                      tournament_k: int = 3,
                      seed: int = 2026,
                      time_limit: float | None = None) -> Dict:
    """Класичний централізований ГА — пошук медіани Кемені."""
    rng = random.Random(seed)
    started = time.time()
    n = len(objects)

    population = [rng.sample(objects, n) for _ in range(pop_size)]
    fitness = [evaluate_ranking(p, triples)[0] for p in population]
    best_idx = min(range(pop_size), key=lambda i: fitness[i])
    best = list(population[best_idx])
    best_cost = fitness[best_idx]
    history = [best_cost]

    for _ in range(n_gen):
        if time_limit and (time.time() - started) > time_limit:
            break
        new_pop: List[List[str]] = [list(best)]  # елітизм
        while len(new_pop) < pop_size:
            p1 = _ga_tournament(population, fitness, rng, tournament_k)
            p2 = _ga_tournament(population, fitness, rng, tournament_k)
            child = _ga_pmx(p1, p2, rng)
            child = _ga_swap_mutation(child, rng, p_mut)
            new_pop.append(child)
        population = new_pop
        fitness = [evaluate_ranking(p, triples)[0] for p in population]
        idx = min(range(pop_size), key=lambda i: fitness[i])
        if fitness[idx] < best_cost:
            best_cost = fitness[idx]
            best = list(population[idx])
        history.append(best_cost)

    return {
        "best_ranking": best,
        "best_cost": best_cost,
        "history": history,
        "elapsed": round(time.time() - started, 4),
        "params": {"pop_size": pop_size, "n_gen": n_gen,
                   "p_mut": p_mut, "tournament_k": tournament_k},
    }


def _island_step(objects: Sequence[str],
                 triples: Sequence[Sequence[str]],
                 population: List[List[str]],
                 fitness: List[int],
                 n_gen_per_epoch: int,
                 seed: int) -> Tuple[List[List[str]], List[int], List[str], int]:
    """Один епохальний прогін ГА на острові."""
    rng = random.Random(seed)
    pop_size = len(population)
    best_idx = min(range(pop_size), key=lambda i: fitness[i])
    best = list(population[best_idx])
    best_cost = fitness[best_idx]

    for _ in range(n_gen_per_epoch):
        new_pop: List[List[str]] = [list(best)]
        while len(new_pop) < pop_size:
            p1 = _ga_tournament(population, fitness, rng)
            p2 = _ga_tournament(population, fitness, rng)
            child = _ga_pmx(p1, p2, rng)
            child = _ga_swap_mutation(child, rng)
            new_pop.append(child)
        population = new_pop
        fitness = [evaluate_ranking(p, triples)[0] for p in population]
        idx = min(range(pop_size), key=lambda i: fitness[i])
        if fitness[idx] < best_cost:
            best_cost = fitness[idx]
            best = list(population[idx])
    return population, fitness, best, best_cost


def distributed_genetic_algorithm(objects: Sequence[str],
                                  triples: Sequence[Sequence[str]],
                                  n_islands: int = 4,
                                  pop_per_island: int = 13,
                                  n_gen: int = 30,
                                  n_epochs: int = 5,
                                  seed: int = 2026,
                                  time_limit: float | None = None) -> Dict:
    """
    Острівна модель ГА: n_islands популяцій еволюціонують паралельно
    n_epochs епох, між якими відбувається міграція по кільцю
    (найкращий індивід острова заміщає найгіршого на наступному острові).
    """
    started = time.time()
    n_gen_per_epoch = max(1, n_gen // n_epochs)
    rng = random.Random(seed)
    n = len(objects)

    islands = []  # [(population, fitness)]
    for k in range(n_islands):
        pop = [rng.sample(objects, n) for _ in range(pop_per_island)]
        fit = [evaluate_ranking(p, triples)[0] for p in pop]
        islands.append([pop, fit])

    bi = min(range(n_islands * pop_per_island),
             key=lambda i: islands[i // pop_per_island][1][i % pop_per_island])
    best = list(islands[bi // pop_per_island][0][bi % pop_per_island])
    best_cost = islands[bi // pop_per_island][1][bi % pop_per_island]
    history = [best_cost]

    for epoch in range(n_epochs):
        if time_limit and (time.time() - started) > time_limit:
            break
        with ThreadPoolExecutor(max_workers=n_islands) as ex:
            futures = [
                ex.submit(_island_step, objects, triples,
                          islands[k][0], islands[k][1],
                          n_gen_per_epoch,
                          seed + epoch * 100 + k)
                for k in range(n_islands)
            ]
            for k, f in enumerate(futures):
                pop, fit, b_local, c_local = f.result()
                islands[k] = [pop, fit]
                if c_local < best_cost:
                    best_cost = c_local
                    best = list(b_local)
        history.append(best_cost)
        # Міграція по кільцю
        if epoch < n_epochs - 1:
            for k in range(n_islands):
                src = k
                dst = (k + 1) % n_islands
                src_best = min(range(pop_per_island),
                               key=lambda i: islands[src][1][i])
                dst_worst = max(range(pop_per_island),
                                key=lambda i: islands[dst][1][i])
                islands[dst][0][dst_worst] = list(islands[src][0][src_best])
                islands[dst][1][dst_worst] = islands[src][1][src_best]

    return {
        "best_ranking": best,
        "best_cost": best_cost,
        "history": history,
        "elapsed": round(time.time() - started, 4),
        "params": {"n_islands": n_islands, "pop_per_island": pop_per_island,
                   "n_gen": n_gen, "n_epochs": n_epochs,
                   "total_pop": n_islands * pop_per_island},
    }


# ===========================================================================
# 5. Порівняльний пакет: централізований vs розподілений ГА для n>>12
# ===========================================================================
def ga_comparison_suite(seed: int = 17) -> List[Dict]:
    """
    Прогін ГА на синтетичних даних n>>12.
    Сітка: n_alt ∈ {20, 50, 100} × n_exp ∈ {10, 20, 30}.

    Семантика порівняння — «розподілені vs централізовані ОБЧИСЛЕННЯ»
    (як трактує п.15 завдання): кожен з K = 4 розподілених вузлів має
    повноцінну популяцію тієї ж розмірності, що й централізований процес.
    На реальній розподіленій системі (4 окремі машини / процеси) розподілений
    варіант витрачає той самий wall-clock, що і централізований, але виконує
    K-кратний об'єм обчислень — це і є джерело покращення якості розв'язку.
    На serverless-Python (GIL) wall-clock розподіленого зростає, але
    покращення якості зберігається.
    """
    sizes = (20, 50, 100)
    expert_counts = (10, 20, 30)
    rows: List[Dict] = []

    for n_alt in sizes:
        if n_alt <= 20:
            pop, n_gen = 24, 20
        elif n_alt <= 50:
            pop, n_gen = 18, 15
        else:
            pop, n_gen = 12, 12
        n_islands = 4

        for n_exp in expert_counts:
            objects, triples = generate_random_problem(
                n_alt, n_exp, seed=seed + n_alt + n_exp)

            cen = genetic_algorithm(
                objects, triples,
                pop_size=pop, n_gen=n_gen,
                seed=seed, time_limit=2.5)
            dis = distributed_genetic_algorithm(
                objects, triples,
                n_islands=n_islands,
                pop_per_island=pop,  # повна популяція на кожен вузол
                n_gen=n_gen, n_epochs=4,
                seed=seed, time_limit=2.5)

            improvement = cen["best_cost"] - dis["best_cost"]
            rel = (100.0 * improvement / cen["best_cost"]
                   if cen["best_cost"] else 0.0)
            rows.append({
                "n_alt": n_alt,
                "n_exp": n_exp,
                "pop_total": pop,
                "n_gen": n_gen,
                "n_islands": n_islands,
                "centralized_cost": cen["best_cost"],
                "centralized_time": cen["elapsed"],
                "distributed_cost": dis["best_cost"],
                "distributed_time": dis["elapsed"],
                "improvement": improvement,
                "improvement_pct": round(rel, 2),
            })

    return rows


def single_ga_demo(n_alt: int = 50, n_exp: int = 20, seed: int = 7) -> Dict:
    """
    Деталізований прогін на одній задачі: повна історія обох алгоритмів
    та згенеровані експертні трійки — для виведення на екран.
    Розподілений ГА має повну популяцію на кожному з 4 «вузлів».
    """
    objects, triples = generate_random_problem(n_alt, n_exp, seed=seed)
    pop = 24
    n_gen = 25
    cen = genetic_algorithm(objects, triples, pop_size=pop, n_gen=n_gen,
                            seed=seed, time_limit=2.5)
    dis = distributed_genetic_algorithm(
        objects, triples,
        n_islands=4, pop_per_island=pop, n_gen=n_gen, n_epochs=5,
        seed=seed, time_limit=2.5)
    return {
        "n_alt": n_alt,
        "n_exp": n_exp,
        "pop_size": pop,
        "n_gen": n_gen,
        "objects_preview": objects[:10],
        "triples_preview": [list(t) for t in triples[:8]],
        "centralized": cen,
        "distributed": dis,
    }
