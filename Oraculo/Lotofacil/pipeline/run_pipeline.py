import os
import json
from datetime import datetime

from Lotofacil.models.poisson import carregar_dados as dados_poisson, calcular_frequencias, ajustar_poisson
from Lotofacil.models.markov import carregar_dados as dados_markov, construir_matriz_transicao, prever_proximas
from Lotofacil.models.beam_search import carregar_dados as dados_beam, beam_search
from Lotofacil.models.mutation import carregar_dados as dados_mut, gerar_mutacoes


def salvar_previsoes(nome_modelo, jogos):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"lotofacil/predictions/{timestamp}_{nome_modelo}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(jogos, f, ensure_ascii=False, indent=2)
    print(f"✅ Previsões salvas em: {path}")


def executar_poisson():
    print("[Poisson] Gerando previsão com base na frequência histórica...")
    series = dados_poisson()
    freq_abs, freq_rel = calcular_frequencias(series)
    ajuste, _ = ajustar_poisson(freq_abs)
    top_15 = sorted(freq_abs.sort_values(ascending=False).head(15).index.tolist())
    salvar_previsoes("poisson", [top_15])


def executar_markov():
    print("[Markov] Gerando previsão com Cadeia de Markov...")
    dados = dados_markov()
    matriz = construir_matriz_transicao(dados)
    estado_inicial = 1  # valor fixo ou sorteado aleatoriamente
    previsao = prever_proximas(matriz, estado_inicial)
    salvar_previsoes("markov", [previsao])


def executar_beam():
    print("[Beam Search] Gerando melhores combinações...")
    dados = dados_beam()
    resultados = beam_search(dados)
    salvar_previsoes("beam", resultados)


def executar_mutation():
    print("[Mutation] Gerando mutações probabilísticas...")
    dados = dados_mut()
    mutantes = gerar_mutacoes(dados)
    salvar_previsoes("mutation", mutantes)


if __name__ == '__main__':
    executar_poisson()
    executar_markov()
    executar_beam()
    executar_mutation()
    print("\n🎯 Pipeline finalizada com sucesso.")
