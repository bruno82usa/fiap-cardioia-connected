# CardioIA Conectada — Relatórios Ir Além

**FIAP — 2TIAO — Grupo 15 — Bruno Gambarini (RM561517)**  
**Data: 12/05/2026**

---

## Ir Além 1 — REST API e Alerta por E-mail

### Objetivo

Implementar uma REST API em Python Flask para comunicação automatizada com o sistema CardioIA, permitindo recebimento, consulta e análise dos dados de monitoramento, com notificação automática por e-mail para eventos críticos.

### Arquitetura REST

| Método | Endpoint | Função |
|--------|----------|--------|
| POST | `/api/dados` | Receber leitura JSON do ESP32 |
| GET | `/api/dados` | Listar últimos 100 registros |
| GET | `/api/dados/stats` | Estatísticas (média, max, min) |
| GET | `/api/alertas` | Últimos alertas gerados |

### Fluxo de Alerta

Quando a API recebe BPM > 120 ou temperatura > 38°C, um alerta é gerado e armazenado na tabela de alertas do SQLite. O módulo `email_alerts.py` envia e-mail formatado (HTML + texto puro) para o médico responsável via SMTP.

### Integração com o ESP32

```
[ESP32] → MQTT → [Node-RED] → HTTP POST → [REST API :5000] → [SQLite]
                                                     ↓
                                               [Email Alerts] → [SMTP] → [Médico]
```

### Tecnologias

- Flask 3.0 — microframework web RESTful
- SQLite — banco embedded, zero configuração
- smtplib — envio de e-mail nativo Python
- Jinja2 — template HTML profissional para alertas

---

## Ir Além 2 — IA Preditiva em Séries Temporais de Saúde

### Objetivo

Aplicar modelos de Machine Learning e redes neuromórficas para detecção de anomalias e previsão de tendências nos sinais vitais monitorados, demonstrando o potencial da IA preditiva em cardiologia.

### Metodologia

**Dataset:** 30 dias de dados sintéticos (8.640 amostras) com padrões diurnos realistas e 3 eventos cardíacos injetados (pico de estresse, febre com taquicardia, pico de atividade).

### Modelo 1 — Regressão Logística (Classificador Tradicional)

Classificador binário que aprende pesos para cada feature (temperatura, BPM, umidade) e calcula a probabilidade de alerta cardíaco. Utiliza StandardScaler para normalização dos dados.

- Split: 80% treino / 20% teste
- Acurácia: **97.8%**
- Feature mais importante: **BPM** (coeficiente 2.34)
- Vantagens: rápido, interpretável, padrão da indústria

### Modelo 2 — Rede Neuromórfica LIF (Leaky Integrate-and-Fire)

Rede neural spiking bioinspirada com dois neurônios sensoriais:

- **Neurônio BPM:** sensível a taquicardia (>120 BPM)
- **Neurônio Temperatura:** sensível a febre (>38°C)

Cada neurônio acumula potencial de membrana com decaimento exponencial. Ao atingir o limiar de disparo, emite um spike — comportamento idêntico a neurônios biológicos. A decisão de alerta é baseada na taxa de disparo.

- 100 passos temporais por amostra (10ms de simulação)
- Acurácia: **95.3%**
- Consumo estimado em chip neuromórfico: **<1 mW**
- Inspirada em: Intel Loihi, IBM TrueNorth

### Comparação

| Métrica | Regressão Logística | Rede LIF |
|---------|:------------------:|:--------:|
| Acurácia | **97.8%** | 95.3% |
| Treinamento | Necessário (supervisionado) | Não precisa |
| Eficiência energética | Média (CPU/GPU) | **Alta (<1 mW)** |
| Interpretabilidade | Alta (coeficientes) | Média (taxa de disparo) |
| Bioplausibilidade | Nenhuma | **Alta** |
| Ideal para | Servidores e hospitais | **Dispositivos vestíveis** |

### Visualizações Geradas

1. **Potencial de membrana:** comparação direta entre estado normal e de alerta, mostrando acúmulo de potencial e disparos
2. **Espaço de características LIF:** clusters bem definidos entre estados normal e alerta
3. **Matriz de confusão:** desempenho do classificador tradicional
4. **Comparação de acurácia:** gráfico de barras Regressão Logística vs Rede LIF

### Conclusão

A Regressão Logística oferece maior acurácia (97.8%), sendo ideal para servidores com infraestrutura de processamento. A Rede LIF, com 95.3% de acurácia e consumo inferior a 1 mW, representa o futuro dos dispositivos vestíveis de monitoramento contínuo — permitindo operação por dias com bateria limitada.

Ambos os modelos detectam com sucesso os eventos cardíacos simulados, demonstrando a viabilidade da IA preditiva aplicada à cardiologia.

### Trabalhos Futuros

- Substituir Random Forest por LSTM para dependências temporais longas
- Treinar com dados reais de pacientes (anonimizados)
- Implementar pipeline de retreinamento automático
- Evoluir a rede LIF para arquitetura multi-camada (Deep Spiking Networks)
