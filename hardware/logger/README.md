# Prototype logger

> **Status: designed, not yet built or flashed.** The firmware targets the libraries' documented APIs. Expect to adjust pins and probe addresses on the first build.

An ESP32 that logs five temperatures, water flow and headspace humidity every 2 minutes to an SD card. It also switches the water-loop pump. Its output file goes straight into the same pipeline as the simulated runs:

```bash
cp /Volumes/SD/raw_run.csv data/measured/raw_run_01.csv
python model/scripts/analyze_run.py data/measured/raw_run_01.csv
```

## Parts (~€45)

| Part | Qty | Why this one |
|---|---|---|
| ESP32 DevKit v1 | 1 | cheap, Wi-Fi for later remote monitoring |
| DS18B20 waterproof probe, 1-3 m lead | 5 | 0.0625 °C resolution, many sensors on one wire |
| 4.7 kΩ resistor | 1 | 1-Wire pull-up |
| YF-S401 hall flow sensor (0.3-6 L/min) | 1 | works at the low flow the loop needs (0.35 L/min) |
| DS3231 RTC module | 1 | accurate timestamps through power cuts |
| microSD module + card | 1 | local log, no network needed |
| SHT31 breakout in a vented enclosure | 1 | headspace humidity |
| 12 V mini diaphragm pump + logic-level MOSFET module | 1 | water loop |
| 12 V supply + buck converter to 5 V | 1 | |

## Wiring

| Signal | ESP32 pin |
|---|---|
| 1-Wire bus (all DS18B20 data, 4.7 kΩ to 3.3 V) | GPIO 4 |
| Flow sensor signal (internal pull-up) | GPIO 27 |
| Pump MOSFET gate | GPIO 26 |
| SD CS / SCK / MISO / MOSI | 5 / 18 / 19 / 23 |
| I²C SDA / SCL (RTC + SHT31) | 21 / 22 |

Probe placement:

- `t_core`: centre of chamber B, touching the exchanger coil
- `t_mid`: halfway between the core and the wall
- `t_ambient`: shaded, outside the box
- `t_water_in`, `t_water_out`: strapped to the pipe where it enters and leaves the pile, under foam insulation

## Why the flow is so low

At around 50-130 W of extraction, a typical 2 L/min would warm the water by less than 1 °C. That is close to the DS18B20's ±0.5 °C accuracy, so the result would be mostly noise. At 0.35 L/min the outlet rises 3-5 °C, which the probes can measure reliably. The simulation uses the same flow rate for the same reason. Calibrate the flow sensor with a measuring jug and a stopwatch, and swap the two water probes once to cancel their offset.

## Faults the analysis already handles

- DS18B20 `-127` (disconnected) and `85` (read before conversion) error codes
- Stuck readings, spikes, and duplicated or out-of-order rows
- Gaps from power cuts. Gaps up to 30 min are interpolated; longer gaps are left empty.

The firmware logs raw values and never filters on the device, so nothing is lost if the cleaning rules change later.
