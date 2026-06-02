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

## 0. Connection check & self-heal — ALWAYS do this first

This phone runs adb over **loopback / classic tcpip** (`127.0.0.1:5555`) — **no WiFi,
no pairing**. Start every session by (re)attaching; it's a no-op if already connected
and silently re-attaches if the adb server was restarted:

```bash
adb connect 127.0.0.1:5555
adb devices            # expect: 127.0.0.1:5555  device
```

- Works with **WiFi off** (loopback is internal to the phone) and survives adb-server
  restarts — survives everything **except a phone reboot**.
- **Stray `emulator-5554` also listed:** target the phone explicitly,
  `adb -s 127.0.0.1:5555 shell …`.
- **`adb connect` fails** (`cannot connect` / `Connection refused`): the phone was
  **rebooted** (classic tcpip resets on reboot; persisting it needs root). Re-arm once
  over USB — a human step, so **stop and tell the user**, don't loop:
  > "adb channel dropped (looks like a phone reboot). Re-arm once: plug the phone into a
  > PC with USB debugging on, run `adb tcpip 5555`, then I'll reconnect — no WiFi needed."
- **`unauthorized`:** the phone is waiting for the on-screen **"Allow USB debugging?"**
  tap — ask the user to tap Allow (+ "Always allow") once.

**This uses classic `adb tcpip`, NOT the Android-11 "Wireless debugging" toggle.** That
button can stay **OFF** (its pairing is broken on Samsung/OneUI anyway); only "**USB
debugging**" must stay **ON** — it's what keeps adbd alive (verified live:
`adb_wifi_enabled=0`, `adb_enabled=1`, channel up).

## ⚠️ Before toggling WiFi / airplane

On **this** phone adb runs over **loopback** (`127.0.0.1:5555`), so disabling WiFi or
enabling airplane mode does **NOT** cut the adb link — you keep control either way.
(Only if you were attached over a WiFi IP — `adb connect <wifi-ip>:5555` — would WiFi-off
drop the link; in that case confirm first.)

Still: turning WiFi/data off changes the **user's** connectivity. Before `svc wifi
disable`, `svc data disable`, or airplane-on, briefly confirm if they're actively using
it. Turning radios back **on** is always safe.

## 1. WiFi

```bash
# State (1 = on, 0 = off)
adb shell settings get global wifi_on
adb shell cmd wifi status                      # Android 12+, richer status

# Turn on (safe). Turn off won't drop adb (loopback) but cuts the user's net — confirm.
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

# Airplane mode — drops WiFi/data, but adb survives on loopback; confirm with user first.
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

- **Connection check first**, every session: `adb connect 127.0.0.1:5555` (self-heal),
  then `adb devices`. Don't issue control commands blind.
- **adb is on loopback** — WiFi/airplane toggles don't cut it. Still confirm before
  `svc wifi disable` / airplane-on, since it disrupts the user's own connectivity.
- **Verify each toggle** with its matching status command; report the before/after.
- Use **non-interactive flags and bounded output** (`grep -m`, `head`) — never dump
  full `dumpsys`.
- **Never assume root.** If a command returns a permission error, `Can't find
  service`, or `cmd: not found`, the device is older or restricted — fall back to
  `settings put` / `am broadcast` (e.g. airplane:
  `settings put global airplane_mode_on 1 && am broadcast -a android.intent.action.AIRPLANE_MODE`),
  and report the exact command + output rather than blind-retrying.
- On `device offline` / `unauthorized`: `adb disconnect` then `adb connect
  127.0.0.1:5555` **once** (tap "Allow USB debugging" if prompted). If `adb connect`
  itself refuses, the phone likely rebooted — ask for the one-time USB `adb tcpip 5555`
  re-arm (see §0). Don't loop.
