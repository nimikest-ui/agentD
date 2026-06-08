---
name: adb-phone-control
description: "Use when the user asks the agent to control the Android phone from Kali — toggle WiFi/Bluetooth/mobile data, set alarms, make calls, send SMS, adjust volume/brightness, control media, take photos, manage notifications, open apps/URLs, screen record, and more — via ADB over wireless debugging (no root)."
compatibility: Requires shell execution (the `execute` tool) and `adb` installed in Kali, with the phone reachable over wireless debugging.
allowed-tools: execute, read_file, write_file
---

# ADB Phone Control (no root)

Drive the Android phone's radios, apps, and UI from Kali over **ADB wireless debugging**.
No root, no Termux:API — every command below runs through `adb` via the `execute`
tool.

## What this can and cannot do

The ADB shell runs as the **shell user (UID 2000)**, which Android trusts for a lot
without root:

- ✅ Toggle **WiFi / Bluetooth / mobile data** on and off
- ✅ **Scan** nearby WiFi APs; read radio + connection state
- ✅ **Connect** to a WiFi network
- ✅ Read device state (battery, settings), take **screenshots**, simulate **taps**
- ✅ Set **alarms**, make **calls**, send **SMS**
- ✅ Control **volume**, **brightness**, **Do Not Disturb**
- ✅ **Open apps and URLs**, launch **camera**
- ✅ Control **media playback** (play/pause/next/prev)
- ✅ Manage **notifications**, read **clipboard**
- ✅ **Screen record**, **screen rotation**, **lock screen**
- ✅ Insert **calendar events**, view **contacts**

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

**Default to the UI tree, NOT screenshots.** `uiautomator dump` gives a cheap text
hierarchy with every element's `text`, `resource-id`, `content-desc`, and on-screen
`bounds` — enough to find and tap anything. **Never `read_file` a full-res screenshot
into the model** — a ~1.5 MB PNG stalls the model mid-turn (this is the #1 cause of "the
agent froze and never tapped anything"). Use vision only as a last resort, downscaled.

```bash
# Dump the on-screen UI hierarchy (text, ~tens of KB) and find your target
adb -s 127.0.0.1:5555 shell uiautomator dump /sdcard/ui.xml >/dev/null
adb -s 127.0.0.1:5555 shell cat /sdcard/ui.xml | tr '>' '>\n' \
  | grep -i 'clickable="true"' | grep -iE 'PLAY|Search|<label you want>'
# a node's bounds="[x1,y1][x2,y2]" → tap its centre: cx=(x1+x2)/2, cy=(y1+y2)/2

adb -s 127.0.0.1:5555 shell input tap <cx> <cy>
adb -s 127.0.0.1:5555 shell input swipe <x1> <y1> <x2> <y2> 300   # scroll / drag
adb -s 127.0.0.1:5555 shell input keyevent KEYCODE_HOME           # or BACK, ENTER, …
```

**Vision fallback (only if the tree isn't enough): downscale first**, or the read hangs
the model. Needs ImageMagick (`convert`) or PIL in Kali:

```bash
adb -s 127.0.0.1:5555 exec-out screencap -p > /tmp/screen_full.png
convert /tmp/screen_full.png -resize 540x /tmp/screen.png   # then read_file /tmp/screen.png
```

### Worked example — open YouTube and play a (random) video, no vision

```bash
P=com.google.android.youtube
adb -s 127.0.0.1:5555 shell monkey -p $P -c android.intent.category.LAUNCHER 1   # open app
sleep 3
adb -s 127.0.0.1:5555 shell uiautomator dump /sdcard/ui.xml >/dev/null
# Video thumbnails are clickable nodes whose content-desc is the title — grab the first:
adb -s 127.0.0.1:5555 shell cat /sdcard/ui.xml | tr '>' '>\n' \
  | grep -i 'clickable="true"' | grep -i 'content-desc=' | head -1
# read its bounds, compute the centre, tap it:
adb -s 127.0.0.1:5555 shell input tap <cx> <cy>
```

`resource-id`/`content-desc` strings vary by app version — inspect the dump and tap the
first thumbnail node. Once a video is open, `input keyevent KEYCODE_MEDIA_PLAY_PAUSE`
toggles playback. Verify with `dumpsys media_session | grep -i -m3 'state\|package'`.

## 5. Alarms

```bash
# Set an alarm (opens clock app or sets silently depending on OEM)
adb shell am start -a android.intent.action.SET_ALARM \
  --ei android.intent.extra.alarm.HOUR 5 \
  --ei android.intent.extra.alarm.MINUTES 30 \
  --ez android.intent.extra.alarm.SKIP_UI true \
  --es android.intent.extra.alarm.MESSAGE "Wake up"

# Parameters:
#   HOUR        — 0-23 (24h format)
#   MINUTES     — 0-59
#   SKIP_UI     — true = set silently (may not work on all OEMs)
#   MESSAGE     — alarm label
#   VIBRATE     — true/false (optional)
#   DAYS        — bitmask for repeat (optional): 1=Sun,2=Mon,4=Tue,8=Wed,16=Thu,32=Fri,64=Sat
#                  e.g. 62 = Mon-Fri (2+4+8+16+32)

# If SKIP_UI doesn't work (some Samsung/OEM), the intent opens the clock app pre-filled —
# the user may need to tap "Save". Report what happened.
```

## 6. Phone calls

```bash
# Dial (opens dialer — user must tap call)
adb shell am start -a android.intent.action.DIAL -d tel:+1234567890

# Direct call (places call immediately — requires phone permission)
adb shell am start -a android.intent.action.CALL -d tel:+1234567890

# End call
adb shell input keyevent KEYCODE_ENDCALL
```

Use `DIAL` to be safe (shows dialer for user confirmation). Use `CALL` only when the
user explicitly wants to place the call immediately.

## 7. SMS

```bash
# Open SMS app with pre-filled message (user must tap send)
adb shell am start -a android.intent.action.SENDTO \
  -d "sms:+1234567890" \
  --es sms_body "Hello from ADB"

# On some devices, append ?body= to the URI instead:
adb shell am start -a android.intent.action.SENDTO \
  -d "smsto:+1234567890?body=Hello%20from%20ADB"
```

Note: ADB cannot send SMS silently without root. This opens the messaging app
pre-filled — the user taps send. This is a safety feature, not a limitation.

## 8. Volume control

```bash
# List volume streams
adb shell cmd media_session volume --stream 3 --get    # 3 = music (STREAM_MUSIC)
adb shell cmd media_session volume --stream 1 --get    # 1 = ring (STREAM_RING)
adb shell cmd media_session volume --stream 2 --get    # 2 = notification
adb shell cmd media_session volume --stream 4 --get    # 4 = alarm

# Set volume (0 = min, max varies by device, usually 15)
adb shell cmd media_session volume --stream 3 --set 10

# Adjust by step (+1 / -1)
adb shell cmd media_session volume --stream 3 --adj raise
adb shell cmd media_session volume --stream 3 --adj lower

# Mute / unmute
adb shell cmd media_session volume --stream 3 --set 0

# Keyevent alternatives (adjusts current stream)
adb shell input keyevent KEYCODE_VOLUME_UP
adb shell input keyevent KEYCODE_VOLUME_DOWN
adb shell input keyevent KEYCODE_VOLUME_MUTE
```

Stream types: 0=voice, 1=ring, 2=notification, 3=music, 4=alarm, 5=system

## 9. Screen brightness

```bash
# Read current brightness (0-255)
adb shell settings get system screen_brightness

# Set brightness (0-255)
adb shell settings put system screen_brightness 128    # 50%
adb shell settings put system screen_brightness 255    # max
adb shell settings put system screen_brightness 10     # very dim

# Toggle auto-brightness (1 = on, 0 = off)
adb shell settings get system screen_brightness_mode
adb shell settings put system screen_brightness_mode 0  # manual
adb shell settings put system screen_brightness_mode 1  # auto
```

## 10. Do Not Disturb (DND)

```bash
# Check DND state
adb shell settings get global zen_mode    # 0=off, 1=priority, 2=total silence, 3=alarms

# Enable total silence
adb shell cmd notification set_dnd on

# Disable DND
adb shell cmd notification set_dnd off

# Alternative via settings (Android 9+)
adb shell settings put global zen_mode 1    # priority only
adb shell settings put global zen_mode 0    # off
```

## 11. Open apps and URLs

```bash
# Open a URL in default browser
adb shell am start -a android.intent.action.VIEW -d "https://example.com"

# Open a specific app by package name
adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main
adb shell am start -n com.whatsapp/.Main

# Open Android settings
adb shell am start -a android.settings.SETTINGS
adb shell am start -a android.settings.WIFI_SETTINGS
adb shell am start -a android.settings.BLUETOOTH_SETTINGS
adb shell am start -a android.settings.DISPLAY_SETTINGS
adb shell am start -a android.settings.SOUND_SETTINGS
adb shell am start -a android.settings.BATTERY_SAVER_SETTINGS

# List installed packages (find package names)
adb shell pm list packages | grep -i "chrome\|whatsapp\|spotify"

# Open YouTube video
adb shell am start -a android.intent.action.VIEW -d "https://youtube.com/watch?v=VIDEO_ID"

# Open Google Maps location
adb shell am start -a android.intent.action.VIEW -d "geo:37.7749,-122.4194"
```

## 12. Camera

```bash
# Take a photo (opens camera app)
adb shell am start -a android.media.action.IMAGE_CAPTURE

# Record video
adb shell am start -a android.media.action.VIDEO_CAPTURE

# Open camera in specific mode (OEM-dependent)
adb shell am start -a android.media.action.STILL_IMAGE_CAMERA
```

## 13. Media playback control

```bash
# Play / pause
adb shell input keyevent KEYCODE_MEDIA_PLAY_PAUSE

# Next / previous track
adb shell input keyevent KEYCODE_MEDIA_NEXT
adb shell input keyevent KEYCODE_MEDIA_PREVIOUS

# Stop
adb shell input keyevent KEYCODE_MEDIA_STOP

# Play / pause via media session (more reliable on some devices)
adb shell cmd media_session dispatch play
adb shell cmd media_session dispatch pause
adb shell cmd media_session dispatch next
adb shell cmd media_session dispatch previous

# What's currently playing (may show metadata)
adb shell dumpsys media_session | grep -i -m 10 "state\|metadata\|artist\|title\|package"
```

## 14. Notifications

```bash
# List recent notifications (bounded output)
adb shell dumpsys notification --noredact | grep -i -m 20 "pkg=\|title=\|text="

# Dismiss all notifications
adb shell service call notification 1        # cancel all (may vary by Android version)

# Open notification shade
adb shell cmd statusbar expand-notifications

# Close notification shade
adb shell cmd statusbar collapse
```

## 15. Clipboard

```bash
# Read clipboard (Android 10+ restricted — may return empty on newer versions)
adb shell cmd clipboard get

# Set clipboard text (Android 12+)
adb shell cmd clipboard set "Hello from ADB"

# Older Android (pre-12) clipboard via input
adb shell input text "text_to_type"
```

Note: Android 10+ restricts background clipboard access. Setting works on Android 12+;
reading may be empty unless an app is in foreground.

## 16. Screen rotation

```bash
# Check auto-rotate state (0 = portrait locked, 1 = auto)
adb shell settings get system accelerometer_rotation

# Disable auto-rotate (lock orientation)
adb shell settings put system accelerometer_rotation 0

# Enable auto-rotate
adb shell settings put system accelerometer_rotation 1

# Set rotation manually (0=0°, 1=90°, 2=180°, 3=270°)
adb shell settings put system user_rotation 1    # landscape
adb shell settings put system user_rotation 0    # portrait
```

## 17. Screen recording

```bash
# Record screen (max 3 minutes by default)
adb shell screenrecord /sdcard/recording.mp4

# Record with options
adb shell screenrecord --time-limit 30 --size 720x1280 /sdcard/recording.mp4

# Stop: Ctrl+C in terminal, or kill the process
# Pull the file to local machine
adb pull /sdcard/recording.mp4 /tmp/recording.mp4
```

## 18. Calendar events

```bash
# Insert a calendar event
adb shell content insert --uri content://com.android.calendar/events \
  --bind title:s:"Meeting with Team" \
  --bind description:s:"Discuss project" \
  --bind dtbegin:l:$(date -d "tomorrow 10:00" +%s)000 \
  --bind dtend:l:$(date -d "tomorrow 11:00" +%s)000 \
  --bind eventTimezone:s:"UTC"

# List calendars
adb shell content query --uri content://com.android.calendar/calendars --projection _id:calendar_displayName

# List upcoming events
adb shell content query --uri content://com.android.calendar/events --projection _id:title:dtstart --where "dtstart>=$(date +%s)000" --sort "dtstart ASC"
```

Note: Calendar content provider access varies by Android version and OEM. May return
empty if the calendar app restricts shell access.

## 19. Contacts

```bash
# Search contacts
adb shell content query --uri content://com.android.contacts/contacts --projection display_name:_id --where "display_name LIKE '%John%'"

# List all contact names (bounded)
adb shell content query --uri content://com.android.contacts/contacts --projection display_name --sort "display_name ASC" 2>/dev/null | head -30
```

## 20. Lock screen / power

```bash
# Lock the screen
adb shell input keyevent KEYCODE_POWER

# Wake up (if screen is off)
adb shell input keyevent KEYCODE_WAKEUP

# Unlock (swipe up — won't work with PIN/pattern)
adb shell input swipe 540 1800 540 800 300

# Reboot (confirm with user first!)
adb shell reboot

# Take screenshot and save locally
adb exec-out screencap -p > /tmp/phone_screen.png
```

## 21. Input text and keyboard

```bash
# Type text (as if from keyboard — works in any text field)
adb shell input text "Hello%20World"    # spaces must be %20

# Special keys
adb shell input keyevent KEYCODE_ENTER
adb shell input keyevent KEYCODE_TAB
adb shell input keyevent KEYCODE_DEL        # backspace
adb shell input keyevent KEYCODE_ESCAPE

# Paste from clipboard (if set via cmd clipboard set)
adb shell input keyevent KEYCODE_PASTE
```

## Quick reference — common intents

| Action | Command |
|--------|---------|
| Set alarm | `am start -a android.intent.action.SET_ALARM --ei HOUR <h> --ei MINUTES <m>` |
| Dial number | `am start -a android.intent.action.DIAL -d tel:<number>` |
| Call number | `am start -a android.intent.action.CALL -d tel:<number>` |
| Send SMS | `am start -a android.intent.action.SENDTO -d "sms:<number>" --es sms_body "<msg>"` |
| Open URL | `am start -a android.intent.action.VIEW -d "<url>"` |
| Open settings | `am start -a android.settings.SETTINGS` |
| Take photo | `am start -a android.media.action.IMAGE_CAPTURE` |
| Play/pause | `input keyevent KEYCODE_MEDIA_PLAY_PAUSE` |
| Volume up/down | `input keyevent KEYCODE_VOLUME_UP/DOWN` |

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
- **OEM variance**: Samsung, Xiaomi, OnePlus etc. may restrict some intents or require
  different package names. If a command fails, try alternatives listed in each section
  and report the exact error to the user.
- **Confirm before destructive actions**: reboot, airplane mode, disabling radios —
  always check with the user first.
