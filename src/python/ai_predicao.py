# CardioIA Conectada - Ir Além 2: IA Preditiva em Séries Temporais de Saúde
# FIAP - 2TIAO - Grupo 15 - Bruno Gambarini (RM561517)
# Análise de anomalias e previsão de sinais vitais com Machine Learning

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings("ignore")

# ============= CARREGAR DADOS =============
print("=" * 60)
print("  🫀 CardioIA — IA Preditiva em Sinais Vitais")
print("  Grupo 15 — Bruno Gambarini (RM561517)")
print("=" * 60)

df = pd.read_csv("dados_paciente.csv", parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)
print(f"\n📊 Dataset carregado: {len(df)} amostras de {df.index.min().date()} a {df.index.max().date()}")

# ============= 1. DETECÇÃO DE ANOMALIAS (Isolation Forest) =============
print("\n🔍 1. Detectando anomalias com Isolation Forest...")

features = df[["temperatura", "bpm", "umidade"]].fillna(df.mean())

# Treina Isolation Forest
iso_forest = IsolationForest(
    n_estimators=100,
    contamination=0.05,  # espera ~5% de anomalias
    random_state=42,
    n_jobs=-1
)
df["anomalia"] = iso_forest.fit_predict(features)
df["anomalia"] = df["anomalia"].map({1: "Normal", -1: "Anomalia"})

n_anomalias = (df["anomalia"] == "Anomalia").sum()
print(f"   ✅ Anomalias detectadas: {n_anomalias} ({n_anomalias/len(df)*100:.1f}%)")

# Lista top anomalias
anomalias = df[df["anomalia"] == "Anomalia"].head(5)
print("\n   🚨 Exemplos de anomalias detectadas:")
for t, row in anomalias.iterrows():
    print(f"   • {t}: Temp={row['temperatura']:.1f}°C, BPM={row['bpm']:.0f}, Umid={row['umidade']:.1f}%")

# ============= 2. PREVISÃO BPM (Random Forest) =============
print("\n📈 2. Treinando modelo preditivo de BPM (Random Forest)...")

# Engenharia de features para série temporal
df["hora"] = df.index.hour
df["dia_semana"] = df.index.dayofweek
df["bpm_lag1"] = df["bpm"].shift(1).fillna(df["bpm"].mean())
df["bpm_lag2"] = df["bpm"].shift(2).fillna(df["bpm"].mean())
df["bpm_lag3"] = df["bpm"].shift(3).fillna(df["bpm"].mean())
df["bpm_ma6"] = df["bpm"].rolling(6).mean().fillna(df["bpm"].mean())

pred_features = ["temperatura", "hora", "dia_semana", "bpm_lag1", "bpm_lag2", "bpm_lag3", "bpm_ma6"]
X = df[pred_features].fillna(df.mean())
y = df["bpm"]

# Split treino/teste (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

# Treina RandomForest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10)
rf_model.fit(X_train, y_train)

# Avalia
y_pred = rf_model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"   ✅ Modelo treinado!")
print(f"   📊 MAE (Erro Absoluto Médio): {mae:.1f} BPM")
print(f"   📊 RMSE (Raiz Erro Quadrático): {rmse:.1f} BPM")

# Feature importance
importances = pd.DataFrame({
    "feature": pred_features,
    "importancia": rf_model.feature_importances_
}).sort_values("importancia", ascending=False)
print("\n   🔑 Features mais importantes:")
for _, row in importances.iterrows():
    print(f"   • {row['feature']}: {row['importancia']:.3f}")

# ============= 3. FUNÇÃO PREVER BPM =============
def prever_bpm(dados: pd.DataFrame, horas_futuras: int = 24) -> list:
    """Prevê BPM para as próximas N horas usando o modelo Random Forest treinado."""
    ultima_linha = dados.iloc[-1].copy()
    previsoes = []
    
    for h in range(1, horas_futuras + 1):
        hora_futura = (ultima_linha["hora"] + h) % 24
        
        features_input = pd.DataFrame([{
            "temperatura": ultima_linha["temperatura"],
            "hora": hora_futura,
            "dia_semana": (ultima_linha["dia_semana"] + (h // 24)) % 7,
            "bpm_lag1": dados["bpm"].iloc[-h] if h <= len(dados) else ultima_linha["bpm"],
            "bpm_lag2": dados["bpm"].iloc[-h-1] if h+1 <= len(dados) else ultima_linha["bpm"],
            "bpm_lag3": dados["bpm"].iloc[-h-2] if h+2 <= len(dados) else ultima_linha["bpm"],
            "bpm_ma6": dados["bpm"].iloc[-6:].mean()
        }])
        
        pred = rf_model.predict(features_input)[0]
        previsoes.append(round(pred, 1))
    
    return previsoes

# ============= 4. PREVISÃO DEMONSTRAÇÃO =============
print(f"\n🔮 3. Previsão para as próximas 24 horas:")
previsoes_24h = prever_bpm(df, horas_futuras=24)
for i, p in enumerate(previsoes_24h[::3], 1):  # mostra a cada 3h
    print(f"   • +{i*3}h: {p:.0f} BPM")

# ============= 5. VISUALIZAÇÃO =============
print("\n📊 4. Gerando gráficos...")

fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle("CardioIA Conectada — Análise Preditiva de Sinais Vitais\nGrupo 15 — Bruno Gambarini RM561517", 
             fontsize=14, fontweight="bold")

# Gráfico 1: BPM com anomalias
ultimos_7d = df.iloc[-2016:]  # últimos 7 dias (288 amostras/dia)
axes[0].plot(ultimos_7d.index, ultimos_7d["bpm"], "b-", alpha=0.7, label="BPM", linewidth=0.5)
normal = ultimos_7d[ultimos_7d["anomalia"] == "Normal"]
anomalias_plot = ultimos_7d[ultimos_7d["anomalia"] == "Anomalia"]
axes[0].scatter(normal.index, normal["bpm"], c="blue", s=2, alpha=0.3)
axes[0].scatter(anomalias_plot.index, anomalias_plot["bpm"], c="red", s=20, alpha=0.8, label="Anomalia")
axes[0].axhline(y=120, color="orange", linestyle="--", alpha=0.5, label="Limite 120 BPM")
axes[0].set_ylabel("BPM")
axes[0].legend(loc="upper right")
axes[0].set_title("Batimentos Cardíacos — Últimos 7 Dias com Anomalias")

# Gráfico 2: Temperatura com anomalias
axes[1].plot(ultimos_7d.index, ultimos_7d["temperatura"], "r-", alpha=0.5, linewidth=0.5)
temp_normal = ultimos_7d[ultimos_7d["anomalia"] == "Normal"]
temp_anomalia = ultimos_7d[ultimos_7d["anomalia"] == "Anomalia"]
axes[1].scatter(temp_normal.index, temp_normal["temperatura"], c="blue", s=2, alpha=0.3)
axes[1].scatter(temp_anomalia.index, temp_anomalia["temperatura"], c="red", s=20, alpha=0.8)
axes[1].axhline(y=38, color="orange", linestyle="--", alpha=0.5, label="Limite Febre (38°C)")
axes[1].set_ylabel("Temperatura (°C)")
axes[1].legend(loc="upper right")
axes[1].set_title("Temperatura Corporal — Últimos 7 Dias com Anomalias")

# Gráfico 3: Feature Importances
axes[2].barh(importances["feature"], importances["importancia"], color="#1E90FF")
axes[2].set_xlabel("Importância")
axes[2].set_title("Importância das Features no Modelo Random Forest")
axes[2].invert_yaxis()

plt.tight_layout()
plt.savefig("cardioia_ai_predicao.png", dpi=150, bbox_inches="tight")
print("   ✅ Gráfico salvo: cardioia_ai_predicao.png")

print("\n" + "=" * 60)
print("  ✅ Análise preditiva concluída com sucesso!")
print("  📊 Modelo Random Forest treinado (MAE: {:.1f} BPM)".format(mae))
print("  🔍 {n_anomalias} anomalias detectadas pelo Isolation Forest")
print("  🫀 Sistema pronto para monitoramento contínuo")
print("=" * 60)
