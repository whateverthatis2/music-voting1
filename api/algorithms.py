# -*- coding: utf-8 -*-
"""
Алгоритми лабораторної роботи №3.

Реалізовано:
  * метрика Кука (відстань між ранжуваннями за модулем різниці позицій);
  * відстань від кандидатного ранжування до експертної трійки (евристика E1);
  * матриця статистики переваг (п.1.2 завдання);
  * розгорнута матриця рангів (п.1.3 завдання);
  * прямий перебір n! перестановок з обчисленням
        sum-критерію та max-критерію (медіани Кемені — Снела);
  * відновлення ранжувань з векторів рангів.
"""

from __future__ import annotations

from itertools import permutations
from typing import Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Метрика Кука та евристика E1 (поміркованої взаємності)
# ---------------------------------------------------------------------------
def cook_distance(rank_a: Sequence[int], rank_b: Sequence[int]) -> int:
    """
    Класична метрика Кука неспівпадання рангів:

        d(R^j, R^l) = Σ |r^j_i - r^l_i|.

    Вектори rank_a, rank_b мають однакову довжину — позиція i у векторі
    зберігає ранг і-го об'єкта.
    """
    return sum(abs(int(a) - int(b)) for a, b in zip(rank_a, rank_b))


def distance_to_triple(ranking: Sequence[str], triple: Sequence[str]) -> int:
    """
    Евристика E1 (поміркованої взаємності) — відстань Кука від кандидатного
    ранжування до експертної трійки:

        d^l_v = |1 - r(i1)| + |2 - r(i2)| + |3 - r(i3)|,

    де r(x) — позиція об'єкта x у кандидатному ранжуванні `ranking` (1..n).
    Якщо об'єкт відсутній у ranking, штрафуємо величиною n
    (формально неможливо, бо ranking — перестановка тих самих об'єктів).
    """
    n = len(ranking)
    pos = {obj: i + 1 for i, obj in enumerate(ranking)}
    return sum(abs((k + 1) - pos.get(obj, n + 1)) for k, obj in enumerate(triple))


# ---------------------------------------------------------------------------
# Агрегація відстаней по всіх експертах
# ---------------------------------------------------------------------------
def evaluate_ranking(
    ranking: Sequence[str],
    expert_triples: Sequence[Sequence[str]],
) -> Tuple[int, int, List[int]]:
    """
    Повертає (sum_distance, max_distance, per_expert_distances).
    Sum-критерій — медіана Кемені; max-критерій — мінімаксна медіана.
    """
    distances = [distance_to_triple(ranking, t) for t in expert_triples]
    return sum(distances), max(distances), distances


# ---------------------------------------------------------------------------
# Матриці п.1.2 та п.1.3 завдання
# ---------------------------------------------------------------------------
def preference_matrix(
    objects: Sequence[str],
    expert_triples: Sequence[Sequence[str]],
) -> List[List[int]]:
    """
    Матриця статистики переваг (п.1.2):
        рядки 1..3 — кількість експертів, що поставили об'єкт на 1/2/3 місце;
        рядок 4   — сумарна кількість згадувань (рейтинг Борда без ваг).

    Розмір: 4 × len(objects).
    """
    n = len(objects)
    idx = {obj: j for j, obj in enumerate(objects)}
    matrix = [[0] * n for _ in range(4)]
    for triple in expert_triples:
        for rank, obj in enumerate(triple):
            j = idx.get(obj)
            if j is None:
                continue
            matrix[rank][j] += 1
            matrix[3][j] += 1
    return matrix


def expanded_rank_matrix(
    objects: Sequence[str],
    expert_triples: Sequence[Sequence[str]],
) -> List[List[int]]:
    """
    Розгорнута матриця рангів (п.1.3): n_objects × n_experts.
    matrix[i][j] = ранг об'єкта i у трійці експерта j (1, 2, 3) або 0,
                   якщо експерт об'єкт не назвав.
    """
    n_obj = len(objects)
    n_exp = len(expert_triples)
    idx = {obj: i for i, obj in enumerate(objects)}
    matrix = [[0] * n_exp for _ in range(n_obj)]
    for j, triple in enumerate(expert_triples):
        for rank, obj in enumerate(triple):
            i = idx.get(obj)
            if i is None:
                continue
            matrix[i][j] = rank + 1
    return matrix


def borda_score(matrix_p: Sequence[Sequence[int]]) -> List[int]:
    """
    Агрегатний рейтинг Борда: вага 3 за 1-ше місце, 2 — за 2-ге, 1 — за 3-тє.
    Корисний для порівняння з результатами прямого перебору / ACO.
    """
    return [3 * matrix_p[0][j] + 2 * matrix_p[1][j] + 1 * matrix_p[2][j]
            for j in range(len(matrix_p[0]))]


# ---------------------------------------------------------------------------
# Прямий перебір n!
# ---------------------------------------------------------------------------
def enumerate_all(
    objects: Sequence[str],
    expert_triples: Sequence[Sequence[str]],
    keep_top: int = 10,
):
    """
    Генерує всі n! перестановок та обчислює sum/max критерії.

    Повертає словник:
        {
            "n_perm":           кількість перестановок (n!),
            "best_sum_value":   мінімум суми відстаней,
            "best_sum_rank":    одна з перестановок з мін. сумою,
            "best_max_value":   мінімум максимуму відстаней,
            "best_max_rank":    одна з перестановок з мін. максимумом,
            "all_best_sum":     ВСІ перестановки з мін. сумою,
            "all_best_max":     ВСІ перестановки з мін. максимумом,
            "top_sum":          перші keep_top перестановок з найменшою сумою,
            "top_max":          перші keep_top з найменшим максимумом,
            "sample_perms":     демонстраційні перестановки з обчисленнями,
        }
    """
    best_sum = float("inf")
    best_max = float("inf")
    best_sum_rank: List[str] = []
    best_max_rank: List[str] = []
    all_best_sum: List[List[str]] = []
    all_best_max: List[List[str]] = []

    # купа з keep_top найкращих
    top_sum: List[Tuple[int, int, List[str]]] = []
    top_max: List[Tuple[int, int, List[str]]] = []

    n_perm = 0
    for perm in permutations(objects):
        n_perm += 1
        ranking = list(perm)
        s, m, _ = evaluate_ranking(ranking, expert_triples)

        if s < best_sum:
            best_sum, best_sum_rank = s, ranking
            all_best_sum = [ranking]
        elif s == best_sum:
            all_best_sum.append(ranking)

        if m < best_max:
            best_max, best_max_rank = m, ranking
            all_best_max = [ranking]
        elif m == best_max:
            all_best_max.append(ranking)

        # ведемо коротку таблицю топ-N
        if len(top_sum) < keep_top or s < top_sum[-1][0]:
            top_sum.append((s, m, ranking))
            top_sum.sort(key=lambda x: (x[0], x[1]))
            top_sum = top_sum[:keep_top]
        if len(top_max) < keep_top or m < top_max[-1][1]:
            top_max.append((s, m, ranking))
            top_max.sort(key=lambda x: (x[1], x[0]))
            top_max = top_max[:keep_top]

    # Демонстраційний приклад (п.9): фіксовані перестановки + обчислення
    sample_perms = _build_samples(objects, expert_triples)

    return {
        "n_perm": n_perm,
        "best_sum_value": best_sum,
        "best_sum_rank": best_sum_rank,
        "best_max_value": best_max,
        "best_max_rank": best_max_rank,
        "all_best_sum": all_best_sum,
        "all_best_max": all_best_max,
        "top_sum": top_sum,
        "top_max": top_max,
        "sample_perms": sample_perms,
    }


def _build_samples(objects, expert_triples, n_samples: int = 5):
    """
    Готує таблицю п.9 — продемонструвати правильність обчислень
    на кількох перестановках. Беремо: лексикографічну, обернену,
    зсунуту та дві випадкові.
    """
    import random

    samples = [list(objects), list(reversed(objects))]
    rotated = list(objects[1:]) + [objects[0]]
    samples.append(rotated)
    rng = random.Random(42)
    for _ in range(n_samples - len(samples)):
        s = list(objects)
        rng.shuffle(s)
        samples.append(s)

    rows = []
    for ranking in samples:
        s, m, dists = evaluate_ranking(ranking, expert_triples)
        rows.append({"ranking": ranking, "sum": s, "max": m, "dists": dists})
    return rows


# ---------------------------------------------------------------------------
# Відновлення ранжування за вектором рангів (п.11)
# ---------------------------------------------------------------------------
def recover_ranking_from_ranks(
    objects: Sequence[str],
    rank_vector: Sequence[int],
) -> List[str]:
    """
    На вхід — вектор рангів довжини n: rank_vector[i] = ранг об'єкта objects[i].
    На виході — об'єкти, упорядковані за зростанням рангу.
    """
    pairs = sorted(zip(rank_vector, objects), key=lambda p: p[0])
    return [obj for _, obj in pairs]


def ranking_to_rank_vector(
    objects: Sequence[str],
    ranking: Sequence[str],
) -> List[int]:
    """
    Зворотна операція: за ранжуванням повертає вектор рангів об'єктів
    у вихідному порядку `objects`.
    """
    pos = {obj: i + 1 for i, obj in enumerate(ranking)}
    return [pos[obj] for obj in objects]
