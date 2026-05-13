# Projeto Wokwi — CardioIA Conectada

> Montagem passo-a-passo para o simulador Wokwi

## 🚀 Passo a Passo (2 minutos)

### 1. Criar projeto
Acesse https://wokwi.com/projects/new/esp32

### 2. Substituir diagram.json
- Clique na aba `diagram.json`
- Apague todo o conteúdo (Ctrl+A → Delete)
- Cole o conteúdo de [`src/esp32/diagram.json`](src/esp32/diagram.json)

### 3. Substituir sketch.ino
- Clique na aba `sketch.ino`
- Apague todo o conteúdo
- Cole o conteúdo de [`src/esp32/parte1_wokwi.ino`](src/esp32/parte1_wokwi.ino)

### 4. Executar
- Clique no ▶ **Play** (botão verde no canto inferior esquerdo)
- O Monitor Serial mostrará as leituras
- Pressione o botão do circuito para simular batimentos

## 📋 Componentes

| Quantidade | Componente | Localização no diagrama |
|:----------:|-----------|------------------------|
| 1 | ESP32 DevKit V4 | Centro |
| 1 | DHT22 | Acima do ESP32 |
| 1 | Botão Pulsador (vermelho) | Abaixo do ESP32 |
| 1 | LED Verde | À esquerda, superior |
| 1 | LED Vermelho | À esquerda, meio |
| 1 | LED Amarelo | À esquerda, inferior |
| 3 | Resistor 220Ω | Entre LEDs e ESP32 |

## 🔌 Conexões

| GPIO | Componente | Cor do fio |
|:----:|------------|:----------:|
| 3.3V | DHT22 VCC | 🔴 Vermelho |
| GND | DHT22 GND | ⚫ Preto |
| 15 | DHT22 Data | 🟢 Verde |
| 4 | Botão (pino 2) | 🔵 Azul |
| GND | Botão (pino 1) | ⚫ Preto |
| 2 | LED Verde (via 220Ω) | 🟢 Verde |
| 0 | LED Vermelho (via 220Ω) | 🔴 Vermelho |
| 5 | LED Amarelo (via 220Ω) | 🟡 Amarelo |

## 🔗 Link direto

**https://wokwi.com/projects/463861297023651841**
