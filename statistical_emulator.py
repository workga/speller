from collections import defaultdict
from itertools import product
import random
import matplotlib.pyplot as plt 


prob_tp_options = [0.7, 0.75, 0.8, 0.85, 0.9]
prob_tn_options = [0.7, 0.75, 0.8, 0.85, 0.9]
n_options = [3, 4, 5, 6, 7, 8, 9, 10]
treshold = 0.99


SIZE = 16
TIMES = 1000


def run_option(prob_tp: float, prob_tn: float, n: int) -> float:
    target = 5
    stats = []
    prob_fp = 1 - prob_tn
    for _ in range(TIMES):
        accum = [0] * SIZE
        for i in range(SIZE):
            prob = prob_tp if i == target else prob_fp
            accum[i] = sum(int(random.random() < prob) for _ in range(n))

        if max(enumerate(accum), key=lambda item: item[1])[0] == target:
            stats.append(1)
        else:
            stats.append(0)

    return sum(stats) / TIMES

def run_options(subset: int | None = None) -> dict[tuple[float, float], list[tuple[int, float]]]:
    results = defaultdict(list)
    options = list(product(prob_tp_options, prob_tn_options, n_options))[:subset]
    for i, (prob_tp, prob_tn, n) in enumerate(options):
        result = run_option(prob_tp, prob_tn, n)
        results[prob_tp, prob_tn].append((n, result))
        print(f"Done {i} / {len(options)} or {int(i / len(options) * 100)}%")

    return results


def plot_results(results: dict[tuple[float, float], list[tuple[int, float]]], treshold: float) -> None:
    _, axis = plt.subplots(len(prob_tp_options), len(prob_tn_options)) 
  
    for i, j in product(range(len(prob_tp_options)), range(len(prob_tn_options))):
        data = results[prob_tp_options[i], prob_tn_options[j]]
        min_n = None
        for n, result in sorted(data):
            if result >= treshold:
                min_n = n
                break
        color = 'r' if min_n else 'b'
        title = f"TP:{prob_tp_options[i]} TN:{prob_tn_options[j]}"
        if min_n:
            title += f', N:{min_n}, time:{round(0.2 + min_n * 0.160 * SIZE, 2)}'

        x , y = list(zip(*data))
        axis[i, j].plot(x, y, color=color)
        axis[i, j].set_title(title, fontdict={'fontsize': 12, 'color': color}) 
        axis[i, j].set_xlim(0, max(n_options))
        axis[i, j].set_ylim(0, 1)
 
    plt.rcParams['figure.constrained_layout.use'] = True
    plt.subplots_adjust(wspace=0.6, hspace=0.6)
    plt.show()


def main() -> None:
    results = run_options()
    assert len(results) == len(prob_tp_options) * len(prob_tn_options)
    plot_results(results, treshold)

if __name__ == '__main__':
    main()