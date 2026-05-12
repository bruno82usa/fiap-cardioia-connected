# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href="https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP" border="0" width="40%" height="40%"></a>
</p>

<br>

# CardioIA Conectada — IoT e Visualização de Dados para a Saúde Digital

### Grupo 15 — CardioIA

## 👨‍🎓 Integrantes

- Bruno Gambarini (RM561517)

## 👩‍🏫 Professores

| Papel | Nome |
|-------|------|
| Tutor(a) | Prof. Renato Nogueira |
| Coordenador(a) | Prof. André Godoi |

---

## 📜 Descrição

O projeto CardioIA Conectada desenvolve um sistema de monitoramento cardíaco inteligente utilizando IoT, Edge Computing e Inteligência Artificial.

A solução integra um **ESP32** com sensores DHT22 (temperatura/umidade) e botão pulsador (batimentos cardíacos) que capturam sinais vitais em tempo real. O sistema implementa **Edge Computing** com buffer circular para resiliência offline — os dados continuam sendo coletados mesmo sem conexão, sendo automaticamente sincronizados quando a conectividade é restabelecida.

A transmissão para a nuvem utiliza o protocolo **MQTT** através do broker HiveMQ Cloud. Os dados são visualizados em **dashboards interativos no Node-RED**, com gráficos de séries temporais, medidores gauge e sistema de alertas automáticos.

Como diferenciação, o projeto inclui:

- **REST API** em Python Flask com SQLite
- **Sistema de alertas** por e-mail automático
- **Machine Learning** para detecção de anomalias (Isolation Forest) e previsão de BPM (Random Forest)
- **Rede Neuromórfica LIF** (Leaky Integrate-and-Fire) comparada ao classificador tradicional

## 📁 Estrutura de pastas

| Pasta | Conteúdo |
|-------|----------|
| `.github` | Configurações do GitHub |
| `assets` | Imagens e logotipos |
| `config` | Arquivos de configuração (MQTT, API, WiFi) |
| `document` | Relatórios, diagramas e documentação técnica |
| `scripts` | Scripts auxiliares (deploy, automação) |
| `src/esp32` | Código embarcado ESP32 (C++/Arduino) |
| `src/dashboard` | Fluxos do Node-RED |
| `src/python` | REST API, análise preditiva e alertas (Python) |

## 🔧 Como executar

### Pré-requisitos

- Wokwi (simulador online) ou ESP32 físico
- Node-RED (local ou cloud)
- Python 3.10+
- Conta HiveMQ Cloud (gratuita)

### Parte 1 — ESP32 no Wokwi

1. Acesse https://wokwi.com/projects/new/esp32
2. Carregue `src/esp32/parte1_wokwi.ino`
3. Monte o circuito conforme `document/wokwi_setup/setup.md`
4. Execute a simulação

### Parte 2 — MQTT + Node-RED

1. Configure credenciais no HiveMQ Cloud
2. Importe `src/dashboard/node-red-flow.json` no Node-RED
3. Carregue `src/esp32/parte2_mqtt.ino` no ESP32

### Ir Além — Python

```bash
cd src/python
pip install -r requirements.txt
python api_server.py       # API na porta 5000
python email_alerts.py     # Sistema de alertas
python dados_sinteticos.py # Dataset sintético
python ai_predicao.py      # ML tradicional
python lif_neuromorphic.py # Rede LIF neuromórfica
```

## 🗃 Histórico de lançamentos

- **1.0.0** — 12/05/2026
  - Fase 3: IoT na Saúde — Monitoramento Contínuo
  - ESP32 + sensores + Edge Computing
  - MQTT + Node-RED Dashboard com alertas
  - API REST + alertas por e-mail
  - IA preditiva (Isolation Forest + Random Forest)
  - Rede neuromórfica LIF (comparação)

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1">

[CardioIA Conectada](https://github.com/bruno82usa/fiap-cardioia-connected) está licenciado sob [Attribution 4.0 International](http://creativecommons.org/licenses/by/4.0/).
