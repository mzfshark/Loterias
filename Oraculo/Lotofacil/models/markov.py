import pandas as pd
import numpy as np
from collections import defaultdict, Counter


def carregar_dados(path='lotofacil/data/Lotofacil.csv'):
    df = pd.read_csv(path)
    colunas = [col for col in df.columns if 'Bola' in col or 'Numero' in col]
    return df[colunas].values.tolist()


def construir_matriz_transicao(sequencias):
    transicoes = defaultdict(Counter)
    for jogo in sequencias:
        jogo_ordenado = sorted(jogo)
        for i in range(len(jogo_ordenado) - 1):
            atual = jogo_ordenado[i]
            prox = jogo_ordenado[i + 1]
            transicoes[atual][prox] += 1

    matriz = {}
    for dezena, contagem in transicoes.items():
        total = sum(contagem.values())
        matriz[dezena] = {k: v / total for k, v in contagem.items()}
    return matriz


def prever_proximas(matriz, estado_inicial, tamanho=15):
    atual = estado_inicial
    previsao = [atual]
    while len(previsao) < tamanho:
        if atual not in matriz or not matriz[atual]:
            break
        proximos = list(matriz[atual].keys())
        probs = list(matriz[atual].values())
        atual = np.random.choice(proximos, p=probs)
        if atual not in previsao:
            previsao.append(atual)
    while len(previsao) < tamanho:
        candidato = np.random.randint(1, 26)
        if candidato not in previsao:
            previsao.append(candidato)
    return sorted(previsao)


if __name__ == '__main__':
    dados = carregar_dados()
    matriz = construir_matriz_transicao(dados)
    estado_inicial = np.random.choice(range(1, 26))
    previsao = prever_proximas(matriz, estado_inicial)
    print("Previsão baseada em Cadeia de Markov:", previsao)
