import pandas as pd
import numpy as np
import random
from collections import Counter


def carregar_dados(path='Lotofacil/data/Lotofacil.csv'):
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col or 'Numero' in col]
    return df[colunas].values.tolist()


def calcular_probabilidades(jogos):
    todas = [n for jogo in jogos for n in jogo]
    freq = Counter(todas)
    total = sum(freq.values())
    probs = {n: freq[n] / total for n in range(1, 26)}
    return probs


def mutar(jogo_base, probs, taxa_mutacao=0.3):
    jogo = jogo_base[:]
    for i in range(len(jogo)):
        if random.random() < taxa_mutacao:
            candidatos = [n for n in range(1, 26) if n not in jogo]
            pesos = [probs[n] for n in candidatos]
            if candidatos:
                novo = random.choices(candidatos, weights=pesos, k=1)[0]
                jogo[i] = novo
    # Garantir que o jogo tenha 15 dezenas únicas
    jogo = sorted(set(jogo))
    while len(jogo) < 15:
        candidatos = [n for n in range(1, 26) if n not in jogo]
        novo = random.choices(candidatos, weights=[probs[n] for n in candidatos], k=1)[0]
        jogo.append(novo)
    return sorted(jogo[:15])


def gerar_populacao_base(jogos, n=10):
    return [sorted(random.sample(range(1, 26), 15)) for _ in range(n)]


def gerar_mutacoes(jogos_hist, num_mutantes=10, taxa_mutacao=0.3):
    probs = calcular_probabilidades(jogos_hist)
    base = gerar_populacao_base(jogos_hist, n=num_mutantes)
    mutantes = [mutar(jogo, probs, taxa_mutacao) for jogo in base]
    return mutantes


if __name__ == '__main__':
    jogos = carregar_dados()
    mutacoes = gerar_mutacoes(jogos)
    print("Mutantes gerados com base em mutação probabilística:")
    for m in mutacoes:
        print(m)
