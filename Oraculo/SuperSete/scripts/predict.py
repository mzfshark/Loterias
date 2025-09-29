import os
import sys
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from collections import Counter

# Adiciona raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Oraculo.SuperSete.models import frequency
from Oraculo.SuperSete.models import poisson
from Oraculo.SuperSete.models import markov
from Oraculo.SuperSete.models import bayesian
from Oraculo.SuperSete.models import evolutionary

# Configs
DATA_PATH = "Oraculo/SuperSete/data/SuperSete.csv"
OUTPUT_PATH = "Oraculo/SuperSete/predictions"
DOCS_PATH = "Oraculo/SuperSete/docs"

print("\n📊 Carregando dados históricos...")
df_full = pd.read_csv(DATA_PATH)
df_full = df_full.sort_values(by="Concurso").reset_index(drop=True)
df = df_full[[f"Coluna {i}" for i in range(1, 8)]]
print(f"Linhas carregadas: {len(df)} | Último sorteio: Concurso {df_full['Concurso'].iloc[-1]}")

# -----------------------------
# Estatísticas
# -----------------------------
print("\n📈 Calculando estatísticas...")
freqs = frequency.calculate_frequency_by_column(df)
norm_freqs = frequency.normalize_frequency(freqs)
poisson_scores = poisson.column_poisson_scores(freqs)
markov_preds = markov.generate_predictions(df)
priors = bayesian.initialize_priors()
bayes_post = bayesian.update_posteriors(priors, df.tail(10))
top_bayes = bayesian.get_top_candidates(bayes_post, top_n=3)

print("\n🎯 Top 3 dígitos por coluna (modelo Bayesiano):")
for col, digs in top_bayes.items():
    print(f"{col}: {digs}")

# -----------------------------
# Geração de Palpites
# -----------------------------
print("\n🎰 Gerando palpites...")

# Curto prazo (últimos 5)
short_df = df.tail(5)
short_freqs = frequency.calculate_frequency_by_column(short_df)
short_guess = [max(col.items(), key=lambda x: x[1])[0] for col in short_freqs.values()]

# Médio prazo (últimos 20)
mid_df = df.tail(20)
mid_freqs = frequency.calculate_frequency_by_column(mid_df)
mid_guess = [max(col.items(), key=lambda x: x[1])[0] for col in mid_freqs.values()]

# Longo prazo (histórico completo)
long_guess = [max(col.items(), key=lambda x: x[1])[0] for col in freqs.values()]

# Evolutivo
evo_games = evolutionary.evolve_population(
    evolutionary.initialize_population(50),
    freqs,
    generations=30
)

# Bayesian palpite
bayes_guess = [top[0] for top in top_bayes.values()]

# Markov palpite
markov_guess = [max(pred.items(), key=lambda x: x[1])[0] for pred in markov_preds.values()]

# Poisson palpite
poisson_guess = [max(scores.items(), key=lambda x: x[1])[0] for scores in poisson_scores.values()]

# Palpite da rodada (baseado nas dezenas mais frequentes entre todos os palpites)
all_jogos = [short_guess, mid_guess, long_guess, bayes_guess, markov_guess, poisson_guess] + evo_games
palpite_rodada = [Counter([jogo[i] for jogo in all_jogos]).most_common(1)[0][0] for i in range(7)]

# -----------------------------
# Salvamento
# -----------------------------
print("\n💾 Salvando palpites...")
today = datetime.now().strftime("%Y-%m-%d")
os.makedirs(OUTPUT_PATH, exist_ok=True)

output = [
    {"modelo": "curto_prazo", "jogo": short_guess},
    {"modelo": "medio_prazo", "jogo": mid_guess},
    {"modelo": "longo_prazo", "jogo": long_guess},
    {"modelo": "bayesiano", "jogo": bayes_guess},
    {"modelo": "markov", "jogo": markov_guess},
    {"modelo": "poisson", "jogo": poisson_guess},
    {"modelo": "palpite_rodada", "jogo": palpite_rodada},
]
for j in evo_games:
    output.append({"modelo": "evolutivo", "jogo": j})

json_path = os.path.join(OUTPUT_PATH, f"prediction_{today}.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

csv_path = os.path.join(OUTPUT_PATH, f"prediction_{today}.csv")
pd.DataFrame([{**{"col"+str(i+1): num for i, num in enumerate(x['jogo'])}, "modelo": x['modelo']} for x in output]).to_csv(csv_path, index=False)

print(f"\n✅ Previsões salvas:")
print(f"- JSON: {json_path}")
print(f"- CSV : {csv_path}")

# -----------------------------
# Geração de Tabelas e Gráficos
# -----------------------------
os.makedirs(DOCS_PATH, exist_ok=True)

# Tabela de frequência por coluna
freq_table = pd.DataFrame.from_dict(freqs, orient="index").fillna(0).astype(int)
freq_table = freq_table.reindex(columns=range(10)).fillna(0)
freq_table = freq_table.T  # Transforma para que dezenas (0-9) fiquem no eixo Y e colunas (1-7) no eixo X
freq_table = freq_table.sort_index(ascending=True)  # Garante que 0 fique no topo
freq_table.columns = [f"Coluna {i}" for i in range(1, 8)]

# Heatmap consolidado
fig = go.Figure(data=go.Heatmap(
    z=freq_table.values,
    x=freq_table.columns,
    y=freq_table.index,
    colorscale=[[0, '#f7fbec'], [0.5, '#afd355'], [1, '#6b8c21']],
    text=freq_table.index.values[:, None].repeat(freq_table.shape[1], axis=1),
    texttemplate="%{text}",
    hoverinfo="y+z"
))
fig.update_layout(
    title="Heatmap de Frequência por Coluna (0 a 9)",
    xaxis_title="Colunas",
    yaxis_title="Dezenas",
    height=500,
    paper_bgcolor="#0b0f14",
    plot_bgcolor="#0f1720",
    font=dict(color="#e8eef5"),
    margin=dict(l=40, r=20, t=60, b=40)
)
fig.write_html(os.path.join(DOCS_PATH, "heatmap.html"))

print("\n📊 Relatórios gerados na pasta docs.")
print("\n🚀 Pipeline de previsão finalizada com sucesso.")
