import pandas as pd
import numpy as np
import heapq
from collections import Counter


def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv'):
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col or 'Numero' in col]
    return df[colunas].values.tolist()


def calcular_frequencia(jogos):
    todas = [n for jogo in jogos for n in jogo]
    freq = Counter(todas)
    total = sum(freq.values())
    scores = {n: freq[n] / total for n in range(1, 26)}
    return scores


def score_jogo(jogo, scores):
    return sum(scores[d] for d in jogo)


def beam_search(jogos, beam_width=50, top_k=10):
    scores = calcular_frequencia(jogos)
    candidatos = [([], 0)]  # (jogo parcial, score acumulado)
    for _ in range(15):
        novos_candidatos = []
        for base, score_base in candidatos:
            for n in range(1, 26):
                if n in base:
                    continue
                novo = base + [n]
                novo_score = score_jogo(novo, scores)
                novos_candidatos.append((novo, novo_score))
        candidatos = heapq.nlargest(beam_width, novos_candidatos, key=lambda x: x[1])
    melhores = heapq.nlargest(top_k, candidatos, key=lambda x: x[1])
    return [sorted(m[0]) for m in melhores]


if __name__ == '__main__':
    jogos = carregar_dados()
    resultados = beam_search(jogos)
    print("Melhores jogos por Beam Search:")
    for jogo in resultados:
        print(jogo)
