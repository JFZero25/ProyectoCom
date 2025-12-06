#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>

// ============== CONFIGURACIÓN ==============

const char* WIFI_SSID = "WIFI-DCI";
const char* WIFI_PASSWORD = "DComInf_2K24";
const char* SERVER_IP = "172.27.231.250 ";
const int RASPBERRY_PORT = 5000;

const int SENSOR_ADDRESS = 0x68;

// Tiempo entre fotos si sigue habiendo movimiento
const unsigned long INTERVALO_FOTO = 10000;

// ============== VARIABLES ==============
unsigned long ultimaFoto = 0;
long magnitudAnterior = 0;

// ============== FUNCIONES ==============

void conectarWiFi() {
  Serial.print("Conectando a WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConectado! IP:");
  Serial.println(WiFi.localIP());
}

void iniciarSensor() {
  // Sacar del modo sleep
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(0x6B);  // Registro PWR_MGMT_1
  Wire.write(0x00);  // Wake up
  Wire.endTransmission();

  delay(50);

  // Configurar acelerómetro ±2g
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(0x1C);  // ACCEL_CONFIG
  Wire.write(0x00);  // ±2g
  Wire.endTransmission();
}

bool detectarMovimiento() {
  Wire.beginTransmission(SENSOR_ADDRESS);
  Wire.write(0x3B);   // ACCEL_XOUT_H (registro correcto)
  Wire.endTransmission(false);

  Wire.requestFrom(SENSOR_ADDRESS, 6);

  if (Wire.available() == 6) {

    int16_t x = (Wire.read() << 8) | Wire.read();
    int16_t y = (Wire.read() << 8) | Wire.read();
    int16_t z = (Wire.read() << 8) | Wire.read();

    long magnitud = abs(x) + abs(y) + abs(z);

    // Detectar un cambio brusco → movimiento
    if (abs(magnitud - magnitudAnterior) > 1500) {
      magnitudAnterior = magnitud;
      Serial.println("MOVIMIENTO DETECTADO!");
      return true;
    }

    magnitudAnterior = magnitud;
  }

  return false;
}

void tomarFoto() {
  if (WiFi.status() != WL_CONNECTED)
    conectarWiFi();

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + RASPBERRY_PORT + "/disparar";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  Serial.println("Notificando a Raspberry...");

  int code = http.POST("{}");
  Serial.print("Respuesta: ");
  Serial.println(code);

  http.end();
}

// ============== SETUP ==============

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(500);

  Serial.println("Iniciando sensor...");
  iniciarSensor();
  Serial.println("Sensor iniciado.");

  // Confirmar que el sensor responde
  Wire.beginTransmission(SENSOR_ADDRESS);
  if (Wire.endTransmission() != 0) {
    Serial.println("ERROR: Sensor RAK12006 no detectado.");
    while (1) {}
  }

  conectarWiFi();
  Serial.println("Sistema listo.");
}

// ============== LOOP ==============

void loop() {
  unsigned long ahora = millis();

  if (detectarMovimiento()) {
    if (ahora - ultimaFoto >= INTERVALO_FOTO) {
      Serial.println("Movimiento detectado → tomando foto.");
      tomarFoto();
      ultimaFoto = ahora;
    }
  }

  delay(50);
}