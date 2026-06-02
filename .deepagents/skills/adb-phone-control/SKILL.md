---
name: adb-phone-control
description: "Use when the user asks the agent to control the Android phone's WiFi, Bluetooth, mobile data, or device state from Kali — toggle radios on/off, scan networks/devices, connect to WiFi, screenshot, or tap the UI — via ADB over wireless debugging (no root)."
compatibility: Requires shell execution (the `execute` tool) and `adb` installed in Kali, with the phone reachable over wireless debugging.
allowed-tools: execute, read_file, write_file
---

# ADB Phone Control (no root)

Drive the Android phone's radios and UI from Kali over **ADB wireless debugging**.
No root, no Termux:API — every command below runs through `adb` via the `execute`
tool.

## What this can and cannot do

The ADB shell runs as the **shell user (UID 2000)**, which Android trusts for a lot
without root:

- ✅ Toggle **WiFi / Bluetooth / mobile data** on and off
- ✅ **Scan** nearby WiFi APs; read radio + connection state
- ✅ **Connect** to a WiFi network
- ✅ Read device state (battery, settings), take **screenshots**, simulate **taps**

It **cannot** (these need root + a custom/NetHunter kernel — do not attempt, tell the
user it's out of scope):

- ❌ WiFi/Bluetooth **monitor mode / packet injection** (aircrack, bettercap, hcitool)
- ❌ Reading other apps' private data, remounting `/system`, raw HCI access

## 0. Connection check — ALWAYS do this first

```bash
adb devices
```

Look for a line ending in `device` (not `offline` / `unauthorized` / empty).

- **No device / `offline`:** reconnect to the IP:PORT shown on the phone's
  *Wireless debugging* screen: `adb connect <ip>:<port>` (then re-run `adb devices`).
- **`unauthorized`:** the phone needs to re-accept this host — re-pair (below).
- **Pairing (one-time, needs a human):** `adb pair <ip>:<pairport>` then enter the
  6-digit code from *Wireless debugging → Pair device with pairing code*. **You
  cannot supply this code yourself — ask the user for it once and stop; do not loop.**
- **If `adb pair` fails** with `protocol fault (couldn't read status message): Success`
  (known broken on some devices, notably **Samsung/OneUI** — the device's
  wireless-debugging *pairing* service is the problem, not adb): use the **one-time USB
  bootstrap** instead. From any computer with adb, USB-plug the phone (USB debugging on),
  run `adb tcpip 5555`, unplug — then attach over the network with
  `adb connect <phone-ip>:5555` (or `adb connect 127.0.0.1:5555` when adb runs on the
  phone itself). That's classic tcpip — no TLS, no pairing. Re-run the USB `adb tcpip
  5555` after a device reboot. The first network connect triggers an on-screen
  "Allow USB debugging?" prompt — the user taps Allow once.
- **Multiple devices listed** (e.g. a stray `emulator-5554`): target the phone
  explicitly with `adb -s <serial> shell …`, e.g. `adb -s 127.0.0.1:5555 shell …`.

## ⚠️ Self-disconnect safety (read before toggling)

If ADB is reaching the phone **over WiFi** (it is, with wireless debugging), then
**disabling WiFi — or enabling airplane mode — cuts the ADB link itself** and you
lose all control until the user re-enables it on the device. Before any
`svc wifi disable`, airplane-mode-on, or a WiFi *switch* to another network:

1. State plainly that it will drop your connection, and
2. **Get explicit user confirmation first.** Never do it unprompted.

Toggling **Bluetooth** or **mobile data** is safe (doesn't affect the WiFi transport).

## 1. WiFi

```bash
# State (1 = on, 0 = off)
adb shell settings get global wifi_on
adb shell cmd wifi status                      # Android 12+, richer status

# Turn on  (safe).  Turn off = SEE self-disconnect warning above.
adb shell svc wifi enable
adb shell svc wifi disable

# Scan nearby access points  (Android 11+)
adb shell cmd wifi start-scan
adb shell cmd wifi list-scan-results

# Saved networks / connect  (Android 11+; may pop a confirm dialog on some OEMs)
adb shell cmd wifi list-networks
adb shell cmd wifi connect-network "<SSID>" wpa2 "<password>"
adb shell cmd wifi connect-network "<SSID>" open
```

After any toggle, **verify** with `settings get global wifi_on`.

## 2. Bluetooth (safe to toggle)

```bash
adb shell settings get global bluetooth_on     # 1 / 0
adb shell svc bluetooth enable
adb shell svc bluetooth disable

# Adapter + bonded (paired) devices — keep output bounded
adb shell dumpsys bluetooth_manager | grep -i -m 20 -A2 "state\|Bonded\|mAddress\|name"
```

Note: scanning for *new* BLE devices from the shell is limited/unreliable without an
app; `dumpsys bluetooth_manager` reliably shows adapter state and already-bonded
devices. Don't promise live discovery scans.

## 3. Mobile data, airplane, and device state

```bash
adb shell svc data enable                       # mobile data on/off (safe)
adb shell svc data disable

# Airplane mode — enabling it drops WiFi too: SEE self-disconnect warning.
adb shell cmd connectivity airplane-mode enable     # Android 11+
adb shell cmd connectivity airplane-mode disable

adb shell dumpsys battery | grep -i -m 5 "level\|status\|powered"
```

## 4. See the screen / tap the UI

```bash
adb exec-out screencap -p > /tmp/screen.png     # then read_file /tmp/screen.png for vision
adb shell input tap <x> <y>
adb shell input swipe <x1> <y1> <x2> <y2> 300
adb shell input keyevent KEYCODE_HOME           # or KEYCODE_BACK, KEYCODE_POWER, …
```

## Rules of engagement

- **Connection check first**, every session. Don't issue control commands blind.
- **Confirm before any action that drops the ADB-over-WiFi link** (WiFi off, airplane
  on, switching WiFi networks). Bluetooth/mobile-data toggles don't need this.
- **Verify each toggle** with its matching status command; report the before/after.
- Use **non-interactive flags and bounded output** (`grep -m`, `head`) — never dump
  full `dumpsys`.
- **Never assume root.** If a command returns a permission error, `Can't find
  service`, or `cmd: not found`, the device is older or restricted — fall back to
  `settings put` / `am broadcast` (e.g. airplane:
  `settings put global airplane_mode_on 1 && am broadcast -a android.intent.action.AIRPLANE_MODE`),
  and report the exact command + output rather than blind-retrying.
- On `device offline` / `unauthorized`: `adb disconnect` then `adb connect
  <ip>:<port>` **once**; if it still fails, report and ask the user to re-check
  Wireless debugging / re-pair.
