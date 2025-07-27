import pandas as pd
import numpy as np
from scipy.stats import poisson


def carregar_dados(path='Oraculo/Lotofacil/data/Lotofacil.csv'):
    df = pd.read_csv(path)
    colunas_bolas = [col for col in df.columns if 'Bola' in col or 'Numero' in col]
    dezenas = df[colunas_bolas].values.flatten()
    return pd.Series(dezenas)


def calcular_frequencias(series):
    freq_abs = series.value_counts().sort_index()
    freq_rel = freq_abs / len(series)
    return freq_abs, freq_rel


def ajustar_poisson(freq_abs):
    media = freq_abs.mean()
    ajuste = {dezena: poisson.pmf(k=freq, mu=media) for dezena, freq in freq_abs.items()}
    return ajuste, media


def gerar_tabela_probabilidades(freq_abs, freq_rel, ajuste_poisson):
    df = pd.DataFrame({
        'Dezena': freq_abs.index,
        'Frequência Absoluta': freq_abs.values,
        'Frequência Relativa (%)': (freq_rel.values * 100).round(2),
        'Probabilidade Poisson': [ajuste_poisson[d] for d in freq_abs.index]
    })
    return df.sort_values(by='Dezena')


if __name__ == '__main__':
    series = carregar_dados()
    freq_abs, freq_rel = calcular_frequencias(series)
    ajuste, media = ajustar_poisson(freq_abs)
    tabela = gerar_tabela_probabilidades(freq_abs, freq_rel, ajuste)

    print("Média de ocorrências por dezena:", media)
    print(tabela.to_markdown(index=False))
