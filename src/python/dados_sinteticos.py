# CardioIA Conectada - Gerador de Dataset Sintético
# FIAP - 2TIAO - Grupo 15 - Bruno Gambarini (RM561517)
# Gera dados realistas de paciente cardíaco para 30 dias de monitoramento

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configurações
DIAS = 30
AMOSTRAS_POR_DIA = 288  # 1 leitura a cada 5 minutos (12*24)
TOTAL_AMOSTRAS = DIAS * AMOSTRAS_POR_DIA

# Parâmetros fisiológicos
TEMP_BASE = 36.5
TEMP_AMPLITUDE = 0.8    # variação diurna ±0.8°C
BPM_BASE = 72
BPM_AMPLITUDE = 15       # variação diurna ±15 BPM
UMIDADE_BASE = 65
UMIDADE_AMPLITUDE = 10

np.random.seed(42)
data_inicio = datetime(2026, 4, 12, 0, 0, 0)

# Gera timestamps
timestamps = [data_inicio + timedelta(minutes=5 * i) for i in range(TOTAL_AMOSTRAS)]

# Padrão diurno: senoide de 24h
horas = np.array([t.hour + t.minute / 60 for t in timestamps])
fase_diurna = np.sin(2 * np.pi * (horas - 6) / 24)

# Temperatura: oscila ao longo do dia
temperatura = TEMP_BASE + TEMP_AMPLITUDE * fase_diurna + np.random.normal(0, 0.2, TOTAL_AMOSTRAS)

# BPM: mais alto durante o dia, mais baixo à noite
bpm = BPM_BASE + BPM_AMPLITUDE * fase_diurna + np.random.normal(0, 5, TOTAL_AMOSTRAS)
bpm = np.clip(bpm, 50, 160)

# Umidade: oposta à temperatura
umidade = UMIDADE_BASE - UMIDADE_AMPLITUDE * fase_diurna + np.random.normal(0, 3, TOTAL_AMOSTRAS)
umidade = np.clip(umidade, 30, 95)

# Simula eventos cardíacos (picos de BPM e temperatura)
# Dia 5: pico de estresse
evento1 = slice(5 * AMOSTRAS_POR_DIA, 5 * AMOSTRAS_POR_DIA + 24)
bpm[evento1] += np.random.normal(20, 5, 24)
temperatura[evento1] += np.random.normal(0.8, 0.2, 24)

# Dia 12: febre + taquicardia
evento2 = slice(12 * AMOSTRAS_POR_DIA, 12 * AMOSTRAS_POR_DIA + 48)
bpm[evento2] += np.random.normal(30, 10, 48)
temperatura[evento2] += np.random.normal(2.5, 0.5, 48)

# Dia 22: pico de atividade
evento3 = slice(22 * AMOSTRAS_POR_DIA, 22 * AMOSTRAS_POR_DIA + 12)
bpm[evento3] += np.random.normal(35, 15, 12)

# Status de conexão: 95% online, com quedas ocasionais
status = np.random.choice(["online", "offline"], TOTAL_AMOSTRAS, p=[0.95, 0.05])

# Cria DataFrame
df = pd.DataFrame({
    "timestamp": timestamps,
    "temperatura": temperatura.round(2),
    "umidade": umidade.round(2),
    "bpm": bpm.round(0).astype(int),
    "status_conexao": status
})

# Salva CSV
df.to_csv("src/python/dados_paciente.csv", index=False, encoding="utf-8")

print("=" * 50)
print("  CardioIA — Dataset Sintético Gerado")
print("  Grupo 15 — Bruno Gambarini RM561517")
print("=" * 50)
print(f"\n📊 Dados gerados:")
print(f"  • Período: {df['timestamp'].min()} a {df['timestamp'].max()}")
print(f"  • Amostras: {len(df)} ({DIAS} dias x {AMOSTRAS_POR_DIA}/dia)")
print(f"\n📈 Estatísticas:")
print(f"  • Temperatura: {df['temperatura'].min():.1f}°C a {df['temperatura'].max():.1f}°C (média: {df['temperatura'].mean():.1f}°C)")
print(f"  • BPM: {df['bpm'].min():.0f} a {df['bpm'].max():.0f} (média: {df['bpm'].mean():.0f})")
print(f"  • Umidade: {df['umidade'].min():.1f}% a {df['umidade'].max():.1f}% (média: {df['umidade'].mean():.1f}%)")
print(f"\n🫀 Eventos cardíacos simulados:")
print(f"  • Dia 5: Pico de estresse (BPM {df.iloc[evento1].bpm.max():.0f})")
print(f"  • Dia 12: Febre + taquicardia (Temp {df.iloc[evento2].temperatura.max():.1f}°C, BPM {df.iloc[evento2].bpm.max():.0f})")
print(f"  • Dia 22: Pico de atividade (BPM {df.iloc[evento3].bpm.max():.0f})")
print(f"\n💾 Arquivo salvo: src/python/dados_paciente.csv")
