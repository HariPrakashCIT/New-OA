# ESP32 USB connection

Open https://hariprakashcit.github.io/New-OA/ in desktop **Chrome or Edge**, then select **USB connection**. USB live monitoring does not require sign-in or Wi-Fi on the ESP32. The laptop needs internet to load the website and to save readings or generate reports.

## Upload the USB sketch once

1. Download `OsteoCareUSB.ino` from the website's USB setup page, or open `firmware/OsteoCareUSB/OsteoCareUSB.ino` from this repository in Arduino IDE.
2. Install **esp32 by Espressif Systems**, version **3.0.7**, in Boards Manager and select your board and port. The default pin map targets a **classic ESP32 DevKit**.
3. Connect three FSR voltage-divider outputs to **heel GPIO 34**, **ball GPIO 35**, **toe GPIO 32**, with a common ground. Ensure ADC inputs stay within your board's ratings; never apply 5 V. Adjust the sketch's pin constants if your wiring differs. Other ESP32 variants require their own valid ADC pins; native-USB boards may require USB CDC On Boot enabled.
4. Upload. The USB sketch replaces the Wi-Fi sketch; re-upload the original sketch to return to direct Wi-Fi transmission. No Wi-Fi password, API key or certificate belongs in the USB sketch.
5. Close Arduino Serial Monitor/Plotter and other tabs that use the port.
6. Use a USB **data** cable, click **Connect USB** on the website, and choose the ESP32 port in the browser prompt.
7. Press each FSR and confirm that the correct live value changes. A connected port alone does not establish that sensors are wired correctly.

The browser requires explicit device permission. It cannot silently connect merely because a cable is inserted. If the port is missing, check the data cable and your board manufacturer's CP210x/CH340 driver. Safari and Firefox do not support this Web Serial workflow.

## Save USB readings

Sign in, create/select an insole, and enable **Save USB readings to my account** on the USB connection page. No device secret is needed for this browser bridge: the backend authenticates the signed-in account and verifies ownership of the selected insole.

- The local chart retains the latest **1,800** real USB samples in memory.
- Cloud saving submits the most recent sample at most once per second, with only one request in flight.
- Only backend-confirmed writes count as saved; failed samples are not queued or fabricated. Later readings retry automatically while saving remains enabled.
- Reports, PDFs, AI and other signed-in devices read confirmed database records, not unsaved preview data.
- Start a walking session after the first cloud confirmation. Session duration is elapsed time, not a clinical gait measurement.
- Keep the tab open and laptop awake. Closing/reloading the tab discards unsaved samples. Reconnect and re-enable cloud saving after a reload or disconnection.
- USB timestamps are laptop receive times; enable automatic clock synchronization. They are not hardware acquisition timestamps.

## Protocol

USB firmware emits one newline-delimited JSON message about every 110 ms at **115200 baud**:

```text
{"type":"osteocare_reading","protocol":1,"heel_pressure":<integer>,"ball_pressure":<integer>,"toe_pressure":<integer>}
```

Each value must be a real 12-bit ADC count from 0 to 4095. The browser rejects missing, non-integer and out-of-range values; boot text is ignored. Lines are bounded to 1,024 characters. No browser-provided code or serial command is executed.

The authenticated bridge is `POST /api/devices/{device_id}/usb-readings`, using a Supabase user access token. Its JSON body contains an ISO `timestamp` and the three pressure values. Device ownership, ADC validation and timestamp checks are enforced server-side. The existing ESP32 Wi-Fi `/api/readings` endpoint and device-key authentication remain supported.

## Validation limits

Automated tests exercise decoding, fragmented messages, invalid data, disconnect/reconnect, port release, cloud failures, and device ownership. Chromium browser checks use a simulated serial stream on a local test page and do not insert invented telemetry into the live database. A physical ESP32/cable/FSR rehearsal is still required.

The USB sketch compiles with Arduino CLI 1.6.0, Espressif ESP32 core 3.0.7 and `esp32:esp32:esp32` (286,937 bytes flash; 20,336 bytes static RAM). Compilation does not verify physical wiring.
