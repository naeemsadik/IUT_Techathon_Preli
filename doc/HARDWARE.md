# Hardware Reference Schematic (Phase 3)

> **⚠ Reference only — not runtime.**
>
> This document describes the **intended** hardware deployment for the office
> energy monitoring system. The Wokwi / Tinkercad schematic is a deliverable
> that proves out the physical design (ESP32 + relays + loads), but it does
> **not** feed data into the running system.
>
> The runtime data source is `simulator/simulator.py`, which POSTs synthetic
> `heartbeat` and `state_change` payloads to `POST /api/ingest`. Wiring the
> real ESP32 to the backend is a follow-up deployment task.

---

## 1. Scope

This document covers a **single-room** prototype (Drawing Room, 5 devices) —
the smallest unit that exercises the full wiring pattern. The same pattern
replicates across the other two rooms.

| Component | Quantity | Notes |
|---|---|---|
| ESP32 DevKit V1 | 1 | Wi-Fi enabled MCU, runs the firmware that sends ingest payloads |
| 5 V single-channel relay modules | 5 | One per load; optically isolated |
| AC fans (≤ 60 W) | 2 | Drawing Room fan 1, Drawing Room fan 2 |
| LED bulbs or tube lights (≤ 15 W) | 3 | Drawing Room lights 1, 2, 3 |
| 5 V DC supply (≥ 2 A) | 1 | Powers the ESP32 + relay coils |
| 230 V → 5 V AC-DC converter | 1 | For the relay + MCU supply, fused |

---

## 2. Pin Map (Drawing Room)

The Wokwi / Tinkercad schematic uses these GPIOs:

| Load | Device ID | Relay IN pin (ESP32 GPIO) | Notes |
|---|---|---|---|
| Fan 1 | `drawing_room_fan_1` | `GPIO 26` | Active-HIGH relay |
| Fan 2 | `drawing_room_fan_2` | `GPIO 27` | Active-HIGH relay |
| Light 1 | `drawing_room_light_1` | `GPIO 32` | Active-HIGH relay |
| Light 2 | `drawing_room_light_2` | `GPIO 33` | Active-HIGH relay |
| Light 3 | `drawing_room_light_3` | `GPIO 25` | Active-HIGH relay |

> Active-HIGH means `digitalWrite(pin, HIGH)` energises the relay and turns
> the load on. The firmware must invert for any active-LOW relays on hand.

---

## 3. Wiring Diagram (ASCII)

```text
   AC MAINS (230 V, fused)
        │
        ├─── Fan 1 ─── Relay CH1 ─── GPIO 26
        ├─── Fan 2 ─── Relay CH2 ─── GPIO 27
        ├─── Light 1 ─ Relay CH3 ─── GPIO 32
        ├─── Light 2 ─ Relay CH4 ─── GPIO 33
        └─── Light 3 ─ Relay CH5 ─── GPIO 25

                    ┌──── 5 V DC ────────┐
                    │                    │
                  ESP32               Relays
                    │                    │
                    │   GND ───────── GND │
                    └────────────────────┘
```

**Safety notes:**

- All 230 V wiring must be done by a qualified electrician.
- Use proper insulation on mains-side relay contacts.
- Flyback diodes are not needed for resistive loads like incandescent bulbs
  and shaded-pole fans, but always include snubbers for inductive loads.
- Provide a fuse or circuit breaker on the mains feed.

---

## 4. Suggested ESP32 Firmware Sketch (pseudocode)

The full Arduino sketch lives outside this repo (it's deployed to the device,
not the host running the FastAPI server). For reference, the loop on the
ESP32 does roughly:

```cpp
void loop() {
  // Every N seconds, send a heartbeat for the room.
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MS) {
    sendHeartbeat();
    lastHeartbeat = now;
  }

  // On any GPIO edge, send a state_change.
  for (each load) {
    bool currentState = digitalRead(load.gpio);
    if (currentState != load.lastReported) {
      sendStateChange(load);
      load.lastReported = currentState;
    }
  }

  delay(50);
}
```

JSON shape (matches the backend's `HeartbeatPayload` / `StateChangePayload`):

```json
{
  "message_type": "heartbeat",
  "source_id": "esp32-drawing-room",
  "sequence": 17,
  "device_timestamp": "2026-07-04T14:00:00Z",
  "devices": [
    { "device_id": "drawing_room_fan_1", "room": "drawing_room",
      "device_type": "fan", "status": "off", "power_draw_w": 60 }
  ]
}
```

`power_draw_w` should be the **rated** wattage of the load, not a measured
value. The backend zeros it for the API when `status == "off"`.

`device_timestamp` is **informational only** — the backend always stamps
`last_changed` server-side to avoid clock skew.

---

## 5. How to Deploy (When Ready)

To swap from `simulator.py` to real ESP32 hardware:

1. Build & flash the ESP32 firmware that speaks the JSON contract above.
2. Ensure the ESP32 can reach the FastAPI host on the network.
3. Stop `simulator.py`.
4. Power-cycle each room's MCU; the first heartbeat per room syncs
   state with the backend (matches `last_changed = now`).
5. Confirm via the frontend or `!status` that real device readings
   appear within HEARTBEAT_INTERVAL_MS.

The backend is **unaware** of where the payloads come from. Any source that
respects the contract (`POST /api/ingest`, Pydantic-validated) will work.

---

## 6. Related Documents

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) §5A — Edge Simulation Layer
- [`SIMULATOR.md`](./SIMULATOR.md) — The runtime simulator that
  replaces this hardware for development.
- [`SYSTEM_GUIDE.md`](./SYSTEM_GUIDE.md) §6 — Payload contract
