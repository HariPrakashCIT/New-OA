# Knee Health firmware adapted for the OsteoCare website

Website: https://hariprakashcit.github.io/New-OA/
Firmware: https://hariprakashcit.github.io/New-OA/firmware/OsteoCareWiFi.zip

1. Sign in and open **Wi-Fi connection → Pair an insole**. Copy the device ID and private device key (shown once). Create a new device if you no longer have its key.
2. Unzip the firmware and open `OsteoCareWiFi/OsteoCareWiFi.ino` in Arduino IDE. Keep `trusted_roots.h` beside the sketch.
3. Install **esp32 by Espressif Systems 3.0.7**. Select your classic ESP32 DevKit board and port. Set `WIFI_SSID`, `WIFI_PASSWORD`, `DEVICE_ID` and `DEVICE_KEY` locally. Use internet-connected 2.4 GHz Wi-Fi or a phone hotspot; captive portals need a different network.
4. Upload once by USB. Leave the insole unloaded during startup calibration. Sensor wiring remains heel GPIO34, ball GPIO35, toe GPIO32, each with its resistor voltage divider and common ground. Respect ADC voltage limits; never feed 5 V to ADC pins.
5. Keep the ESP32 powered. All sensor transmission is now **Wi-Fi → HTTPS backend → database → website**. USB is only for uploading/power/debugging, not sensor transfer to the website.
6. Check Serial Monitor at 115200 baud for `Cloud saved reading (201)`. Watch the website's Live monitoring page. The free backend can take about a minute to wake up; the firmware retries with fresh data.
7. Record readings, create a daily/weekly/monthly report in **AI workspace**, then give consent and click **Explain with Gemma**. Reports show measured summaries separately from generated explanations.

## What was analyzed and adapted

The supplied `knee health.txt` sets up an ESP32 access point and HTTP `/api/data`. It samples three FSRs every 50 ms, subtracts a 100-sample unloaded baseline, clamps negative values to zero, and emits `v`, `seq`, `ms`, `fsr`, `total`, and `pressed`.

The uploaded DEX bridge contains `HttpURLConnection`, `http://192.168.4.1/api/data`, and `window.onKhrEvent`. The Android manifest includes internet access and cleartext networking support. These Android capabilities do not transfer directly into a public HTTPS browser. DEX and resource tables are compiled artifacts, not a complete editable frontend. The newly uploaded bridge differs from the older APK's bridge; the older APK's HTML expects obsolete `fsrMv`/IMU fields, so those assumptions were not imported.

The website adaptation preserves the three FSR pins, baseline procedure, ADC units, field order and >300 pressed threshold. It replaces the isolated hotspot with an internet-connected Wi-Fi station and a device-key-authenticated HTTPS upload. No IMUs, multiplexers, steps, calories or knee-force estimates were added.

## Data and AI behavior

- The firmware samples at 20 Hz independently of network requests. It uploads the latest sample roughly once per second plus request time. It does not upload every 20 Hz sample, buffer outages, or reconstruct gait events.
- `/api/knee-readings` validates timestamp, integer ranges, three-element arrays, version, total and pressed consistency before mapping `fsr[0..2]` to heel/ball/toe database columns. The existing device-key authentication applies.
- Timestamp uses internet-synchronized time adjusted to the sampled value. No upload occurs before clock synchronization. Sequence/uptime/total/pressed are validated but not separately persisted; equivalent total/pressed can be derived from stored pressures.
- Reports include zone mean/min/max and the proportion of saved readings above 300 ADC counts, relative loaded-signal shares, saturation flags and recording gaps. The original relative-share contact heuristic uses a combined signal above 150 counts. These are engineering descriptions, not clinical thresholds.
- Gemma receives bounded numeric summaries and fixed flags only, with user consent. It does not receive Wi-Fi credentials or device keys. Free-provider rate limits and availability still apply. A new report is needed to include newer samples.
- Do not combine old raw-ADC and new baseline-adjusted sessions for comparison. Pair a new insole record for this firmware if the previous record contains old-firmware readings. Restart unloaded to recalibrate.

## HTTPS and connectivity

The ZIP includes public trust anchors retrieved from Google's official PKI and Let's Encrypt. TLS verification stays enabled; do not use `setInsecure`. If the backend changes certificate issuers, update `trusted_roots.h` from the appropriate trusted CA source. No server secrets are included. Never upload your configured sketch with passwords/device keys to GitHub.

The original `KneeHealthReady` hotspot is not used by this cloud workflow. The website and ESP32 may use different networks as long as both have internet access. Physical Wi-Fi association, ADC wiring and model inference with your real recordings still require a hardware rehearsal.

## Verification

35 backend tests and 22 frontend tests passed. The Wi-Fi sketch compiled for `esp32:esp32:esp32` with core 3.0.7 (1,086,281 bytes flash; 47,584 bytes static RAM). Browser checks verify Wi-Fi setup, firmware download and AI navigation. Tests use fixtures; no invented telemetry was inserted into the production database.
