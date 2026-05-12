# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# CardioIA Conectada — IoT e Visualização de Dados para a Saúde Digital

## Grupo 15 — CardioIA

## 👨‍🎓 Integrantes: 
- <a href="https://www.linkedin.com/">Bruno Gambarini (RM561517)</a>

## 👩‍🏫 Professores:
### Tutor(a) 
- <a href="https://www.linkedin.com/">Prof. Renato Nogueira</a>
### Coordenador(a)
- <a href="https://www.linkedin.com/">Prof. André Godoi</a>

## 📜 Descrição

O projeto CardioIA Conectada desenvolve um sistema de monitoramento cardíaco inteligente utilizando tecnologias de IoT, Edge Computing e Inteligência Artificial. A solução integra um ESP32 com sensores (DHT22 para temperatura/umidade e botão pulsador simulando batimentos cardíacos) que capturam sinais vitais em tempo real. 

O sistema implementa Edge Computing com buffer circular no ESP32, garantindo resiliência offline — os dados continuam sendo coletados mesmo sem conexão à internet, sendo automaticamente sincronizados quando a conectividade é restabelecida. A transmissão para a nuvem utiliza o protocolo MQTT através do broker HiveMQ Cloud.

Os dados são visualizados em dashboards interativos no Node-RED, com gráficos de séries temporais, medidores gauge e sistema de alertas automáticos. Como diferenciação (Ir Além), o projeto inclui uma REST API em Python com SQLite para armazenamento dos dados, sistema de notificação por e-mail e análise preditiva com modelos de Machine Learning (ARIMA e Isolation Forest) para detecção de anomalias e previsão de tendências nos sinais vitais.

A arquitetura reflete o fluxo completo: captura → processamento Edge → transmissão MQTT → visualização Cloud → análise preditiva com IA, demonstrando a aplicação prática de IoT médico com responsabilidade no uso dos dados.

## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- <b>.github</b>: Arquivos de configuração específicos do GitHub para automação.

- <b>assets</b>: Elementos não-estruturados do repositório, como imagens e logotipos.

- <b>config</b>: Arquivos de configuração para parâmetros do projeto (MQTT, API, WiFi).

- <b>document</b>: Todos os documentos do projeto: relatórios, diagramas e documentação técnica.

- <b>scripts</b>: Scripts auxiliares para deploy, backup e automação.

- <b>src</b>: Todo o código fonte desenvolvido:
  - `src/esp32/`: Código embarcado para ESP32 (C++/Arduino)
  - `src/dashboard/`: Fluxos do Node-RED
  - `src/python/`: REST API, análise preditiva e alertas (Python)

- <b>README.md</b>: Arquivo que serve como guia e explicação geral sobre o projeto.

## 🔧 Como executar o código

### Pré-requisitos
- Wokwi (simulador online) ou ESP32 físico
- Node-RED (local ou cloud)
- Python 3.10+
- Conta HiveMQ Cloud (gratuita)

### Parte 1 — ESP32 + Sensores no Wokwi
```bash
# 1. Acesse https://wokwi.com/projects/new/esp32
# 2. Carregue o código: src/esp32/parte1_wokwi.ino
# 3. Adicione os componentes conforme document/parte1_esquema.md
# 4. Execute a simulação
```

### Parte 2 — MQTT + Node-RED Dashboard
```bash
# 1. Configure credenciais no HiveMQ Cloud
# 2. Importe src/dashboard/node-red-flow.json no Node-RED
# 3. Configure o ESP32: src/esp32/parte2_mqtt.ino
```

### Ir Além — Python REST + IA
```bash
cd src/python
pip install -r requirements.txt
python api_server.py          # API na porta 5000
python email_alerts.py        # Sistema de alertas
python dados_sinteticos.py    # Gerar dataset sintético
python ai_predicao.py         # Análise preditiva
```

## 🗃 Histórico de lançamentos

* 1.0.0 - 12/05/2026
    * Fase 3: IoT na Saúde — Monitoramento Contínuo
    * ESP32 + sensores + Edge Computing
    * MQTT + Node-RED Dashboard
    * API REST + Alertas e-mail
    * IA preditiva (ARIMA + Isolation Forest)

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/bruno82usa/fiap-cardioia-connected">CardioIA Conectada</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
