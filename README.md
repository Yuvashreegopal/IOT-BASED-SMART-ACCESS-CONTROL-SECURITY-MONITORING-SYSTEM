# IOT-BASED-SMART-ACCESS-CONTROL-SECURITY-MONITORING-SYSTEM

An IoT-based smart access control system that combines **RFID authentication**, **Face Recognition**, **Role-based Access Control**, **Time-based Authorization**, **Replay Attack Prevention**, and a **Web Dashboard** for real-time monitoring.

This project is designed for secure access management in colleges, labs, offices, and restricted areas.

---

## Features

* RFID card authentication using MFRC522
* Face recognition using OpenCV (LBPH model)
* Dual-factor authentication (RFID + Face)
* Role-based access control
* Time-based access rules
* Replay attack prevention / request rate limiting
* Live web dashboard
* Access logs storage in MySQL
* Security alerts page
* ESP32 Wi-Fi connectivity
* Real-time grant / deny response

---

## Technologies Used

| Category         | Technology            |
| ---------------- | --------------------- |
| Microcontroller  | ESP32                 |
| RFID Module      | MFRC522               |
| Backend          | Python Flask          |
| Face Recognition | OpenCV + LBPH         |
| Database         | MySQL                 |
| Frontend         | HTML, CSS, JavaScript |
| Communication    | HTTP API              |
| IDE              | VS Code / Arduino IDE |

---

# Hardware Connections

## ESP32 to RFID RC522 Wiring

| RFID RC522 Pin | ESP32 Pin |
| -------------- | --------- |
| SDA (SS)       | GPIO 5    |
| SCK            | GPIO 18   |
| MOSI           | GPIO 23   |
| MISO           | GPIO 19   |
| RST            | GPIO 22   |
| GND            | GND       |
| 3.3V           | 3.3V      |

---

## Optional Output Devices

| Device            | ESP32 Pin |
| ----------------- | --------- |
| Buzzer            | GPIO 2    |
| Green LED         | GPIO 4    |
| Red LED           | GPIO 15   |
| Relay / Door Lock | GPIO 16   |

---

# Software Architecture

```text
RFID Card Scan
      ↓
ESP32 Reads UID
      ↓
Send UID to Flask Server
      ↓
Check User in MySQL
      ↓
Time Access Validation
      ↓
Face Recognition Trigger
      ↓
Grant / Deny Access
      ↓
Update Dashboard + Logs
```

---

# Project Folder Structure

```text
iot_access_control_backend/
│── app.py
│── templates/
│   ├── dashboard.html
│   ├── alerts.html
│   └── logs.html
│── static/
│── dataset/
│── trainer/
│── esp32_code/
│── requirements.txt
│── README.md
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/rfid-security-control.git
cd rfid-security-control
```

---

## 2. Install Python Packages

```bash
pip install -r requirements.txt
```

---

## 3. Install Required Libraries

```bash
pip install flask opencv-python mysql-connector-python numpy
```

---

## 4. Configure MySQL Database

Create database:

```sql
CREATE DATABASE iot_access_control;
```

Import required tables:

* users
* access_logs
* alerts

---

## 5. Run Flask Server

```bash
python app.py
```

---

## 6. Upload ESP32 Code

Use Arduino IDE and upload `.ino` file.

Update WiFi and server IP:

```cpp
const char* ssid = "YourWiFi";
const char* password = "YourPassword";
String server = "http://YOUR_PC_IP:5000/api/access-request";
```

---

# Default Access Rules

| User      | Role           | Access Time |
| --------- | -------------- | ----------- |
| Sachin    | Student        | 9 AM – 2 PM |
| Yuvashree | Student        | 2 PM – 8 PM |
| Admin     | Admin          | Anytime     |
| Lab Staff | Lab Technician | Anytime     |

---

# Security Features

| Feature             | Description                    |
| ------------------- | ------------------------------ |
| Face Authentication | Prevents stolen RFID usage     |
| Replay Protection   | Blocks repeated rapid requests |
| Role Access         | Restricts based on user role   |
| Time Access         | Shift-wise control             |
| Logging             | Every attempt stored           |

---

# API Endpoints

| Endpoint            | Method | Purpose             |
| ------------------- | ------ | ------------------- |
| /api/access-request | POST   | RFID authentication |
| /api/door-status    | GET    | Live door status    |
| /dashboard          | GET    | Web dashboard       |
| /alerts             | GET    | Security alerts     |
| /logs               | GET    | Access logs         |

---

# Example Output

## Access Granted

```json
{
 "access":"granted",
 "user":"Sachin"
}
```

## Access Denied

```json
{
 "access":"denied",
 "reason":"outside_allowed_time"
}
```

---

# Future Enhancements

* Mobile app control
* Cloud dashboard
* OTP verification
* CCTV integration
* Fingerprint module
* Email/SMS alerts

---

# Authors

* Sachin
* Team Members

---

# License

This project is for academic and educational purposes.

---

# Final Note

If you like this project, give it a ⭐ on GitHub.
