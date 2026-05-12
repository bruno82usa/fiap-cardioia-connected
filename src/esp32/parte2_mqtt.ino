/*
 * CardioIA Conectada - Parte 2: MQTT para Cloud
 * FIAP - 2TIAO - Grupo 15 - Bruno Gambarini RM561517
 * 
 * Este código simula o envio de dados do ESP32 para a nuvem via MQTT.
 * Em produção, substituir a simulação WiFi pelo WiFi.h real.
 * 
 * Tópicos MQTT:
 *   - cardioia/sensores/temperatura  (float)
 *   - cardioia/sensores/umidade       (float)
 *   - cardioia/sensores/bpm            (int)
 *   - cardioia/sensores/status         (string: "online"/"offline")
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// ============= CONFIGURAÇÕES =============
// WiFi - Substituir pelas credenciais reais
const char* WIFI_SSID = "FIAP-IoT";
const char* WIFI_PASSWORD = "FIAP2026";

// MQTT - Broker HiveMQ Cloud
const char* MQTT_SERVER = "broker.hivemq.com";  // Broker público para teste
const int MQTT_PORT = 1883;
const char* MQTT_CLIENT_ID = "ESP32_CardioIA_Grupo15";

// Tópicos MQTT para publicação
const char* TOPIC_TEMP = "cardioia/sensores/temperatura";
const char* TOPIC_HUMID = "cardioia/sensores/umidade";
const char* TOPIC_BPM = "cardioia/sensores/bpm";
const char* TOPIC_STATUS = "cardioia/sensores/status";
const char* TOPIC_ALERTA = "cardioia/alertas";

// ============= HARDWARE =============
#define DHT_PIN 15       // Pino do sensor DHT22
#define DHT_TYPE DHT22   // Tipo do sensor
#define BOTAO_PIN 4      // Pino do botão (simula BPM)

DHT dht(DHT_PIN, DHT_TYPE);

// ============= CLIENTES =============
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// ============= VARIÁVEIS GLOBAIS =============
float temperatura = 0.0;
float umidade = 0.0;
int bpm = 0;
unsigned long ultimoEnvio = 0;
const unsigned long INTERVALO_ENVIO = 2000;  // 2 segundos entre envios
int contadorBatidas = 0;
unsigned long tempoUltimoBPM = 0;
bool wifiConectado = false;

// ============= SETUP =============
void setup() {
  Serial.begin(115200);
  Serial.println("\n====================================");
  Serial.println("  CardioIA Conectada - Fase 3");
  Serial.println("  Sistema MQTT de Monitoramento");
  Serial.println("  Grupo 15 - Bruno Gambarini RM561517");
  Serial.println("====================================\n");

  // Inicializa sensores
  dht.begin();
  pinMode(BOTAO_PIN, INPUT_PULLUP);

  // Tenta conectar ao WiFi
  conectarWiFi();

  // Configura MQTT
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(callbackMQTT);

  Serial.println("[SISTEMA] Monitoramento iniciado - Aguardando dados...");
}

// ============= LOOP PRINCIPAL =============
void loop() {
  // Mantém conexão WiFi viva (simulação)
  if (WiFi.status() != WL_CONNECTED) {
    wifiConectado = false;
    conectarWiFi();
  }

  // Mantém conexão MQTT
  if (!mqttClient.connected()) {
    reconectarMQTT();
  }
  mqttClient.loop();

  // Lê sensores
  lerSensores();
  detectarBatimentos();

  // Envia dados a cada 2 segundos
  if (millis() - ultimoEnvio >= INTERVALO_ENVIO) {
    enviarDadosMQTT();
    ultimoEnvio = millis();
  }
}

// ============= WIFI =============
void conectarWiFi() {
  Serial.print("[WiFi] Conectando a ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int tentativas = 0;
  while (WiFi.status() != WL_CONNECTED && tentativas < 20) {
    delay(500);
    Serial.print(".");
    tentativas++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConectado = true;
    Serial.println("\n[WiFi] Conectado!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConectado = false;
    Serial.println("\n[WiFi] Falha na conexão - Modo Offline");
  }
}

// ============= MQTT =============
void reconectarMQTT() {
  if (!wifiConectado) return;

  Serial.print("[MQTT] Conectando ao broker... ");
  
  if (mqttClient.connect(MQTT_CLIENT_ID)) {
    Serial.println("Conectado!");
    
    // Assina tópicos de comando (se necessário)
    mqttClient.subscribe("cardioia/comandos/#");
    
    // Publica status online
    mqttClient.publish(TOPIC_STATUS, "online");
  } else {
    Serial.print("Falha (rc=");
    Serial.print(mqttClient.state());
    Serial.println(") - Tentando novamente em 5s");
    delay(5000);
  }
}

// Callback de mensagens MQTT recebidas
void callbackMQTT(char* topic, byte* payload, unsigned int length) {
  Serial.print("[MQTT] Mensagem recebida: ");
  Serial.print(topic);
  Serial.print(" -> ");
  
  for (unsigned int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}

// ============= SENSORES =============
void lerSensores() {
  // Lê DHT22 a cada 2 segundos (evita leituras muito frequentes)
  temperatura = dht.readTemperature();
  umidade = dht.readHumidity();

  // Verifica se leitura é válida
  if (isnan(temperatura) || isnan(umidade)) {
    Serial.println("[ERRO] Falha na leitura do DHT22!");
    temperatura = 36.5;  // valor padrão de segurança
    umidade = 60.0;
  }
}

// Detecta batimentos cardíacos simulados via botão
void detectarBatimentos() {
  if (digitalRead(BOTAO_PIN) == LOW) {  // Botão pressionado (pull-up)
    contadorBatidas++;
    delay(50);  // debounce
    
    // Espera soltar o botão
    while (digitalRead(BOTAO_PIN) == LOW) {
      delay(10);
    }
  }

  // Calcula BPM a cada 10 segundos
  if (millis() - tempoUltimoBPM >= 10000) {
    bpm = contadorBatidas * 6;  // multiplica por 6 para projetar minuto
    contadorBatidas = 0;
    tempoUltimoBPM = millis();
  }
}

// ============= ENVIO DE DADOS =============
void enviarDadosMQTT() {
  if (!wifiConectado || !mqttClient.connected()) {
    Serial.println("[MQTT] Offline - Dados armazenados no buffer local");
    return;
  }

  char buffer[10];

  // Envia temperatura
  dtostrf(temperatura, 4, 1, buffer);
  mqttClient.publish(TOPIC_TEMP, buffer);
  Serial.print("[MQTT] Temperatura: ");
  Serial.print(buffer);
  Serial.println("°C");

  // Envia umidade
  dtostrf(umidade, 4, 1, buffer);
  mqttClient.publish(TOPIC_HUMID, buffer);
  Serial.print("[MQTT] Umidade: ");
  Serial.print(buffer);
  Serial.println("%");

  // Envia BPM
  itoa(bpm, buffer, 10);
  mqttClient.publish(TOPIC_BPM, buffer);
  Serial.print("[MQTT] BPM: ");
  Serial.println(bpm);

  // Envia status do sistema
  const char* status = wifiConectado ? "online" : "offline";
  mqttClient.publish(TOPIC_STATUS, status);

  // Verifica e envia alertas
  if (bpm > 120) {
    mqttClient.publish(TOPIC_ALERTA, "ALERTA: BPM elevado!");
    Serial.println("[ALERTA] Batimento cardíaco elevado detectado!");
  }
  if (temperatura > 38.0) {
    mqttClient.publish(TOPIC_ALERTA, "ALERTA: Febre detectada!");
    Serial.println("[ALERTA] Temperatura corporal elevada!");
  }

  Serial.println("---");
}
