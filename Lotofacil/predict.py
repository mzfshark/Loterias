import pandas as pd
import numpy as np
import os
import random


def score_frequency(df, alpha=0.5, short_window=50):
    hist = df.values.flatten()
    freq_long = pd.Series(hist).value_counts(normalize=True)
    freq_short = pd.Series(df.tail(short_window).values.flatten()).value_counts(normalize=True)
    return {num: alpha * freq_long.get(num, 0) + (1-alpha) * freq_short.get(num, 0) for num in range(1, 26)}


def monte_carlo_opt(scores, trials=100000):
    p = np.array([scores[i] for i in range(1, 26)])
    p /= p.sum()
    best_set, best_score = None, -1
    for _ in range(trials):
        combo = np.random.choice(range(1, 26), 15, replace=False, p=p)
        score = sum(scores[i] for i in combo)
        if score > best_score:
            best_score, best_set = score, combo
    return sorted(best_set.tolist())


def genetic_algorithm(scores, pop_size=100, generations=50):
    def fitness(ind): return sum(scores[i] for i in ind)
    population = [random.sample(range(1, 26), 15) for _ in range(pop_size)]
    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        survivors = population[:pop_size//2]
        while len(survivors) < pop_size:
            p1, p2 = random.sample(survivors, 2)
            cut = random.randint(1, 14)
            child = p1[:cut] + [x for x in p2 if x not in p1[:cut]]
            if random.random() < 0.1:
                i, j = random.sample(range(15), 2)
                child[i], child[j] = child[j], child[i]
            survivors.append(child)
        population = survivors
    return sorted(max(population, key=fitness))


def salvar_relatorio(mc_set, ga_set, df, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    freq = pd.Series(df.values.flatten()).value_counts(normalize=True).reindex(range(1,26), fill_value=0)
    df_freq = freq.rename_axis('Number').reset_index(name='Frequency')
    md_table = df_freq.to_markdown(index=False, floatfmt=".2%")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('## Frequência Histórica\n')
        f.write(md_table + '\n\n')
        f.write('## Conjunto Monte Carlo\n')
        f.write(str(mc_set) + '\n\n')
        f.write('## Conjunto Genetic Algorithm\n')
        f.write(str(ga_set) + '\n')

if __name__ == '__main__':
    csv_path = 'Lotofacil/data/Lotofacil.csv'
    if not os.path.exists(csv_path):
        print('Arquivo de dados não encontrado.')
        exit(1)
    df_raw = pd.read_csv(csv_path)
    df = df_raw.iloc[:, 2:17]
    df.columns = [f'Numero{i}' for i in range(1,16)]
    scores = score_frequency(df)
    mc = monte_carlo_opt(scores)
    ga = genetic_algorithm(scores)
    salvar_relatorio(mc, ga, df)
