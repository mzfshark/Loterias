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


def genetic_algorithm(scores, pop_size=100, generations=50, elite_frac=0.2, mutation_rate=0.1):
    def fitness(ind): return sum(scores[i] for i in ind)
    population = [random.sample(range(1, 26), 15) for _ in range(pop_size)]
    elite_size = max(1, int(elite_frac * pop_size))
    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        new_pop = population[:elite_size]
        weights = [fitness(ind) for ind in population]
        while len(new_pop) < pop_size:
            p1, p2 = random.choices(population, weights=weights, k=2)
            cut = random.randint(1, 14)
            child = p1[:cut]
            for g in p2:
                if len(child) >= 15:
                    break
                if g not in child:
                    child.append(g)
            missing = [n for n in range(1,26) if n not in child]
            while len(child) < 15:
                child.append(random.choice(missing))
            if random.random() < mutation_rate:
                i, j = random.sample(range(15), 2)
                child[i], child[j] = child[j], child[i]
            new_pop.append(child)
        population = new_pop
    population.sort(key=fitness, reverse=True)
    return sorted(population[0])


def salvar_relatorio(mc_set, ga_set, df, path="Lotofacil/docs/index.md"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    freq = pd.Series(df.values.flatten()).value_counts(normalize=True).reindex(range(1, 26), fill_value=0)
    df_freq = freq.rename_axis('Number').reset_index(name='Frequency')
    headers = ['Number', 'Frequency']
    rows = df_freq.values.tolist()
    md_table = '| ' + ' | '.join(headers) + ' |\n'
    md_table += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
    for num, freq_val in rows:
        md_table += f'| {num} | {freq_val:.2%} |\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('## Frequência Histórica\n')
        f.write(md_table + '\n')
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
    df.columns = [f'Numero{i}' for i in range(1, 16)]
    scores = score_frequency(df)
    mc = monte_carlo_opt(scores)
    ga = genetic_algorithm(scores)
    salvar_relatorio(mc, ga, df)
