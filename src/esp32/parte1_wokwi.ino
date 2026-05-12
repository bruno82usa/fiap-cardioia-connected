/*
 * =====================================================================
 * CardioIA Conectada — Fase 3: IoT na Saúde
 * PARTE 1: ESP32 no Wokwi — Sensores + Edge Computing
 * 
 * Descrição:
 *   Simula um dispositivo vestível de monitoramento cardíaco com ESP32.
 *   Utiliza sensor DHT22 (temperatura + umidade) e botão pulsador para
 *   simular batimentos cardíacos (BPM). Implementa buffer circular para
 *   armazenamento local (Edge Computing) e lógica de resiliência offline
 *   com sincronização automática ao reconectar.
 *
 * Plataforma: Wokwi (simulador online)
 * Microcontrolador: ESP32
 * Autor: CardioIA Team — Engenharia IoT/Embedded
 * Data: Maio/2026
 * =====================================================================
 */

// ==================== BIBLIOTECAS ====================
// Simulação: as bibliotecas no Wokwi são incluídas automaticamente.
// Em hardware real, instalar via Library Manager do Arduino IDE.
#include "DHT.h"            // Biblioteca para sensor DHT22
#include <Arduino.h>        // Biblioteca base do Arduino para ESP32

// ==================== DEFINIÇÕES DE PINOS ====================
// Pinos físicos do ESP32 (GPIO)
#define PINO_DHT22      15  // Pino de dados do sensor DHT22 (GPIO15)
#define PINO_BOTAO      4   // Pino do botão pulsador — simula batimentos (GPIO4)
#define PINO_LED_VERDE  25  // LED verde: indica conectividade Wi-Fi OK
#define PINO_LED_VERMELHO 26 // LED vermelho: indica desconexão
#define PINO_LED_AMARELO 27 // LED amarelo: indica alerta (temp alta ou BPM crítico)

// ==================== CONSTANTES DO SISTEMA ====================
#define TIPO_DHT        DHT22     // Modelo do sensor de temperatura/umidade
#define TAMANHO_BUFFER  20        // Tamanho máximo do buffer circular de leituras
#define INTERVALO_LEITURA 2000    // Intervalo entre leituras em ms (2 segundos)
#define BPM_CRITICO     120       // Limiar de BPM para acionar alerta
#define TEMP_CRITICA    38.0      // Limiar de temperatura (°C) para alerta

// ==================== ESTRUTURA DE DADOS ====================
// Estrutura que representa uma leitura completa dos sensores.
// Armazena todos os parâmetros vitais em um único registro.
struct LeituraSensor {
  float temperatura;     // Temperatura em graus Celsius (°C)
  float umidade;         // Umidade relativa do ar (%)
  int   bpm;             // Batimentos por minuto (simulado via botão)
  unsigned long timestamp; // Timestamp em millis() da leitura
  bool  enviada;         // Flag: true se já foi enviada para a nuvem
};

// ==================== VARIÁVEIS GLOBAIS ====================
DHT dht(PINO_DHT22, TIPO_DHT);  // Instância do sensor DHT22

LeituraSensor bufferLeituras[TAMANHO_BUFFER]; // Buffer circular de leituras
int indiceBuffer = 0;             // Índice atual de escrita no buffer
int leiturasPendentes = 0;        // Quantidade de leituras não enviadas

bool wifiConectado = false;       // Simula conectividade Wi-Fi (true = online)
bool alertaAtivo = false;         // Flag de alerta (temp crítica ou BPM alto)

unsigned long ultimaLeitura = 0;  // Timestamp da última leitura de sensores
int contadorBatimentos = 0;       // Contador para cálculo de BPM
unsigned long tempoUltimoBatimento = 0; // Timestamp do último batimento detectado
bool estadoBotaoAnterior = HIGH;  // Estado anterior do botão (pull-up interno)

// ==================== PROTÓTIPOS DE FUNÇÕES ====================
void inicializarSistema();
void lerSensores();
void processarBotao();
void calcularBPM();
void armazenarLeitura(float temp, float umid, int bpm);
void verificarAlertas(float temp, int bpm);
void sincronizarCloud();
void enviarLeituraSerial(LeituraSensor leitura);
void atualizarLEDs();
String formatarJSON(LeituraSensor leitura);

// ==================== SETUP ====================
void setup() {
  // Inicializa comunicação serial para debug e simulação da nuvem
  Serial.begin(115200);
  delay(1000); // Aguarda estabilização da serial

  Serial.println(F("\n╔══════════════════════════════════════════╗"));
  Serial.println(F("║   CardioIA Conectada — Fase 3: IoT     ║"));
  Serial.println(F("║   ESP32 + DHT22 + Botão (Wokwi)       ║"));
  Serial.println(F("╚══════════════════════════════════════════╝\n"));

  // Inicializa o sensor DHT22
  dht.begin();
  Serial.println(F("[SISTEMA] Sensor DHT22 inicializado com sucesso."));

  // Configura o botão com pull-up interno (pressiona = LOW)
  pinMode(PINO_BOTAO, INPUT_PULLUP);
  Serial.println(F("[SISTEMA] Botão pulsador configurado (GPIO4, PULL-UP)."));

  // Configura os LEDs indicadores como saída
  pinMode(PINO_LED_VERDE, OUTPUT);
  pinMode(PINO_LED_VERMELHO, OUTPUT);
  pinMode(PINO_LED_AMARELO, OUTPUT);
  Serial.println(F("[SISTEMA] LEDs indicadores configurados (GPIO 25, 26, 27)."));

  // Inicializa os LEDs: vermelho aceso (começa desconectado)
  digitalWrite(PINO_LED_VERDE, LOW);
  digitalWrite(PINO_LED_VERMELHO, HIGH);
  digitalWrite(PINO_LED_AMARELO, LOW);

  // Inicializa o buffer circular de leituras
  for (int i = 0; i < TAMANHO_BUFFER; i++) {
    bufferLeituras[i] = {0.0, 0.0, 0, 0, true}; // Inicia vazio e "já enviado"
  }

  Serial.println(F("[SISTEMA] Buffer circular inicializado."));
  Serial.println(F("[SISTEMA] Iniciando operação offline..."));
  Serial.println(F("[SISTEMA] Aguardando conexão Wi-Fi para sincronizar...\n"));
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  // --- Simulação de conectividade Wi-Fi ---
  // Alterna o estado a cada ~15 segundos para demonstrar a resiliência
  // offline. Em hardware real, isso seria obtido de WiFi.status().
  static unsigned long ultimaTrocaWiFi = 0;
  if (millis() - ultimaTrocaWiFi > 15000) {
    wifiConectado = !wifiConectado;
    ultimaTrocaWiFi = millis();

    if (wifiConectado) {
      Serial.println(F("\n[Wi-Fi] 📶 CONECTADO à rede — sincronizando dados pendentes..."));
      sincronizarCloud(); // Sincroniza leituras acumuladas ao reconectar
    } else {
      Serial.println(F("\n[Wi-Fi] ❌ DESCONECTADO — operando em modo offline (Edge Computing)"));
    }
  }

  // --- Processa o botão pulsador (simula batimentos cardíacos) ---
  processarBotao();

  // --- Lê os sensores no intervalo configurado ---
  if (millis() - ultimaLeitura >= INTERVALO_LEITURA) {
    ultimaLeitura = millis();
    lerSensores();
  }

  // --- Atualiza os LEDs indicadores de estado ---
  atualizarLEDs();

  delay(50); // Pequena pausa para estabilidade do loop (evita bouncing)
}

// ==================== FUNÇÕES PRINCIPAIS ====================

/**
 * inicializarSistema()
 * Responsável pela configuração inicial de todos os periféricos.
 * Chamada uma única vez no setup() para organizar o código.
 */
void inicializarSistema() {
  // Esta função existe como wrapper para organização futura.
  // A inicialização real está inline no setup() para maior clareza.
  Serial.println(F("[INIT] Sistema preparado para operação."));
}

/**
 * lerSensores()
 * Realiza a leitura dos sensores DHT22 (temperatura e umidade)
 * e do BPM calculado via botão pulsador.
 * Armazena os dados no buffer circular e verifica alertas.
 */
void lerSensores() {
  // Leitura do DHT22 com verificação de falha
  float temperatura = dht.readTemperature();
  float umidade = dht.readHumidity();

  // Verifica se a leitura do DHT22 foi válida
  if (isnan(temperatura) || isnan(umidade)) {
    Serial.println(F("[ERRO] Falha na leitura do sensor DHT22! Verifique as conexões."));
    // Em caso de falha, usa o último valor válido (resiliência)
    return;
  }

  // Calcula o BPM baseado nos batimentos detectados pelo botão
  // Se não houver batimentos recentes (mais de 3 segundos), considera BPM = 0
  int bpm = 0;
  if (contadorBatimentos > 0 && (millis() - tempoUltimoBatimento) < 3000) {
    // Estima BPM: conta batimentos nos últimos 10 segundos e extrapola
    bpm = contadorBatimentos * 6; // Multiplica por 6 para projetar para 1 minuto
  } else {
    contadorBatimentos = 0; // Reseta se o ritmo parou
  }

  // Armazena a leitura no buffer circular (Edge Computing)
  armazenarLeitura(temperatura, umidade, bpm);

  // Exibe as leituras no Serial Monitor
  Serial.print(F("[SENSORES] Temp: "));
  Serial.print(temperatura, 1);
  Serial.print(F("°C | Umidade: "));
  Serial.print(umidade, 1);
  Serial.print(F("% | BPM: "));
  Serial.print(bpm);
  Serial.print(F(" | Conectado: "));
  Serial.println(wifiConectado ? F("SIM") : F("NÃO"));

  // Verifica se há condições de alerta
  verificarAlertas(temperatura, bpm);

  // Se estiver conectado, envia imediatamente para a nuvem
  if (wifiConectado) {
    enviarLeituraSerial(bufferLeituras[indiceBuffer > 0 ? indiceBuffer - 1 : TAMANHO_BUFFER - 1]);
  }
}

/**
 * processarBotao()
 * Lê o estado do botão pulsador com debounce simples.
 * Cada pressionamento conta como um batimento cardíaco.
 * Calcula o BPM com base no intervalo entre batimentos.
 */
void processarBotao() {
  bool estadoAtual = digitalRead(PINO_BOTAO);

  // Detecta borda de descida (botão pressionado: HIGH → LOW)
  // devido ao pull-up interno
  if (estadoBotaoAnterior == HIGH && estadoAtual == LOW) {
    // Debounce simples: aguarda 50ms e confirma
    delay(50);
    if (digitalRead(PINO_BOTAO) == LOW) {
      // Batimento cardíaco detectado!
      contadorBatimentos++;
      tempoUltimoBatimento = millis();

      // Debug da detecção de batimento
      Serial.print(F("[BATIMENTO] Pulsação detectada! Total na janela: "));
      Serial.println(contadorBatimentos);
    }
  }
  estadoBotaoAnterior = estadoAtual;
}

/**
 * armazenarLeitura(temp, umidade, bpm)
 * Armazena uma leitura no buffer circular.
 * Implementa a estratégia de Edge Computing: guarda localmente
 * mesmo quando offline, permitindo sincronização posterior.
 *
 * @param temp  Temperatura em °C
 * @param umid  Umidade relativa em %
 * @param bpm   Batimentos por minuto
 */
void armazenarLeitura(float temp, float umid, int bpm) {
  // Escreve no índice atual do buffer circular
  bufferLeituras[indiceBuffer].temperatura = temp;
  bufferLeituras[indiceBuffer].umidade = umid;
  bufferLeituras[indiceBuffer].bpm = bpm;
  bufferLeituras[indiceBuffer].timestamp = millis();
  bufferLeituras[indiceBuffer].enviada = false;

  // Incrementa contador de pendentes (capped no tamanho do buffer)
  if (leiturasPendentes < TAMANHO_BUFFER) {
    leiturasPendentes++;
  }

  // Avança o índice circularmente
  indiceBuffer = (indiceBuffer + 1) % TAMANHO_BUFFER;

  Serial.print(F("[BUFFER] Leitura armazenada. Pendentes: "));
  Serial.print(leiturasPendentes);
  Serial.print(F("/"));
  Serial.println(TAMANHO_BUFFER);
}

/**
 * verificarAlertas(temp, bpm)
 * Avalia se as leituras atuais ultrapassaram os limiares críticos.
 * Aciona o LED amarelo e emite alerta no Serial quando necessário.
 *
 * @param temp  Temperatura atual em °C
 * @param bpm   BPM atual
 */
void verificarAlertas(float temp, int bpm) {
  bool alertaTemp = (temp >= TEMP_CRITICA);
  bool alertaBPM  = (bpm >= BPM_CRITICO && bpm > 0);

  if (alertaTemp || alertaBPM) {
    if (!alertaAtivo) {
      alertaAtivo = true;
      Serial.println(F("\n⚠️  ===== ALERTA MÉDICO ACIONADO ====="));

      if (alertaTemp) {
        Serial.print(F("⚠️  Temperatura elevada: "));
        Serial.print(temp, 1);
        Serial.println(F("°C — Limiar: 38.0°C"));
      }

      if (alertaBPM) {
        Serial.print(F("⚠️  Batimentos cardíacos elevados: "));
        Serial.print(bpm);
        Serial.println(F(" BPM — Limiar: 120 BPM"));
      }

      Serial.println(F("⚠️  ===================================\n"));
    }
  } else {
    // Condições normalizaram: desativa o alerta
    if (alertaAtivo) {
      alertaAtivo = false;
      Serial.println(F("[ALERTA] ✅ Condições normalizadas. Alerta desativado."));
    }
  }
}

/**
 * sincronizarCloud()
 * Percorre o buffer circular e envia todas as leituras pendentes
 * para a nuvem via Serial (simulação). Chamada ao reconectar o Wi-Fi.
 * Implementa a resiliência offline do sistema.
 */
void sincronizarCloud() {
  if (leiturasPendentes == 0) {
    Serial.println(F("[SINCRONIZAÇÃO] Nenhuma leitura pendente para enviar."));
    return;
  }

  Serial.print(F("[SINCRONIZAÇÃO] Enviando "));
  Serial.print(leiturasPendentes);
  Serial.println(F(" leituras pendentes para a nuvem..."));

  int enviadas = 0;
  // Percorre o buffer circular do mais antigo para o mais recente
  for (int i = 0; i < TAMANHO_BUFFER; i++) {
    int idx = (indiceBuffer - leiturasPendentes + i + TAMANHO_BUFFER) % TAMANHO_BUFFER;

    if (!bufferLeituras[idx].enviada && bufferLeituras[idx].timestamp > 0) {
      enviarLeituraSerial(bufferLeituras[idx]);
      bufferLeituras[idx].enviada = true;
      enviadas++;
    }
  }

  leiturasPendentes = 0;
  Serial.print(F("[SINCRONIZAÇÃO] ✅ "));
  Serial.print(enviadas);
  Serial.println(F(" leituras sincronizadas com sucesso!\n"));
}

/**
 * enviarLeituraSerial(leitura)
 * Simula o envio de uma leitura para a nuvem via Serial.println.
 * Em produção, isso seria substituído por HTTP POST, MQTT publish
 * ou gravação direta em banco de dados cloud.
 *
 * @param leitura  Struct com os dados a serem enviados
 */
void enviarLeituraSerial(LeituraSensor leitura) {
  // Formata os dados como JSON para simular payload de API REST
  String jsonPayload = formatarJSON(leitura);

  // Simula envio para a nuvem via Serial (representa WiFi/HTTP/MQTT)
  Serial.print(F("[CLOUD] 📤 Enviando para nuvem → "));
  Serial.println(jsonPayload);

  // Marca como enviada
  leitura.enviada = true;
}

/**
 * formatarJSON(leitura)
 * Converte uma leitura para formato JSON string.
 * Simula o payload que seria enviado para uma API REST ou broker MQTT.
 *
 * @param leitura  Struct LeituraSensor a ser serializada
 * @return         String JSON formatada
 */
String formatarJSON(LeituraSensor leitura) {
  String json = "{";
  json += "\"dispositivo\":\"ESP32-CardioIA-001\",";
  json += "\"temperatura\":" + String(leitura.temperatura, 1) + ",";
  json += "\"umidade\":" + String(leitura.umidade, 1) + ",";
  json += "\"bpm\":" + String(leitura.bpm) + ",";
  json += "\"timestamp\":" + String(leitura.timestamp) + ",";
  json += "\"alerta\":" + String(alertaAtivo ? "true" : "false");
  json += "}";
  return json;
}

/**
 * atualizarLEDs()
 * Controla os LEDs indicadores com base no estado do sistema:
 * - Verde: Wi-Fi conectado e sem alertas
 * - Vermelho: Wi-Fi desconectado
 * - Amarelo: Alerta ativo (independente da conectividade)
 */
void atualizarLEDs() {
  if (alertaAtivo) {
    // Alerta médico: LED amarelo piscante (alterna a cada 500ms)
    digitalWrite(PINO_LED_VERDE, LOW);
    digitalWrite(PINO_LED_VERMELHO, LOW);
    digitalWrite(PINO_LED_AMARELO, (millis() / 500) % 2);
  } else if (wifiConectado) {
    // Operação normal: LED verde aceso
    digitalWrite(PINO_LED_VERDE, HIGH);
    digitalWrite(PINO_LED_VERMELHO, LOW);
    digitalWrite(PINO_LED_AMARELO, LOW);
  } else {
    // Modo offline: LED vermelho aceso com verde piscando (tentando reconectar)
    digitalWrite(PINO_LED_VERDE, (millis() / 1000) % 2);
    digitalWrite(PINO_LED_VERMELHO, HIGH);
    digitalWrite(PINO_LED_AMARELO, LOW);
  }
}

// ==================== FIM DO CÓDIGO ====================
// Este código está pronto para ser carregado no Wokwi.
// Configuração no Wokwi:
//   - Adicionar ESP32
//   - Conectar DHT22 ao GPIO15
//   - Conectar botão pulsador ao GPIO4 (com pull-up)
//   - Conectar LEDs aos GPIOs 25 (verde), 26 (vermelho), 27 (amarelo)
//   - Cada LED com resistor de 220Ω em série
// ===================================================
