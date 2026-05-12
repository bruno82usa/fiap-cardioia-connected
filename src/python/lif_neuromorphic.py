# CardioIA Conectada - Ir Além 2: Modelo Neuromórfico LIF (Leaky Integrate-and-Fire)
# FIAP - 2TIAO - Grupo 15 - Bruno Gambarini (RM561517)
# Implementa e compara classificador tradicional vs rede neuromórfica em sinais vitais

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler

# ============= MODELO NEUROMÓRFICO LIF =============
class LIFNeuron:
    """
    Leaky Integrate-and-Fire (LIF) — neurônio spiking bioplausível.
    
    O neurônio acumula potencial de membrana proporcional à corrente de entrada,
    com decaimento exponencial (leak). Quando o potencial atinge o limiar V_threshold,
    dispara um spike e reseta para V_reset.
    """
    
    def __init__(self, tau_m=10.0, v_threshold=1.0, v_reset=0.0, v_rest=0.0, dt=0.1):
        self.tau_m = tau_m              # Constante de tempo da membrana (ms)
        self.v_threshold = v_threshold  # Limiar de disparo
        self.v_reset = v_reset          # Potencial de reset pós-spike
        self.v_rest = v_rest            # Potencial de repouso
        self.dt = dt                    # Passo temporal (ms)
        self.v = v_rest                 # Potencial atual
        self.spikes = []                # Histórico de spikes
        
    def step(self, current: float) -> int:
        """Avança 1 passo temporal. Retorna 1 se spike, 0 se não."""
        dv = (self.v_rest - self.v + current) / self.tau_m * self.dt
        self.v += dv
        
        spike = 0
        if self.v >= self.v_threshold:
            spike = 1
            self.v = self.v_reset
            self.spikes.append(1)
        else:
            self.spikes.append(0)
        
        return spike
    
    def get_spike_rate(self) -> float:
        """Taxa de disparo em Hz."""
        if len(self.spikes) == 0:
            return 0.0
        total_time = len(self.spikes) * self.dt / 1000.0  # segundos
        return sum(self.spikes) / total_time if total_time > 0 else 0.0

class LIFNetwork:
    """
    Rede LIF para classificação binária de sinais vitais.
    
    Arquitetura:
    - Neurônio 1: sensível a BPM elevado (> taquicardia)
    - Neurônio 2: sensível a temperatura elevada (> febre)
    - Camada de saída: combina spikes para decisão
    
    Inspirado no modelo FitzHugh-Nagumo simplificado.
    """
    
    def __init__(self, bpm_threshold=120, temp_threshold=38.0):
        # Dois neurônios sensoriais
        self.neuron_bpm = LIFNeuron(tau_m=10.0, v_threshold=1.0)
        self.neuron_temp = LIFNeuron(tau_m=8.0, v_threshold=0.8)
        
        # Parâmetros de normalização
        self.bpm_threshold = bpm_threshold
        self.temp_threshold = temp_threshold
        self.bpm_scale = 0.01   # fator de escala BPM → corrente
        self.temp_scale = 0.5   # fator de escala temperatura → corrente
        
        self.spike_history = []
        
    def processar_amostra(self, bpm: float, temperatura: float, time_steps: int = 50) -> dict:
        """
        Processa uma amostra de sinais vitais pela rede LIF.
        
        Cada neurônio recebe corrente proporcional ao desvio do valor basal.
        Se BPM > 120, neurônio BPM dispara mais.
        Se Temperatura > 38, neurônio temp dispara mais.
        """
        self.spike_history = []
        spikes_bpm_total = 0
        spikes_temp_total = 0
        
        # Corrente de entrada normalizada
        current_bpm = max(0, (bpm - 60) * self.bpm_scale)    # BPM basal = 60
        current_temp = max(0, (temperatura - 36.0) * self.temp_scale)  # Temp basal = 36
        
        for t in range(time_steps):
            s_bpm = self.neuron_bpm.step(current_bpm)
            s_temp = self.neuron_temp.step(current_temp)
            
            spikes_bpm_total += s_bpm
            spikes_temp_total += s_temp
            
            self.spike_history.append({
                't': t,
                'bpm_spike': s_bpm,
                'temp_spike': s_temp,
                'v_bpm': self.neuron_bpm.v,
                'v_temp': self.neuron_temp.v
            })
        
        # Decisão: alerta se taxa de disparo de qualquer neurônio > limiar
        rate_bpm = self.neuron_bpm.get_spike_rate()
        rate_temp = self.neuron_temp.get_spike_rate()
        
        alerta = (rate_bpm > 5.0) or (rate_temp > 3.0)
        
        return {
            'alerta': alerta,
            'spike_rate_bpm': rate_bpm,
            'spike_rate_temp': rate_temp,
            'total_spikes_bpm': spikes_bpm_total,
            'total_spikes_temp': spikes_temp_total,
            'current_bpm': current_bpm,
            'current_temp': current_temp,
            'spike_history': self.spike_history
        }

# ============= DATASET E PREPARAÇÃO =============
print("=" * 65)
print("  🧠 CardioIA — Modelo Neuromórfico LIF vs Regressão Logística")
print("  Grupo 15 — Bruno Gambarini (RM561517)")
print("=" * 65)

# Carrega dataset sintético
try:
    df = pd.read_csv("dados_paciente.csv", parse_dates=["timestamp"])
except:
    # Gera na hora se não existir
    print("\n⚠️ Dataset não encontrado. Gerando dados sintéticos...")
    from dados_sinteticos import TOTAL_AMOSTRAS
    exec(open("dados_sinteticos.py").read())
    df = pd.read_csv("dados_paciente.csv", parse_dates=["timestamp"])

print(f"\n📊 Dataset: {len(df)} amostras")

# Cria labels: 1 = alerta (BPM>120 OU temp>38), 0 = normal
df['alerta'] = ((df['bpm'] > 120) | (df['temperatura'] > 38.0)).astype(int)
n_alertas = df['alerta'].sum()
print(f"   • Amostras normais: {len(df) - n_alertas}")
print(f"   • Amostras alerta:   {n_alertas}")

# Features para o classificador tradicional
feature_cols = ['temperatura', 'bpm', 'umidade']
X = df[feature_cols].values
y = df['alerta'].values

# StandardScaler pro modelo tradicional
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split treino/teste
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# ============= 1. CLASSIFICADOR TRADICIONAL (Regressão Logística) =============
print("\n📈 1. Treinando Regressão Logística...")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)

acc_lr = accuracy_score(y_test, y_pred_lr)
print(f"   ✅ Acurácia: {acc_lr:.2%}")
print(f"   📊 Coeficientes:")
print(f"      • Temperatura: {lr.coef_[0][0]:.3f}")
print(f"      • BPM: {lr.coef_[0][1]:.3f}")
print(f"      • Umidade: {lr.coef_[0][2]:.3f}")

# ============= 2. REDE NEUROMÓRFICA LIF =============
print("\n🧠 2. Executando Rede Neuromórfica LIF...")
lif_net = LIFNetwork(bpm_threshold=120, temp_threshold=38.0)

y_pred_lif = []
spike_rates = []
total_amostras = len(df) // 4  # 25% do dataset (suficiente pra demonstração)

for i in range(total_amostras):
    resultado = lif_net.processar_amostra(
        bpm=df.iloc[i]['bpm'],
        temperatura=df.iloc[i]['temperatura'],
        time_steps=100
    )
    y_pred_lif.append(1 if resultado['alerta'] else 0)
    spike_rates.append((resultado['spike_rate_bpm'], resultado['spike_rate_temp']))

y_test_lif = df['alerta'].iloc[:total_amostras].values
acc_lif = accuracy_score(y_test_lif, y_pred_lif)
print(f"   ✅ Acurácia LIF: {acc_lif:.2%}")

# ============= 3. COMPARAÇÃO E ANÁLISE =============
print("\n📊 3. Comparação: Regressão Logística vs Rede LIF")
print("   " + "=" * 50)
print(f"   {'Métrica':<20} {'Reg.Logística':>15} {'Rede LIF':>15}")
print("   " + "-" * 50)
print(f"   {'Acurácia':<20} {acc_lr:>15.2%} {acc_lif:>15.2%}")

# Matriz de confusão da regressão logística
cm = confusion_matrix(y_test, y_pred_lr)
print(f"   {'Precisão (LR)':<20} {'Normal: ' + str(cm[0]):>15} {'Alerta: ' + str(cm[1]):>15}")

print(f"\n   🔬 Vantagens da Rede LIF:")
print(f"      • Bioplausível: simula comportamento real de neurônios")
print(f"      • Eficiência energética: spikes esparsos consomem menos")
print(f"      • Processamento temporal: captura dinâmica dos sinais")
print(f"      • Inspirado em chips neuromórficos (Loihi, TrueNorth)")

print(f"\n   ⚡ Vantagens da Regressão Logística:")
print(f"      • Treinamento rápido e interpretável")
print(f"      • Funciona bem com poucos dados")
print(f"      • Coeficientes diretamente interpretáveis")
print(f"      • Padrão da indústria para classificação binária")

# ============= 4. VISUALIZAÇÃO =============
print("\n🎨 4. Gerando gráficos comparativos...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Comparação: Regressão Logística vs Rede LIF Neuromórfica\nCardioIA — Grupo 15 — Bruno Gambarini RM561517", 
             fontsize=13, fontweight="bold")

# Gráfico 1: Comportamento do neurônio LIF (normal vs alerta)
# Amostra normal (BPM=72, Temp=36.5)
lif_normal = LIFNetwork()
resultado_normal = lif_normal.processar_amostra(bpm=72, temperatura=36.5, time_steps=100)
hist_normal = pd.DataFrame(resultado_normal['spike_history'])

# Amostra alerta (BPM=135, Temp=39.0)
lif_alerta = LIFNetwork()
resultado_alerta = lif_alerta.processar_amostra(bpm=135, temperatura=39.0, time_steps=100)
hist_alerta = pd.DataFrame(resultado_alerta['spike_history'])

axes[0, 0].plot(hist_normal['t'], hist_normal['v_bpm'], 'b-', alpha=0.7, label='V_m BPM (normal)', linewidth=0.8)
axes[0, 0].plot(hist_alerta['t'], hist_alerta['v_bpm'], 'r-', alpha=0.7, label='V_m BPM (alerta)', linewidth=0.8)
axes[0, 0].axhline(y=1.0, color='gray', linestyle='--', alpha=0.3, label='Limiar')
for t in hist_alerta[hist_alerta['bpm_spike'] == 1]['t']:
    axes[0, 0].axvline(x=t, color='red', alpha=0.2, linewidth=0.5)
axes[0, 0].set_xlabel('Tempo (ms)')
axes[0, 0].set_ylabel('Potencial de Membrana (V)')
axes[0, 0].set_title('Neurônio LIF — BPM: Normal vs Alerta')
axes[0, 0].legend(fontsize=7)

# Gráfico 2: Taxa de disparo (spike rate) por amostra
axes[0, 1].scatter([s[0] for s in spike_rates[:200]], [s[1] for s in spike_rates[:200]], 
                   c=['red' if a else 'blue' for a in y_pred_lif[:200]], alpha=0.6, s=15)
axes[0, 1].set_xlabel('Spike Rate BPM (Hz)')
axes[0, 1].set_ylabel('Spike Rate Temp (Hz)')
axes[0, 1].set_title('Espaço de Características LIF\n(Vermelho=Alerta, Azul=Normal)')

# Gráfico 3: Matriz de Confusão — Regressão Logística
im = axes[1, 0].imshow(cm, cmap='Blues', interpolation='nearest')
axes[1, 0].set_xticks([0, 1])
axes[1, 0].set_yticks([0, 1])
axes[1, 0].set_xticklabels(['Normal', 'Alerta'])
axes[1, 0].set_yticklabels(['Normal', 'Alerta'])
axes[1, 0].set_title('Matriz de Confusão — Regressão Logística')
for i in range(2):
    for j in range(2):
        axes[1, 0].text(j, i, str(cm[i, j]), ha='center', va='center', fontsize=14, fontweight='bold')
plt.colorbar(im, ax=axes[1, 0])

# Gráfico 4: Comparação de acurácia
models = ['Regressão\nLogística', 'Rede LIF\nNeuromórfica']
accs = [acc_lr, acc_lif]
bars = axes[1, 1].bar(models, accs, color=['#1E90FF', '#FF4500'], width=0.4)
axes[1, 1].set_ylabel('Acurácia')
axes[1, 1].set_title('Comparação de Acurácia')
axes[1, 1].set_ylim(0, 1)
for bar, acc in zip(bars, accs):
    axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    f'{acc:.1%}', ha='center', fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig("cardioia_lif_vs_lr.png", dpi=150, bbox_inches="tight")
print("   ✅ Gráfico salvo: cardioia_lif_vs_lr.png")

# ============= RELATÓRIO COMPARATIVO =============
print("\n" + "=" * 65)
print("  📋 Relatório comparativo gerado com sucesso!")
print(f"  🧠 Acurácia LIF Neuromórfico: {acc_lif:.1%}")
print(f"  📈 Acurácia Reg. Logística: {acc_lr:.1%}")
print(f"  💡 Conclusão: Ambos modelos detectam eventos cardíacos,")
print(f"     mas a rede LIF oferece eficiência energética para")
print(f"     dispositivos vestíveis com chips neuromórficos.")
print("=" * 65)
