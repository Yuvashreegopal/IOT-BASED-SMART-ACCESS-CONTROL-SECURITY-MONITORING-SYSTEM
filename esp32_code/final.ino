#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP32Servo.h>

// ---------------- WIFI ----------------
const char* ssid = "MyWiFi";
const char* password = "12345678";

const char* serverName = "http://10.107.194.112:5000/api/access-request";

// ---------------- RFID ----------------
#define SS_PIN  5
#define RST_PIN 22
MFRC522 mfrc522(SS_PIN, RST_PIN);

// ---------------- OUTPUT DEVICES ----------------
#define GREEN_LED   2
#define RED_LED     4
#define BUZZER_PIN  25
#define SERVO_PIN   13

Servo doorServo;

// ---------------- SECURITY ----------------
int failCount = 0;
const int MAX_FAILS = 3;

// 🔥 ATTACK MODE (for demo)
bool ATTACK_MODE = false;   // change to true to simulate DoS

// -------------------------------------------------
// 🔊 BUZZER
// -------------------------------------------------
void beepSuccess() {
  tone(BUZZER_PIN, 2000);
  delay(300);
  noTone(BUZZER_PIN);
}

void beepDenied() {
  for (int i = 0; i < 2; i++) {
    tone(BUZZER_PIN, 1500);
    delay(200);
    noTone(BUZZER_PIN);
    delay(150);
  }
}

void beepAlarm() {
  Serial.println("🚨 SECURITY ALERT: 3 FAILED ATTEMPTS!");

  for (int i = 0; i < 5; i++) {
    tone(BUZZER_PIN, 3000);
    delay(150);
    tone(BUZZER_PIN, 1000);
    delay(150);
  }

  noTone(BUZZER_PIN);
}

// -------------------------------------------------
// ✅ ACCESS GRANTED
// -------------------------------------------------
void accessGranted() {
  Serial.println("✅ ACCESS GRANTED");

  failCount = 0;

  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, LOW);

  beepSuccess();

  doorServo.write(90);
  Serial.println("🚪 Door Unlocked");

  delay(3000);

  doorServo.write(0);
  Serial.println("🔒 Door Locked");

  digitalWrite(GREEN_LED, LOW);
}

// -------------------------------------------------
// ❌ ACCESS DENIED
// -------------------------------------------------
void accessDenied() {
  Serial.println("❌ ACCESS DENIED");

  failCount++;

  digitalWrite(RED_LED, HIGH);
  digitalWrite(GREEN_LED, LOW);

  if (failCount >= MAX_FAILS) {
    beepAlarm();
    failCount = 0;
  } else {
    beepDenied();
  }

  digitalWrite(RED_LED, LOW);
}

// -------------------------------------------------
// 🌐 SEND UID TO SERVER
// -------------------------------------------------
bool sendUIDtoServer(String uid) {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi Disconnected!");
    return false;
  }

  HTTPClient http;

  http.begin(serverName);
  http.setTimeout(8000);
  http.setReuse(false);
  http.addHeader("Content-Type", "application/json");

  String jsonData = "{\"uid\":\"" + uid + "\"}";

  Serial.println("📡 Sending UID → Server");
  Serial.println("Payload: " + jsonData);

  int httpResponseCode = http.POST(jsonData);

  Serial.print("HTTP Response Code: ");
  Serial.println(httpResponseCode);

  // 🔥 HANDLE RATE LIMIT (IMPORTANT)
  if (httpResponseCode == 429) {
    Serial.println("🚫 BLOCKED BY SERVER (DoS Protection)");
    http.end();
    return false;
  }

  if (httpResponseCode > 0) {
    String response = http.getString();

    Serial.println("✅ Server Response:");
    Serial.println(response);

    http.end();

    if (response.indexOf("granted") >= 0) {
      return true;
    } else {
      return false;
    }
  }
  else {
    Serial.print("❌ HTTP Error: ");
    Serial.println(httpResponseCode);

    http.end();
    return false;
  }
}

// -------------------------------------------------
// SETUP
// -------------------------------------------------
void setup() {

  Serial.begin(115200);
  delay(1000);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);

  doorServo.attach(SERVO_PIN);
  doorServo.write(0);

  // WIFI
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ WiFi Connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // RFID
  SPI.begin();
  mfrc522.PCD_Init();

  Serial.println("📡 RFID Ready → Scan Card");
}

// -------------------------------------------------
// LOOP
// -------------------------------------------------
void loop() {

  // 🔥 ATTACK SIMULATION MODE
  if (ATTACK_MODE) {
    Serial.println("⚠️ ATTACK MODE ACTIVE");

    for (int i = 0; i < 15; i++) {
      sendUIDtoServer("B4 1E 9E A9");  // use valid UID
      delay(200);
    }

    delay(5000); // wait before next attack
    return;
  }

  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  String readUID = "";

  Serial.print("Scanned UID:");

  for (byte i = 0; i < mfrc522.uid.size; i++) {
    byte b = mfrc522.uid.uidByte[i];

    Serial.print(" ");
    Serial.print(b, HEX);

    if (b < 0x10) readUID += "0";
    readUID += String(b, HEX);

    if (i != mfrc522.uid.size - 1)
      readUID += " ";
  }

  readUID.toUpperCase();

  Serial.println();
  Serial.println("Formatted UID: " + readUID);

  delay(100);

  bool granted = sendUIDtoServer(readUID);

  if (granted) {
    accessGranted();
  } else {
    accessDenied();
  }

  mfrc522.PICC_HaltA();
  delay(1500);
}
