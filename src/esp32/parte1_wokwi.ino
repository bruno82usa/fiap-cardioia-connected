/*
 * CardioIA Conectada — Fase 3: IoT na Saúde
 * PARTE 1: ESP32 + Sensores + Edge Computing
 * Wokwi Simulator
 * 
 * Grupo 15 — Bruno Gambarini RM561517 — FIAP 2026
 * 
 * Circuito:
 *   DHT22 DATA → GPIO 15
 *   Botão     → GPIO 4
 *   LED Verde → GPIO 25 (via 220Ω)
 *   LED Verm  → GPIO 26 (via 220Ω)
 *   LED Amar  → GPIO 27 (via 220Ω)
 */

#include <DHT.h>

// === PINOS ===
#define DHTPIN   15
#define BTNPIN   4
#define LEDG     25
#define LEDR     26
#define LEDY     27

// === CONSTANTES ===
#define DHTTYPE           DHT22
#define BUFFER_SIZE       20
#define INTERVAL_MS       2000
#define BPM_LIMIAR        120
#define TEMP_LIMIAR       38.0
#define INTERVALO_WIFI_MS 15000

DHT dht(DHTPIN, DHTTYPE);

// === BUFFER CIRCULAR (Edge Computing) ===
float buf_temp[BUFFER_SIZE];
float buf_umid[BUFFER_SIZE];
int   buf_bpm[BUFFER_SIZE];
int   buf_idx = 0;
int   buf_pendentes = 0;

bool wifi_ok = false;
bool alerta  = false;
unsigned long ult_leitura;
unsigned long ult_wifi;
int conta_clicks;
unsigned long ultimo_click;
bool btn_anterior = HIGH;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("====================================");
  Serial.println(" CardioIA Conectada — Grupo 15");
  Serial.println(" ESP32 + DHT22 + Botao + LEDs");
  Serial.println("====================================");
  
  dht.begin();
  pinMode(BTNPIN, INPUT_PULLUP);
  pinMode(LEDG, OUTPUT);
  pinMode(LEDR, OUTPUT);
  pinMode(LEDY, OUTPUT);
  
  digitalWrite(LEDG, LOW);
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDY, LOW);
  
  Serial.println("Setup concluido. Iniciando loop...");
}

void loop() {
  // WiFi toggle simulado
  if (millis() - ult_wifi > INTERVALO_WIFI_MS) {
    ult_wifi = millis();
    wifi_ok = !wifi_ok;
    if (wifi_ok) {
      Serial.println("\n[WiFi] CONECTADO — sincronizando...");
      if (buf_pendentes > 0) {
        Serial.print("[SYNC] Enviando "); Serial.print(buf_pendentes);
        Serial.println(" leituras pendentes:");
        for (int i = 0; i < buf_pendentes; i++) {
          int old = (buf_idx - buf_pendentes + i + BUFFER_SIZE) % BUFFER_SIZE;
          Serial.print("  -> #"); Serial.print(i+1); Serial.print(": ");
          Serial.print(buf_temp[old],1); Serial.print("C ");
          Serial.print(buf_umid[old],1); Serial.print("% ");
          Serial.print(buf_bpm[old]); Serial.println("bpm");
        }
        buf_pendentes = 0;
        Serial.println("[SYNC] Sincronizacao concluida!");
      } else {
        Serial.println("[SYNC] Nada pendente.");
      }
    } else {
      Serial.println("\n[WiFi] DESCONECTADO — modo offline (Edge)");
    }
  }

  // Botão (simula batimento)
  int btn_now = digitalRead(BTNPIN);
  if (btn_anterior == HIGH && btn_now == LOW) {
    delay(30);
    if (digitalRead(BTNPIN) == LOW) {
      conta_clicks++;
      ultimo_click = millis();
      Serial.print("[CLICK] #"); Serial.println(conta_clicks);
    }
  }
  btn_anterior = btn_now;

  // Leitura dos sensores (2 seg)
  if (millis() - ult_leitura >= INTERVAL_MS) {
    ult_leitura = millis();

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int   b = 0;

    // DHT22 pode falhar nas primeiras leituras
    if (isnan(t) || isnan(h)) {
      Serial.println("[DHT] Aguardando estabilizacao do sensor...");
      t = 36.5; h = 60.0;
    }

    // BPM: estima dos ultimos clicks
    if (conta_clicks > 0 && millis() - ultimo_click < 10000) {
      b = conta_clicks * 6;
    } else {
      conta_clicks = 0;
    }

    // Armazena no buffer
    buf_temp[buf_idx] = t;
    buf_umid[buf_idx] = h;
    buf_bpm[buf_idx]  = b;
    buf_idx = (buf_idx + 1) % BUFFER_SIZE;
    if (buf_pendentes < BUFFER_SIZE) buf_pendentes++;

    // Serial
    Serial.print("[DADOS] T:"); Serial.print(t,1); Serial.print("C ");
    Serial.print("H:"); Serial.print(h,1); Serial.print("% ");
    Serial.print("BPM:"); Serial.print(b);
    Serial.print(" WiFi:"); Serial.print(wifi_ok ? "ON" : "OFF");
    Serial.print(" Buffer:"); Serial.print(buf_pendentes);
    Serial.print("/"); Serial.println(BUFFER_SIZE);

    // Alerta
    bool novo_alerta = (t >= TEMP_LIMIAR || (b >= BPM_LIMIAR && b > 0));
    if (novo_alerta && !alerta) {
      Serial.print("!!! ALERTA: ");
      if (t >= TEMP_LIMIAR) { Serial.print("Febre "); Serial.print(t,1); Serial.print("C "); }
      if (b >= BPM_LIMIAR)  { Serial.print("Taquicardia "); Serial.print(b); Serial.print("bpm"); }
      Serial.println();
      alerta = true;
    } else if (!novo_alerta && alerta) {
      Serial.println("--- Alerta normalizado ---");
      alerta = false;
    }
  }

  // LEDs
  if (alerta) {
    digitalWrite(LEDG, LOW);
    digitalWrite(LEDR, LOW);
    digitalWrite(LEDY, (millis()/300)%2);
  } else if (wifi_ok) {
    digitalWrite(LEDG, HIGH);
    digitalWrite(LEDR, LOW);
    digitalWrite(LEDY, LOW);
  } else {
    digitalWrite(LEDG, (millis()/800)%2);
    digitalWrite(LEDR, HIGH);
    digitalWrite(LEDY, LOW);
  }

  delay(10);
}
