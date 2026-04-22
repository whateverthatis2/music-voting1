# -*- coding: utf-8 -*-
"""
Мурашиний алгоритм (Ant Colony Optimization) для пошуку колективного
ранжування — медіани Кемені — Снела на основі експертних трійок.

Реалізація — позиційний ACO (ASrank-варіант):
  * феромонна матриця tau[k][j] — «бажаність» поставити об'єкт j на k-ту позицію;
  * евристична інформація eta[j] — Борда-вага об'єкта (3 / 2 / 1);
  * правило вибору об'єкта мурашкою:
        P(j | поточна позиція k) ∝ tau[k][j]^α · eta[j]^β;
  * випаровування ρ та поповнення феромону пропорційно якості розв'язку
        Δτ = Q / (1 + cost(solution)).

Параметри підібрано так, щоб алгоритм гарантовано вкладався у timeout
безсерверної функції Vercel (10 секунд для безкоштовного плану).
"""

from __future__ import annotations

import random
import time
from typing import Dict, List, Sequence, Tuple

from .algorithms import evaluate_ranking


# ---------------------------------------------------------------------------
# Підготовка евристичної інформації
# ---------------------------------------------------------------------------
def _heuristic_weights(
    objects: Sequence[str],
    expert_triples: Sequence[Sequence[str]],
) -> List[float]:
    """
    Вектор евристичної інформації eta[j] на основі рейтингу Борда:
      +3 за 1-ше місце, +2 за 2-ге, +1 за 3-тє.
    Зміщення +1 запобігає нульовим імовірностям.
    """
    idx = {obj: j for j, obj in enumerate(objects)}
    eta = [1.0] * len(objects)
    for triple in expert_triples:
        for pos, obj in enumerate(triple):
            j = idx.get(obj)
            if j is not None:
                eta[j] += (3 - pos)
    return eta


# ---------------------------------------------------------------------------
# Один прогін мурашиного алгоритму
# ---------------------------------------------------------------------------
def ant_colony(
    objects: Sequence[str],
    expert_triples: Sequence[Sequence[str]],
    n_ants: int = 30,
    n_iter: int = 60,
    alpha: float = 1.0,
    beta: float = 2.0,
    rho: float = 0.15,
    q: float = 100.0,
    seed: int | None = None,
    time_limit: float | None = None,
) -> Dict:
    """
    Запуск ACO. Повертає словник:
        best_ranking   — найкраще знайдене ранжування,
        best_cost      — мінімум суми відстаней Кука по експертах,
        best_max       — максимум відстані по експертах для best_ranking,
        history        — історія best_cost по ітераціях (для побудови графіка),
        params         — фактичні параметри прогону,
        elapsed        — час, секунди.
    """
    if seed is not None:
        random.seed(seed)
    started = time.time()

    n = len(objects)
    if n == 0:
        return {"best_ranking": [], "best_cost": 0, "best_max": 0,
                "history": [], "params": {}, "elapsed": 0.0}

    eta = _heuristic_weights(objects, expert_triples)
    tau = [[1.0] * n for _ in range(n)]

    best_ranking: List[str] = []
    best_cost = float("inf")
    best_max = 0
    history: List[float] = []

    for it in range(n_iter):
        if time_limit and (time.time() - started) > time_limit:
            break

        iteration_solutions: List[Tuple[List[str], float]] = []

        for _ in range(n_ants):
            visited = [False] * n
            ranking_idx: List[int] = []

            for k in range(n):
                # ймовірності розміщення об'єктів на k-тій позиції
                weights = []
                for j in range(n):
                    if visited[j]:
                        weights.append(0.0)
                        continue
                    w = (tau[k][j] ** alpha) * (eta[j] ** beta)
                    weights.append(w)

                total = sum(weights)
                if total <= 0.0:
                    chosen = next(j for j in range(n) if not visited[j])
                else:
                    r = random.random() * total
                    cum = 0.0
                    chosen = -1
                    for j, w in enumerate(weights):
                        cum += w
                        if cum >= r:
                            chosen = j
                            break
                    if chosen == -1:
                        chosen = next(j for j in range(n) if not visited[j])

                ranking_idx.append(chosen)
                visited[chosen] = True

            ranking = [objects[j] for j in ranking_idx]
            cost, mx, _ = evaluate_ranking(ranking, expert_triples)
            iteration_solutions.append((ranking, cost))
            if cost < best_cost:
                best_cost, best_max, best_ranking = cost, mx, ranking

        # випаровування
        for k in range(n):
            for j in range(n):
                tau[k][j] *= (1.0 - rho)

        # відкладання феромону
        for ranking, cost in iteration_solutions:
            deposit = q / (1.0 + cost)
            for k, obj in enumerate(ranking):
                j = objects.index(obj)
                tau[k][j] += deposit

        # елітарне підкріплення найкращого розв'язку
        elite_deposit = 2.0 * q / (1.0 + best_cost)
        for k, obj in enumerate(best_ranking):
            j = objects.index(obj)
            tau[k][j] += elite_deposit

        history.append(best_cost)

    return {
        "best_ranking": best_ranking,
        "best_cost": int(best_cost) if best_cost != float("inf") else None,
        "best_max": int(best_max),
        "history": history,
        "params": {"n_ants": n_ants, "n_iter": n_iter,
                   "alpha": alpha, "beta": beta, "rho": rho, "q": q},
        "elapsed": round(time.time() - started, 3),
    }


# ---------------------------------------------------------------------------
# Масштабне дослідження ACO (п.17 завдання)
#   20/50/100 альтернатив × 10/20/30 експертів
# ---------------------------------------------------------------------------
def scaling_test(
    sizes: Sequence[int] = (20, 50, 100),
    expert_counts: Sequence[int] = (10, 20, 30),
    seed: int = 17,
    time_budget_per_run: float = 1.5,
) -> List[Dict]:
    """
    Прогін ACO на синтетичних даних. Параметри ACO зменшуються зі
    зростанням n, щоб усі прогони сумарно вкладалися в Vercel timeout.
    """
    rng = random.Random(seed)
    results: List[Dict] = []

    for n_alt in sizes:
        for n_exp in expert_counts:
            objects = [f"A{i + 1:03d}" for i in range(n_alt)]
            triples = []
            for _ in range(n_exp):
                triples.append(tuple(rng.sample(objects, 3)))

            # адаптивні параметри
            if n_alt <= 20:
                ants, iters = 25, 40
            elif n_alt <= 50:
                ants, iters = 20, 25
            else:
                ants, iters = 15, 18

            res = ant_colony(
                objects, triples,
                n_ants=ants, n_iter=iters,
                seed=seed + n_alt + n_exp,
                time_limit=time_budget_per_run,
            )
            results.append({
                "n_alt": n_alt,
                "n_exp": n_exp,
                "n_ants": ants,
                "n_iter": iters,
                "best_cost": res["best_cost"],
                "best_max": res["best_max"],
                "elapsed": res["elapsed"],
                "iterations_done": len(res["history"]),
            })

    return results
