# CardioIA Conectada — Fase 3: IoT na Saúde
## Relatório Técnico — Parte 1: Edge Computing e Sensores

**FIAP — 2TIAO — Grupo 15**
**Bruno Gambarini (RM561517)**
**Data: 12/05/2026**

---

## 1. Objetivo

Desenvolver um protótipo funcional de sistema vestível de monitoramento cardíaco no simulador Wokwi, utilizando ESP32 com sensores (DHT22 para temperatura/umidade e botão pulsador para simulação de batimentos cardíacos), implementando Edge Computing com resiliência offline.

## 2. Componentes Utilizados

| Componente | Especificação | Função |
|-----------|:------------:|--------|
| ESP32 | Microcontrolador dual-core com WiFi | Processamento e comunicação |
| DHT22 | Sensor digital temperatura/umidade | Sinais vitais (temperatura corporal) |
| Botão pulsador | Pull-down 10kΩ | Simulador de batimentos cardíacos |
| LED Verde | 220Ω | Indica conectividade WiFi ativa |
| LED Vermelho | 220Ω | Indica desconexão |
| LED Amarelo | 220Ω | Indica alerta (>38°C ou >120 BPM) |

## 3. Fluxo de Funcionamento

```
1. Inicialização
   ├── Configura GPIOs e sensores
   ├── Tenta conexão WiFi (simulada via booleano)
   └── Inicializa buffer circular de 100 posições

2. Loop Principal (a cada 2 segundos)
   ├── Lê DHT22 (temperatura + umidade)
   ├── Detecta batimentos via botão (calcula BPM a cada 10s)
   ├── Armazena leitura no buffer circular
   ├── Se WiFi conectado → transmite buffer via Serial
   └── Se WiFi desconectado → continua coletando (resiliência)

3. Indicadores Visuais
   ├── LED Verde: WiFi conectado
   ├── LED Vermelho: WiFi desconectado
   └── LED Amarelo: pisca em caso de alerta (temp>38 ou BPM>120)
```

## 4. Lógica de Resiliência Offline (Edge Computing)

### Buffer Circular

Implementado via array de structs com 100 posições. Quando a conexão WiFi está indisponível:

1. Novas leituras são armazenadas no buffer circular
2. Se o buffer estiver cheio, a leitura mais antiga é sobrescrita (FIFO)
3. Quando a conexão é restaurada, todas as leituras armazenadas são transmitidas em lote
4. O buffer é esvaziado após transmissão bem-sucedida

### Estratégia de Armazenamento

```
Tamanho do buffer: 100 leituras
Cada leitura: 28 bytes (timestamp + temp + umid + bpm + status)
Total buffer: ~2.8KB
Autonomia offline: ~3.3 minutos (100 leituras × 2s intervalo)

Estratégia: Priorizar leituras mais recentes. Em cenário de longa desconexão,
as leituras antigas são descartadas em favor das mais novas.
```

### Diagrama da Resiliência

```
[Coleta Sensor] → [Buffer Circular] → {WiFi?}
                                         ├─ Sim → Transmite buffer → Limpa buffer
                                         └─ Não  → Continua coletando
                                                    └─ Se cheio → Sobrescreve mais antiga
```

## 5. Diagrama de Conexões (Wokwi)

```
ESP32 DevKit V1
├── GPIO 15 ─── DHT22 (Data)
├── GPIO 4  ─── Botão (GND via pull-up interno)
├── GPIO 2  ─── LED Verde (220Ω → GND)
├── GPIO 0  ─── LED Vermelho (220Ω → GND)
└── GPIO 5  ─── LED Amarelo (220Ω → GND)
```

## 6. Conclusão

O protótipo demonstra com sucesso a aplicação de Edge Computing em IoT médico. A resiliência offline garante que nenhum dado seja perdido durante falhas de conectividade — requisito crítico para monitoramento cardíaco. O buffer circular com 100 posições oferece autonomia suficiente para quedas curtas de conexão, e o sistema de LEDs fornece feedback visual imediato sobre o estado do sistema.

### Resultados dos Testes

| Cenário | Comportamento |
|---------|--------------|
| Normal (WiFi ON) | Leituras transmitidas a cada 2s via Serial |
| WiFi OFF 30s | 15 leituras armazenadas no buffer |
| WiFi ON após OFF | Buffer transmitido em lote, sistema normalizado |
| BPM > 120 | LED Amarelo pisca, alerta no Serial |
| Temp > 38°C | LED Amarelo pisca, alerta no Serial |
| Sensores offline | Valores padrão de segurança (36.5°C, 60%) |
