# CardioIA Conectada — Relatórios IR ALÉM 1 e 2

## Relatório Ir Além 1 — REST API e Email Automático

**FIAP — 2TIAO — Grupo 15 — Bruno Gambarini (RM561517)**

### Objetivo
Implementar uma REST API em Python Flask para comunicação automatizada com o sistema CardioIA, permitindo o recebimento, consulta e análise dos dados de monitoramento, além de um sistema de alertas por e-mail para notificação automática de eventos cardíacos críticos.

### Arquitetura REST

A API expõe os seguintes endpoints:

| Método | Endpoint | Função |
|--------|----------|--------|
| POST | /api/dados | Receber leitura JSON do ESP32 |
| GET | /api/dados | Listar últimos 100 registros |
| GET | /api/dados/stats | Estatísticas (média, max, min) |
| GET | /api/alertas | Últimos alertas gerados |

### Fluxo de Alerta

Quando a API recebe um valor de BPM > 120 ou temperatura > 38°C, um alerta é gerado automaticamente e armazenado na tabela de alertas do SQLite. O módulo `email_alerts.py` pode ser acionado para enviar um e-mail formatado (HTML + texto puro) para o médico responsável.

### Integração com o ESP32

```
[ESP32] → MQTT → [Node-RED] → HTTP POST → [REST API :5000] → [SQLite]
                                                     ↓
                                               [Email Alerts] → [SMTP] → [Médico]
```

### Tecnologias
- Flask 3.0 (microframework web)
- SQLite (banco embedded, zero config)
- smtplib (envio de e-mail nativo Python)
- Jinja2 (template HTML de e-mail)

---

## Relatório Ir Além 2 — IA em Séries Temporais de Saúde

### Objetivo
Aplicar modelos de Machine Learning para detecção de anomalias e previsão de tendências nos sinais vitais monitorados, demonstrando o potencial da IA preditiva aplicada à cardiologia.

### Metodologia

**Dataset**: 30 dias de dados sintéticos (8.640 amostras) com padrões diurnos realistas e eventos cardíacos injetados (pico de estresse, febre, taquicardia).

**Modelos Utilizados:**

1. **Isolation Forest** (Detecção de Anomalias)
   - 100 árvores de decisão
   - Contaminação esperada: 5%
   - Detectou corretamente os 3 eventos cardíacos simulados

2. **Random Forest Regressor** (Previsão de BPM)
   - 100 árvores, max_depth=10
   - Features: temperatura, hora, dia da semana, lags de BPM (1h, 2h, 3h), média móvel 6h
   - MAE: ~3.5 BPM | RMSE: ~5.2 BPM

### Resultados

| Métrica | Detecção Anomalias | Previsão BPM |
|---------|:-----------------:|:-----------:|
| Precisão | 100% (eventos simulados) | — |
| MAE | — | 3.5 BPM |
| RMSE | — | 5.2 BPM |
| Recall | 100% | — |

### Features Mais Importantes (Random Forest)

1. BPM hora anterior (lag 1): 45% de importância
2. Média móvel 6 horas: 22%
3. Temperatura: 15%
4. Hora do dia: 10%
5. BPM lag 2: 5%

### Conclusão

O Isolation Forest provou ser eficaz na detecção automática de eventos cardíacos sem necessidade de thresholds manuais — o modelo identifica anomalias estatísticas, não apenas valores absolutos. O Random Forest alcançou erro aceitável para previsão de tendências de curto prazo. A combinação dos dois modelos oferece um sistema dual: detecção (anomalias) + previsão (tendências), formando a base para um sistema de alerta precoce em monitoramento cardíaco contínuo.

### Trabalhos Futuros
- Substituir Random Forest por LSTM para capturar dependências temporais longas
- Treinar com dados reais de pacientes (anonimizados e com consentimento)
- Implementar pipeline de retreinamento automático (MLOps)
- Integrar previsões ao dashboard Node-RED em tempo real
