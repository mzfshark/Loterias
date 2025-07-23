import pandas as pd
import numpy as np
import os
from scipy.stats import hypergeom
import random
import matplotlib.pyplot as plt
import seaborn as sns

def score_frequency(df, alpha=0.5, short_window=50):
    hist = df.values.flatten()
    freq_long = pd.Series(hist).value_counts(normalize=True)
    freq_short = pd.Series(df.tail(short_window).values.flatten()).value_counts(normalize=True)
    scores = {}
    for num in range(1, 26):
        scores[num] = alpha * freq_long.get(num, 0) + (1-alpha) * freq_short.get(num, 0)
    return scores


def monte_carlo_opt(scores, trials=100000):
    p = np.array([scores[i] for i in range(1, 26)])
    p = p / p.sum()
    best_set, best_exp = None, -1
    for _ in range(trials):
        combo = np.random.choice(range(1, 26), 15, replace=False, p=p)
        exp_hits = sum(scores[i] for i in combo)
        if exp_hits > best_exp:
            best_exp, best_set = exp_hits, combo
    return sorted(best_set.tolist())


def genetic_algorithm(scores, pop_size=100, generations=50):
    def fitness(ind): return sum(scores[i] for i in ind)
    population = [random.sample(range(1, 26), 15) for _ in range(pop_size)]
    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_pop = population[:pop_size // 2]
        while len(next_pop) < pop_size:
            p1, p2 = random.sample(population[:20], 2)
            cut = random.randint(1, 14)
            child = p1[:cut] + [g for g in p2 if g not in p1[:cut]]
            if random.random() < 0.1:
                i, j = random.sample(range(15), 2)
                child[i], child[j] = child[j], child[i]
            next_pop.append(child)
        population = next_pop
    return sorted(population[0])


def salvar_relatorio(mc_set, ga_set, df, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    freq_long = pd.Series(df.values.flatten()).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    plt.figure(figsize=(10, 2))
    sns.heatmap(freq_long.values.reshape(1, 25), annot=True, fmt='.2%', cbar=True, cmap='Reds',
                xticklabels=freq_long.index.tolist(), yticklabels=['Freq%'])
    plt.tight_layout()
    heatmap_path = os.path.join(os.path.dirname(path), 'heatmap.png')
    plt.savefig(heatmap_path)
    plt.close()
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"![Heatmap de Frequências]({os.path.basename(heatmap_path)})\n\n")
        f.write("## Conjunto Frequency-Weighted + Monte Carlo\n")
        f.write(f"{mc_set}\n\n")
        f.write("## Conjunto Genetic Algorithm\n")
        f.write(f"{ga_set}\n")

if __name__ == '__main__':
    csv_path = 'Lotofacil/data/Lotofacil.csv'
    if not os.path.exists(csv_path):
        print("Arquivo de dados não encontrado.")
        exit(1)
    df_raw = pd.read_csv(csv_path)
    df = df_raw.iloc[:, 2:17]
    df.columns = [f"Numero{i}" for i in range(1, 16)]
    scores = score_frequency(df)
    mc = monte_carlo_opt(scores)
    ga = genetic_algorithm(scores)
    salvar_relatorio(mc, ga, df)
