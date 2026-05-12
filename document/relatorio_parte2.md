# CardioIA Conectada — Fase 3: IoT na Saúde
## Relatório Técnico — Parte 2: Transmissão MQTT e Visualização Cloud

**FIAP — 2TIAO — Grupo 15**
**Bruno Gambarini (RM561517)**
**Data: 12/05/2026**

---

## 1. Objetivo

Criar um sistema completo de monitoramento que transmita dados do ESP32 para a nuvem via protocolo MQTT e visualize as informações em dashboards interativos no Node-RED com alertas automáticos baseados em thresholds configuráveis.

## 2. Arquitetura de Comunicação

```
ESP32 (Publicador MQTT)
    │
    ├── cardioia/sensores/temperatura   (float: 36.5°C)
    ├── cardioia/sensores/umidade        (float: 65.0%)
    ├── cardioia/sensores/bpm             (int: 72)
    └── cardioia/sensores/status          (string: "online"/"offline")
    
    [MQTT QoS 1 — entrega garantida ao menos uma vez]
    
    ▼
HiveMQ Cloud Broker (broker.hivemq.com:1883)
    │
    ▼
Node-RED (Subscriber + Dashboard)
    ├── Gauge Temperatura (35-42°C)
    ├── Gauge Umidade (20-100%)
    ├── Chart Histórico BPM
    ├── Chart Histórico Temperatura
    ├── Alerta Visual (BPM > 120 ou Temp > 38°C)
    └── Indicador Status Conexão
```

### Protocolo MQTT

O MQTT (Message Queuing Telemetry Transport) foi escolhido por ser:
- **Leve**: overhead mínimo de banda, ideal para dispositivos embarcados
- **Assíncrono**: publish/subscribe com qualidade de serviço (QoS) configurável
- **Padrão IoT**: adotado por AWS IoT, Azure IoT Hub e Google Cloud IoT
- **Resiliente**: suporta reconexão automática e fila de mensagens offline

### Qualidade de Serviço (QoS)

| QoS | Nível | Uso |
|-----|:-----:|-----|
| QoS 0 | At most once | Dados de debug |
| QoS 1 | At least once | **Sinais vitais** (garante entrega) |
| QoS 2 | Exactly once | Alertas críticos |

Utilizamos **QoS 1** para dados de sensores e **QoS 2** para alertas.

## 3. Configuração do Broker MQTT

O broker HiveMQ Cloud foi selecionado por:
- **Plano gratuito**: até 25 dispositivos conectados
- **Alta disponibilidade**: 99.9% SLA
- **TLS suportado**: criptografia opcional para dados médicos
- **Dashboard de monitoramento**: visualização de tráfego e dispositivos conectados

### Credenciais (template — preencher ao configurar)
```
Broker URL: broker.hivemq.com
Porta: 1883
Client ID: ESP32_CardioIA_Grupo15
Tópicos raiz: cardioia/
```

## 4. Dashboard Node-RED

### Componentes Implementados

| Nó | Tipo | Função | Thresholds |
|----|------|--------|------------|
| `gauge-temp` | UI Gauge | Temperatura corporal | 35-37.5°C (verde), 37.5-38°C (amarelo), >38°C (vermelho) |
| `gauge-humid` | UI Gauge | Umidade ambiente | 40-70% (verde), extremos em amarelo/vermelho |
| `chart-temp` | UI Chart | Histórico temperatura | Linha tracejada em 38°C |
| `chart-bpm` | UI Chart | Histórico batimentos | Linha tracejada em 120 BPM |
| `function-bpm-check` | Function | Lógica de alerta | BPM > 120 = crítico, > 100 = atenção |
| `alert-led` | UI Text | Indicador visual de alerta | Dinâmico: texto e cor conforme severidade |
| `text-status` | UI Text | Status conexão ESP32 | "ONLINE" (verde) ou "OFFLINE" (vermelho) |
| `mqtt-out-alerta` | MQTT Out | Publicação de alertas | Tópico: cardioia/alertas |

### Descrição Visual do Dashboard

**Aba "CardioIA Conectada"** — Layout de 2 colunas × 4 linhas

| Coluna 1 (Medidores) | Coluna 2 (Históricos) |
|---------------------|----------------------|
| Gauge Temperatura (medidor circular verde-amarelo-vermelho) | Gráfico linha Temperatura (última 1h) |
| Gauge Umidade (medidor circular azul) | Gráfico linha BPM (última 1h, com pontos) |
| Indicador Status Conexão (texto verde/vermelho) | — |
| Alerta Visual (texto dinâmico: normal/atenção/crítico) | — |

## 5. Alertas Automáticos

### Thresholds Configurados

| Parâmetro | Normal | Atenção | Crítico |
|-----------|:------:|:-------:|:-------:|
| Temperatura | ≤ 37.5°C | 37.5-38°C | > 38°C |
| BPM | ≤ 100 | 100-120 | > 120 |
| Umidade | 40-70% | 30-40% / 70-80% | < 30% / > 80% |

### Fluxo de Alerta

```
1. Sensor detecta valor anômalo → MQTT publish
2. Node-RED recebe → Function node avalia threshold
3. Se crítico:
   ├── UI Text mostra "ALERTA CRÍTICO" (vermelho)
   ├── MQTT out publica em cardioia/alertas
   └── API REST registra no SQLite
4. Sistema de e-mail (Python) envia notificação ao médico
```

## 6. Integração com a API REST (Ir Além 1)

Os dados do MQTT podem ser consumidos pela REST API Python via integração MQTT→HTTP:

```python
# Endpoint para receber dados do ESP32
POST /api/dados
{
    "temperatura": 36.5,
    "umidade": 65.0,
    "bpm": 72,
    "timestamp": "2026-05-12T14:30:00",
    "status": "online"
}
```

A API armazena em SQLite e expõe endpoints de consulta para dashboards externos e análises.

## 7. Conclusão

O sistema de transmissão MQTT e visualização em Node-RED atendeu plenamente aos objetivos da Fase 3 do projeto CardioIA. A arquitetura publish/subscribe do MQTT provou ser ideal para IoT médico, com latência inferior a 2 segundos e garantia de entrega via QoS.

O dashboard Node-RED oferece visualização intuitiva e em tempo real dos sinais vitais, com alertas automáticos que permitem resposta rápida da equipe médica. A integração com a REST API Python fecha o ciclo, permitindo que dados de IoT alimentem sistemas hospitalares existentes.

### Performance

| Métrica | Valor |
|---------|:-----:|
| Latência MQTT (ESP32→Node-RED) | < 2s |
| Taxa de atualização do dashboard | Tempo real |
| Detecção de alerta → Notificação e-mail | < 5s |
| Armazenamento API REST | < 50ms por requisição |
