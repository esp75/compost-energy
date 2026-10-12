// Compost Energy prototype logger - ESP32
//
// STATUS: written against the libraries' documented APIs but NOT YET FLASHED
// OR BENCH-TESTED. Expect to adjust pins and probe addresses on first build.
//
// Logs every 2 minutes to SD card, in exactly the CSV format that
// model/scripts/analyze_run.py reads:
//   timestamp,t_core_c,t_mid_c,t_ambient_c,t_water_in_c,t_water_out_c,flow_l_min,rh_pct
//
// Also runs the water-loop pump with the same thermostat logic as the
// simulation: pump on during the day window only if core > inlet + margin.
//
// Libraries: OneWire, DallasTemperature, RTClib (DS3231), SD (built in),
//            Adafruit SHT31 (headspace humidity).

#include <OneWire.h>
#include <DallasTemperature.h>
#include <RTClib.h>
#include <SD.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>

// ---- pins (see wiring.md) ------------------------------------------------
constexpr uint8_t PIN_ONEWIRE = 4;    // all five DS18B20 on one bus, 4.7k pull-up
constexpr uint8_t PIN_FLOW = 27;      // YF-S401 hall sensor, open collector
constexpr uint8_t PIN_PUMP = 26;      // relay / MOSFET driving 12 V pump
constexpr uint8_t PIN_SD_CS = 5;      // SD card on VSPI (18 SCK, 19 MISO, 23 MOSI)

// ---- settings ------------------------------------------------------------
constexpr uint32_t LOG_INTERVAL_MS = 120000;
constexpr float PULSES_PER_LITRE = 5880.0f;   // YF-S401 datasheet; calibrate with a jug
constexpr uint8_t PUMP_ON_HOUR = 9;
constexpr uint8_t PUMP_OFF_HOUR = 17;
constexpr float ENABLE_MARGIN_C = 8.0f;
constexpr char LOG_PATH[] = "/raw_run.csv";

// Probe ROM addresses: run the DallasTemperature "Multiple" example once,
// label each probe, and paste its address here.
DeviceAddress PROBE_CORE = {0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
DeviceAddress PROBE_MID = {0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01};
DeviceAddress PROBE_AMBIENT = {0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02};
DeviceAddress PROBE_WATER_IN = {0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03};
DeviceAddress PROBE_WATER_OUT = {0x28, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04};

OneWire oneWire(PIN_ONEWIRE);
DallasTemperature probes(&oneWire);
RTC_DS3231 rtc;
Adafruit_SHT31 sht31;

volatile uint32_t flowPulses = 0;
uint32_t lastLogMs = 0;
uint32_t lastFlowMs = 0;
bool pumpOn = false;

void IRAM_ATTR onFlowPulse() { flowPulses++; }

// Raw readings are logged as-is, including DS18B20 error codes (-127, 85):
// cleaning happens offline so nothing is silently lost on the device.
float readC(DeviceAddress addr) { return probes.getTempC(addr); }

void setPump(bool on) {
  pumpOn = on;
  digitalWrite(PIN_PUMP, on ? HIGH : LOW);
}

void updatePump(const DateTime& now, float tCore, float tIn) {
  bool inWindow = now.hour() >= PUMP_ON_HOUR && now.hour() < PUMP_OFF_HOUR;
  bool sensorsOk = tCore > -100 && tCore < 84 && tIn > -100 && tIn < 84;
  // Without valid temperatures keep the pump off rather than guess.
  setPump(inWindow && sensorsOk && tCore > tIn + ENABLE_MARGIN_C);
}

void writeHeaderIfNew() {
  if (SD.exists(LOG_PATH)) return;
  File f = SD.open(LOG_PATH, FILE_WRITE);
  if (!f) return;
  f.println("# MEASURED DATA - Compost Energy prototype logger (ESP32 + DS18B20)");
  f.println("timestamp,t_core_c,t_mid_c,t_ambient_c,t_water_in_c,t_water_out_c,flow_l_min,rh_pct");
  f.close();
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PUMP, OUTPUT);
  setPump(false);
  pinMode(PIN_FLOW, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_FLOW), onFlowPulse, FALLING);

  probes.begin();
  probes.setResolution(12);  // 0.0625 C, 750 ms conversion

  Wire.begin();
  if (!rtc.begin()) Serial.println("RTC not found");
  if (rtc.lostPower()) rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  if (!sht31.begin(0x44)) Serial.println("SHT31 not found");

  if (!SD.begin(PIN_SD_CS)) Serial.println("SD init failed - logging to serial only");
  writeHeaderIfNew();
  lastFlowMs = millis();
}

void loop() {
  uint32_t nowMs = millis();
  if (nowMs - lastLogMs < LOG_INTERVAL_MS) return;
  lastLogMs = nowMs;

  probes.requestTemperatures();
  float tCore = readC(PROBE_CORE);
  float tMid = readC(PROBE_MID);
  float tAmb = readC(PROBE_AMBIENT);
  float tIn = readC(PROBE_WATER_IN);
  float tOut = readC(PROBE_WATER_OUT);
  float rh = sht31.readHumidity();

  noInterrupts();
  uint32_t pulses = flowPulses;
  flowPulses = 0;
  interrupts();
  float minutes = (nowMs - lastFlowMs) / 60000.0f;
  lastFlowMs = nowMs;
  float flowLMin = minutes > 0 ? (pulses / PULSES_PER_LITRE) / minutes : 0;

  DateTime now = rtc.now();
  char line[160];
  snprintf(line, sizeof(line), "%04d-%02d-%02dT%02d:%02d:%02d,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.1f",
           now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second(),
           tCore, tMid, tAmb, tIn, tOut, flowLMin, isnan(rh) ? NAN : rh);
  Serial.println(line);
  File f = SD.open(LOG_PATH, FILE_APPEND);
  if (f) {
    f.println(line);
    f.close();
  }

  // Decide the pump state for the next interval from this reading.
  updatePump(now, tCore, tIn);
}
