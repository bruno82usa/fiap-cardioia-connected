# Projeto Wokwi — CardioIA Conectada (ESP32)

## Link do Projeto Wokwi

https://wokwi.com/projects/new/esp32

> Carregue o arquivo `../esp32/parte1_wokwi.ino` no Wokwi para simular.

## Componentes

| Componente | Pino ESP32 | Função |
|-----------|:----------:|--------|
| DHT22 | GPIO 15 | Temperatura + Umidade |
| Botão Pulsador | GPIO 4 (GND) | Simular BPM |
| LED Verde | GPIO 2 | Conectado (WiFi) |
| LED Vermelho | GPIO 0 | Desconectado |
| LED Amarelo | GPIO 5 | Alerta (>38°C ou >120 BPM) |

## Como testar

1. Acesse https://wokwi.com/projects/new/esp32
2. Copie o código de `esp32/parte1_wokwi.ino` 
3. Adicione os componentes conforme tabela acima
4. Execute a simulação
5. Observe o Monitor Serial para ver as leituras

## Diagrama de Conexões (Wokwi)

```
ESP32
├── GPIO 15 → DHT22 (Data)
├── GPIO 4  → Botão → GND
├── GPIO 2  → LED Verde (220Ω) → GND
├── GPIO 0  → LED Vermelho (220Ω) → GND
└── GPIO 5  → LED Amarelo (220Ω) → GND
```
