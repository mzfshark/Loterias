import pandas as pd
import random
from collections import Counter

def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv'):
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col or 'Numero' in col]
    return df[colunas].values.tolist()

def calcular_frequencia(jogos):
    todas = [n for jogo in jogos for n in jogo]
    freq = Counter(todas)
    return freq

def score_combination(combination, freq):
    return sum(freq.get(num, 0) for num in combination)

def beam_search(df, beam_width=50, top_candidates=10):
    freq = calcular_frequencia(df)
    all_nums = list(range(1, 26))

    # Geração de população inicial com diversidade
    population = [set(random.sample(all_nums, 15)) for _ in range(beam_width * 5)]

    # Scoring e ordenação
    scored = sorted(population, key=lambda c: -score_combination(c, freq))

    # Seleção dos melhores
    melhores = [sorted(list(c)) for c in scored[:top_candidates]]
    return melhores

if __name__ == '__main__':
    jogos = carregar_dados()
    resultados = beam_search(jogos)
    print("Melhores jogos por Beam Search:")
    for jogo in resultados:
        print(jogo)
