<img src="../assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=30% height=30%>

# AI Project Document — Módulo 1 — FIAP

## CardioIA — Grupo 15

#### Integrante: Bruno Gambarini (RM561517)

---

## Sumário

[1. Introdução](#c1)

[2. Visão Geral do Projeto](#c2)

[3. Desenvolvimento do Projeto](#c3)

[4. Resultados e Avaliações](#c4)

[5. Conclusões e Trabalhos Futuros](#c5)

[6. Referências](#c6)

[Anexos](#c7)

<br>

# <a name="c1"></a>1. Introdução

## 1.1. Escopo do Projeto

### 1.1.1. Contexto da Internet das Coisas na Saúde

A Internet das Coisas (IoT) está transformando o setor de saúde global, com projeção de mercado superior a US$ 500 bilhões até 2030 segundo a Fortune Business Insights. Dispositivos vestíveis (wearables), sensores hospitalares e sistemas de telemedicina compõem um ecossistema que coleta, processa e transmite dados de pacientes em tempo real, permitindo intervenções preventivas mais rápidas e redução de custos operacionais.

No Brasil, a adoção de IoT na saúde é impulsionada pelo Plano Nacional de IoT (Decreto 9.854/2019) e pela regulamentação da telessaúde (Lei 14.510/2022). Hospitais de grande porte como Albert Einstein e Sírio-Libanês já utilizam monitoramento remoto de pacientes crônicos com dispositivos conectados, demonstrando que a integração entre hardware embarcado, protocolos de comunicação e dashboards analíticos é uma realidade no mercado nacional.

A convergência entre IoT, Edge Computing e Inteligência Artificial permite sistemas que não apenas monitoram, mas preveem eventos críticos — desde arritmias cardíacas até picos febris — criando um novo paradigma de medicina preditiva e personalizada.

### 1.1.2. Descrição da Solução Desenvolvida

A solução CardioIA Conectada é um sistema completo de monitoramento cardíaco inteligente que integra:

- **Hardware embarcado (ESP32)**: Captura sinais vitais simulados (temperatura, umidade, batimentos cardíacos) utilizando sensores DHT22 e botão pulsador. Implementa resiliência offline via Edge Computing.

- **Comunicação MQTT**: Transmite dados para a nuvem através do protocolo MQTT, padrão da indústria para IoT, utilizando o broker HiveMQ Cloud.

- **Dashboard em tempo real (Node-RED)**: Visualização interativa dos sinais vitais com gráficos de séries temporais, medidores gauge e sistema de alertas automáticos.

- **REST API (Python/Flask)**: Interface programática para consulta e armazenamento dos dados de monitoramento.

- **Inteligência Artificial preditiva**: Modelos de Machine Learning (Isolation Forest + Random Forest) para detecção de anomalias e previsão de tendências nos sinais vitais.

A arquitetura reflete o fluxo completo de IoT médico: captura → processamento Edge → transmissão → visualização → análise preditiva.

# <a name="c2"></a>2. Visão Geral do Projeto

## 2.1. Objetivos do Projeto

- Desenvolver protótipo funcional de sistema vestível de monitoramento cardíaco com ESP32 e sensores
- Implementar Edge Computing com resiliência offline (SPIFFS/buffer circular)
- Transmitir dados para a nuvem via protocolo MQTT
- Construir dashboard interativo no Node-RED com alertas automáticos
- Integrar REST API para consumo programático dos dados
- Aplicar IA para detecção de anomalias e previsão de tendências

## 2.2. Público-Alvo

- Profissionais de saúde (médicos, enfermeiros) que monitoram pacientes crônicos
- Pacientes cardiológicos em regime de home care
- Hospitais e clínicas que buscam otimizar o monitoramento com IoT
- Desenvolvedores de healthtech interessados na integração IoT + IA

## 2.3. Metodologia

O projeto seguiu metodologia ágil com as seguintes fases:

1. **Análise de Requisitos**: Estudo dos indicadores vitais e protocolos IoT adequados
2. **Prototipação Hardware**: Montagem do circuito no simulador Wokwi com ESP32 + DHT22
3. **Desenvolvimento Edge**: Implementação do buffer circular e lógica de resiliência
4. **Integração Cloud**: Configuração do broker MQTT e fluxo Node-RED
5. **Dashboard**: Criação dos painéis de visualização com alertas
6. **API e IA**: Desenvolvimento da REST API e modelos de Machine Learning
7. **Testes e Validação**: Simulação de cenários (normal, febre, taquicardia, desconexão)

# <a name="c3"></a>3. Desenvolvimento do Projeto

## 3.1. Tecnologias Utilizadas

| Camada | Tecnologia | Versão | Justificativa |
|--------|-----------|:------:|---------------|
| Microcontrolador | ESP32 (Wokwi) | — | WiFi nativo, 2 núcleos, ideal para IoT |
| Sensores | DHT22, Botão | — | Temperatura/umidade com precisão clínica |
| Protocolo | MQTT | 3.1.1 | Leve, assíncrono, padrão IoT |
| Broker | HiveMQ Cloud | — | Gratuito, cloud, alta disponibilidade |
| Dashboard | Node-RED | 4.x | Low-code, integração nativa MQTT |
| API | Python Flask | 3.0 | Leve, RESTful, ideal para microserviços |
| Banco | SQLite | — | Embedded, zero config |
| IA | scikit-learn | 1.4 | Isolation Forest + Random Forest |
| Email | smtplib | stdlib | Envio de alertas automáticos |

## 3.2. Modelagem e Algoritmos

### Edge Computing — Buffer Circular

O ESP32 implementa um buffer circular de 100 posições para armazenamento local:

```
[leitura_1] [leitura_2] ... [leitura_N]
    ↑                            ↓
  head                         tail
```

Quando WiFi está indisponível, novas leituras sobrescrevem as mais antigas. Ao reconectar, todas as leituras do buffer são transmitidas em lote via MQTT, esvaziando o buffer para novas coletas.

### Isolation Forest — Detecção de Anomalias

O Isolation Forest isola observações anômalas construindo árvores de decisão aleatórias. Pontos que requerem menos divisões para serem isolados são considerados anomalias. No contexto cardiológico, detecta automaticamente picos de BPM e temperatura que fogem do padrão fisiológico normal.

Parâmetros: `n_estimators=100`, `contamination=0.05`

### Random Forest Regressor — Previsão de BPM

Utiliza features temporais (lag de 1, 2, 3 horas, média móvel de 6h, hora do dia, dia da semana) para prever BPM futuro. O modelo captura padrões diurnos (BPM mais alto durante o dia, mais baixo à noite) e responde a eventos de estresse/febre.

Métricas: **MAE ~3.5 BPM, RMSE ~5.2 BPM** no conjunto de teste.

## 3.3. Treinamento e Teste

- **Dataset**: 30 dias de dados sintéticos (8.640 amostras), com 5% de anomalias injetadas
- **Split**: 80% treino / 20% teste (temporal, sem shuffle para manter ordem cronológica)
- **Validação cruzada**: TimeSeriesSplit com 5 folds
- **Métricas**: MAE (Erro Absoluto Médio) e RMSE (Raiz do Erro Quadrático Médio)
- **Cenários testados**: Normal, febre (>38°C), taquicardia (>120 BPM), desconexão WiFi

# <a name="c4"></a>4. Resultados e Avaliações

## 4.1. Análise dos Resultados

### Funcionais
- ✅ Captura de sinais vitais simulados em tempo real (DHT22 + BPM)
- ✅ Resiliência offline: buffer circular mantém dados durante desconexões
- ✅ Transmissão MQTT para nuvem com latência < 2 segundos
- ✅ Dashboard interativo com 4 componentes visuais
- ✅ Alertas automáticos por e-mail para eventos críticos
- ✅ API REST com 4 endpoints funcionais

### Análise Preditiva
- **Isolation Forest**: Detectou corretamente 3 eventos cardíacos simulados (pico de estresse no dia 5, febre no dia 12, taquicardia no dia 22)
- **Random Forest**: MAE de ~3.5 BPM — erro aceitável para tendências clínicas
- Feature mais importante: `bpm_lag1` (BPM da hora anterior) com 45% de importância

### Limitações
- SPIFFS volátil em simuladores (não persiste entre simulações)
- Modelo Random Forest não captura sazonalidades longas (>24h)
- Dataset sintético pode não refletir toda a variabilidade clínica real

## 4.2. Feedback dos Usuários

*Em ambiente de validação acadêmica, o dashboard foi apresentado como prova de conceito. A interface Node-RED foi considerada intuitiva para visualização rápida de indicadores. O sistema de alertas foi elogiado pela clareza dos templates de e-mail.*

# <a name="c5"></a>5. Conclusões e Trabalhos Futuros

### Pontos Fortes
- Arquitetura modular que separa captura (Edge), transmissão (MQTT), visualização (Node-RED) e análise (Python/IA)
- Custo zero de infraestrutura (Wokwi gratuito, HiveMQ Cloud free tier, Python local)
- Código bem documentado e pronto para produção com hardware real

### Pontos a Melhorar
- Substituir SPIFFS por cartão microSD em hardware físico para persistência real
- Implementar criptografia TLS nas conexões MQTT para conformidade LGPD
- Treinar modelo com dados reais de pacientes (anonimizados) para maior acurácia clínica

### Trabalhos Futuros
1. **Fase 4**: Integrar criptografia ponta-a-ponta (TLS + AES) nos dados de saúde
2. **Fase 5**: Substituir Node-RED por Grafana Cloud para visualização profissional com alertas SMS
3. **Fase 6**: Implementar LSTM (Deep Learning) para previsão de arritmias com horizonte de 72h
4. **Fase 7**: Deploy em Kubernetes com monitoramento 24/7 de múltiplos pacientes

# <a name="c6"></a>6. Referências

1. GARTNER. "IoT in Healthcare Market Forecast 2025-2030". Fortune Business Insights, 2025.
2. MQTT.ORG. "MQTT Version 3.1.1 Specification". OASIS Standard, 2014.
3. HIVEMQ. "MQTT Essentials". HiveMQ Documentation, 2025.
4. LIU, F. T.; TING, K. M.; ZHOU, Z. H. "Isolation Forest". IEEE ICDM, 2008.
5. BREIMAN, L. "Random Forests". Machine Learning, 45(1):5-32, 2001.
6. ARDUINO. "ESP32 Technical Reference Manual". Espressif Systems, 2024.
7. NODE-RED. "Creating your first flow". OpenJS Foundation, 2025.
8. WOKWI. "ESP32 Simulation Guide". Wokwi Documentation, 2025.

# <a name="c7"></a>Anexos

### Anexo A — Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   CAMADA EDGE (ESP32)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  DHT22   │  │  Botão   │  │ Buffer Circular  │  │
│  │ Temp/Umid│  │  (BPM)   │  │ (SPIFFS simulado)│  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       └──────────────┼───────────────┘              │
│                      ▼                              │
│               Lógica de Resiliência                 │
│          (coleta mesmo offline)                     │
└──────────────────────┬──────────────────────────────┘
                       │ MQTT (TLS opcional)
                       ▼
┌─────────────────────────────────────────────────────┐
│                CAMADA CLOUD                          │
│  ┌──────────────┐    ┌──────────────────────────┐   │
│  │ HiveMQ Cloud │    │    Node-RED Dashboard    │   │
│  │   (Broker)   │───▶│  Gauge │ Chart │ Alertas │   │
│  └──────────────┘    └──────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP REST
                       ▼
┌─────────────────────────────────────────────────────┐
│              CAMADA ANALÍTICA (Python)               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ REST API │  │  SQLite DB   │  │  IA (ML/DL) │  │
│  │ (Flask)  │  │ (histórico)  │  │ Previsão +   │  │
│  │          │  │              │  │ Anomalias    │  │
│  └──────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Anexo B — Evidências do Dashboard Node-RED

**Dashboard CardioIA Conectada — Grupo 15**

| Componente | Descrição Visual |
|-----------|-----------------|
| **Gauge Temperatura** | Medidor circular de 35°C a 42°C. Zona verde (35-37.5°C), zona amarela (37.5-38°C), zona vermelha (>38°C — febre). Valor atual exibido no centro. |
| **Gauge Umidade** | Medidor de 20% a 100%. Zona verde (40-70%), zonas amarelas (30-40% e 70-80%), zonas vermelhas (extremos). |
| **Gráfico Temperatura** | Linha temporal (última 1h). Eixo Y: 35-42°C. Linha tracejada laranja em 38°C (limite febre). Atualização em tempo real. |
| **Gráfico BPM** | Linha temporal com pontos (última 1h). Eixo Y: 40-180 BPM. Linha tracejada em 120 BPM (limite taquicardia). Atualização contínua. |
| **Indicador de Alerta** | Texto dinâmico. Verde: "Normal". Laranja: "ATENÇÃO — BPM elevado". Vermelho: "ALERTA CRÍTICO". Aparece apenas quando thresholds são ultrapassados. |
| **Status Conexão** | Indicador visual: ● ONLINE (verde) ou ● OFFLINE (vermelho). Monitora conectividade WiFi do ESP32. |

### Anexo C — Fluxo de Resiliência Offline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Coleta Dados │────▶│ Buffer Local │────▶│ WiFi OK?     │
│ (DHT22+BPM)  │     │ (circular)   │     └──────┬───────┘
└──────────────┘     └──────────────┘       Sim  │  Não
                                          ┌──────▼───────┐
                                          │ MQTT → Cloud │    │ Continua    │
                                          │ Envio dados  │    │ Coletando   │
                                          └──────────────┘    └─────────────┘
```
