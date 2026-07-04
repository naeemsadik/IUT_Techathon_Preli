/* ============================================================
   Office Energy Monitor — Dashboard client
   ------------------------------------------------------------
   - On load: GET /api/status → render initial state
             GET /api/usage  → render usage panel
   - Then subscribe to:
       WS /ws/dashboard  → apply state_diff in real time
       WS /ws/alerts     → push alerts into the alerts panel
   ============================================================ */

(() => {
  "use strict";

  // ----------------------------------------------------------
  // Config
  // ----------------------------------------------------------

  const params = new URLSearchParams(window.location.search);
  const API_BASE = params.get("api") || window.location.origin.replace(/:\d+$/, ":8000");
  // Override via ?api=http://host:port if backend isn't on the default port.

  const WS_DASHBOARD = apiBaseToWs(`${API_BASE}/ws/dashboard`);
  const WS_ALERTS = apiBaseToWs(`${API_BASE}/ws/alerts`);

  function apiBaseToWs(url) {
    return url.replace(/^http/, "ws");
  }

  // Static device layout, mirrored from backend/app/state.py
  // (2 fans + 3 lights × 3 rooms = 15 devices).
  const ROOMS = [
    {
      slug: "drawing_room",
      name: "Drawing Room",
      devices: [
        { device_id: "drawing_room_fan_1",   room: "drawing_room", device_type: "fan",   display_name: "Fan 1" },
        { device_id: "drawing_room_fan_2",   room: "drawing_room", device_type: "fan",   display_name: "Fan 2" },
        { device_id: "drawing_room_light_1", room: "drawing_room", device_type: "light", display_name: "Light 1" },
        { device_id: "drawing_room_light_2", room: "drawing_room", device_type: "light", display_name: "Light 2" },
        { device_id: "drawing_room_light_3", room: "drawing_room", device_type: "light", display_name: "Light 3" },
      ],
    },
    {
      slug: "work_room_1",
      name: "Work Room 1",
      devices: [
        { device_id: "work_room_1_fan_1",   room: "work_room_1", device_type: "fan",   display_name: "Fan 1" },
        { device_id: "work_room_1_fan_2",   room: "work_room_1", device_type: "fan",   display_name: "Fan 2" },
        { device_id: "work_room_1_light_1", room: "work_room_1", device_type: "light", display_name: "Light 1" },
        { device_id: "work_room_1_light_2", room: "work_room_1", device_type: "light", display_name: "Light 2" },
        { device_id: "work_room_1_light_3", room: "work_room_1", device_type: "light", display_name: "Light 3" },
      ],
    },
    {
      slug: "work_room_2",
      name: "Work Room 2",
      devices: [
        { device_id: "work_room_2_fan_1",   room: "work_room_2", device_type: "fan",   display_name: "Fan 1" },
        { device_id: "work_room_2_fan_2",   room: "work_room_2", device_type: "fan",   display_name: "Fan 2" },
        { device_id: "work_room_2_light_1", room: "work_room_2", device_type: "light", display_name: "Light 1" },
        { device_id: "work_room_2_light_2", room: "work_room_2", device_type: "light", display_name: "Light 2" },
        { device_id: "work_room_2_light_3", room: "work_room_2", device_type: "light", display_name: "Light 3" },
      ],
    },
  ];

  const ICONS = {
    fan: `<svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor" aria-hidden="true">
            <path d="M12 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4Zm0 16a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM4.93 4.93a2 2 0 1 0 0 2.83 2 2 0 0 0 0-2.83Zm14.14 14.14a2 2 0 1 0 0-2.83 2 2 0 0 0 0 2.83ZM2 12a2 2 0 1 0 4 0 2 2 0 0 0-4 0Zm16 0a2 2 0 1 0 4 0 2 2 0 0 0-4 0ZM4.93 19.07a2 2 0 1 0 2.83 0 2 2 0 0 0-2.83 0Zm14.14-14.14a2 2 0 1 0-2.83 0 2 2 0 0 0 2.83 0Z"/>
            <circle cx="12" cy="12" r="2.4" fill="currentColor"/>
          </svg>`,
    light: `<svg viewBox="0 0 24 24" width="32" height="32" fill="currentColor" aria-hidden="true">
              <path d="M9 21h6v-1H9v1Zm3-19a7 7 0 0 0-4 12.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26A7 7 0 0 0 12 2Zm0 2a5 5 0 0 1 3 9.07l-.5.35.5.62V16H9v-1.96l.5-.62-.5-.35A5 5 0 0 1 12 4Z"/>
            </svg>`,
  };

  // ----------------------------------------------------------
  // State
  // ----------------------------------------------------------

  /** @type {Map<string, {status: 'on'|'off', power_draw_w: number, last_changed: string}>} */
  const deviceState = new Map();

  // Initialize all devices as OFF
  for (const room of ROOMS) {
    for (const d of room.devices) {
      deviceState.set(d.device_id, {
        status: "off",
        power_draw_w: 0,
        last_changed: null,
      });
    }
  }

  let totalWattage = 0;
  let roomWattage = { drawing_room: 0, work_room_1: 0, work_room_2: 0 };

  // ----------------------------------------------------------
  // Render — initial skeleton
  // ----------------------------------------------------------

  function renderRooms() {
    const container = document.getElementById("roomsContainer");
    container.innerHTML = "";
    for (const room of ROOMS) {
      const card = document.createElement("div");
      card.className = "room-card";
      card.innerHTML = `
        <div class="room-head">
          <h3 class="room-name">${room.name}</h3>
          <span class="room-watts" id="room-watts-${room.slug}">0 W</span>
        </div>
        <div class="devices">
          ${room.devices
            .map(
              (d) => `
            <div class="device ${d.device_type}" id="dev-${d.device_id}" data-device-id="${d.device_id}">
              <div class="icon">${ICONS[d.device_type]}</div>
              <div class="label">${d.display_name}</div>
              <div class="badge">OFF</div>
            </div>`
            )
            .join("")}
        </div>
      `;
      container.appendChild(card);
    }
  }

  // ----------------------------------------------------------
  // Apply state updates
  // ----------------------------------------------------------

  function applyDeviceUpdate(record) {
    // record: {device_id, room, device_type, status, power_draw_w, last_changed}
    if (!deviceState.has(record.device_id)) return;
    deviceState.set(record.device_id, {
      status: record.status,
      power_draw_w: record.power_draw_w,
      last_changed: record.last_changed,
    });
    paintDevice(record.device_id);
  }

  function paintDevice(deviceId) {
    const state = deviceState.get(deviceId);
    if (!state) return;
    const el = document.getElementById(`dev-${deviceId}`);
    if (!el) return;
    const isOn = state.status === "on";
    el.classList.toggle("on", isOn);
    el.querySelector(".badge").textContent = isOn ? "ON" : "OFF";
  }

  function recomputeTotals() {
    totalWattage = 0;
    roomWattage = { drawing_room: 0, work_room_1: 0, work_room_2: 0 };
    for (const [id, s] of deviceState.entries()) {
      // Find the room via the static manifest
      const room = ROOMS.find((r) => r.devices.some((d) => d.device_id === id));
      if (!room) continue;
      const w = s.status === "on" ? s.power_draw_w : 0;
      roomWattage[room.slug] += w;
      totalWattage += w;
    }
  }

  function paintTotals() {
    document.getElementById("totalWattage").textContent = totalWattage.toString();
    const onCount = [...deviceState.values()].filter((s) => s.status === "on").length;
    document.getElementById("deviceCount").textContent = `${onCount} of 15 devices ON`;

    // Bar: scale relative to theoretical max of 300 W (5 fans @ 60W if all fans on).
    // Lights @ 15W each add up to 45 more → max 345 W. Use 345 as 100%.
    const maxWatts = 345;
    const pct = Math.min(100, (totalWattage / maxWatts) * 100);
    document.getElementById("meterBar").style.width = `${pct}%`;

    for (const room of ROOMS) {
      const el = document.getElementById(`room-watts-${room.slug}`);
      if (el) el.textContent = `${roomWattage[room.slug]} W`;
    }
  }

  function applyStateDiff(diff) {
    if (!diff || !Array.isArray(diff.changes)) return;
    for (const record of diff.changes) applyDeviceUpdate(record);
    if (typeof diff.total_wattage === "number") {
      totalWattage = diff.total_wattage;
    }
    if (diff.room_wattage) {
      roomWattage = diff.room_wattage;
    }
    paintTotals();
    document.getElementById("lastUpdate").textContent = `Updated ${formatTime(new Date())}`;
  }

  // ----------------------------------------------------------
  // Alerts
  // ----------------------------------------------------------

  function pushAlert(alert) {
    const list = document.getElementById("alertsList");
    // Remove "empty" placeholder if present
    const empty = list.querySelector(".alerts-empty");
    if (empty) empty.remove();

    const severity = (alert.severity || "warning").toLowerCase();
    const li = document.createElement("li");
    li.className = `alert-item ${severity}`;
    li.innerHTML = `
      <div class="alert-head">
        <span class="alert-title">${escapeHtml(alert.alert_type || "Alert")}</span>
        <span class="alert-time">${formatTime(new Date(alert.created_at || Date.now()))}</span>
      </div>
      <div class="alert-msg">${escapeHtml(alert.message || "")}</div>
    `;
    list.insertBefore(li, list.firstChild);

    // Cap the list to the last 50 alerts
    while (list.children.length > 50) list.removeChild(list.lastChild);
  }

  document.getElementById("clearAlerts").addEventListener("click", () => {
    const list = document.getElementById("alertsList");
    list.innerHTML = `<li class="alerts-empty">No alerts. Subscribe to /ws/alerts to receive new ones in real time.</li>`;
  });

  // ----------------------------------------------------------
  // Usage
  // ----------------------------------------------------------

  async function refreshUsage() {
    try {
      const resp = await fetch(`${API_BASE}/api/usage`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const envelope = await resp.json();
      const usage = envelope.data || envelope;

      document.getElementById("usageDaily").textContent =
        (usage.daily_kwh ?? 0).toFixed(3);
      document.getElementById("usageWeekly").textContent =
        (usage.weekly_kwh ?? 0).toFixed(3);
      document.getElementById("usageMonthly").textContent =
        (usage.monthly_kwh ?? 0).toFixed(3);

      const rooms = document.getElementById("usageRooms");
      rooms.innerHTML = "";
      const list = usage.per_room || [];
      if (list.length === 0) {
        rooms.innerHTML = `<div class="usage-room"><span class="name">No usage data yet.</span><span class="kwh">—</span></div>`;
      } else {
        for (const r of list) {
          const row = document.createElement("div");
          row.className = "usage-room";
          row.innerHTML = `<span class="name">${escapeHtml(r.room_name)}</span><span class="kwh">${(r.kwh ?? 0).toFixed(3)} kWh</span>`;
          rooms.appendChild(row);
        }
      }
    } catch (err) {
      console.warn("Failed to fetch usage:", err);
    }
  }

  document.getElementById("refreshUsage").addEventListener("click", refreshUsage);

  // ----------------------------------------------------------
  // Initial state load
  // ----------------------------------------------------------

  async function loadInitialStatus() {
    try {
      const resp = await fetch(`${API_BASE}/api/status`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const envelope = await resp.json();
      const status = envelope.data || envelope;
      // Backend returns rooms with devices sorted by device_id; we mirror the
      // same order in the static ROOMS manifest, so we can match by index.
      // status.rooms: [{name, total_wattage, devices:[{name, state, wattage}]}]
      const apiRooms = status.rooms || [];
      for (const room of ROOMS) {
        const apiRoom = apiRooms.find((r) => r.name === room.name);
        if (!apiRoom) continue;
        const apiDevices = apiRoom.devices || [];
        for (let i = 0; i < room.devices.length; i++) {
          const local = room.devices[i];
          const apiDev = apiDevices[i];
          if (!apiDev) continue;
          // Match by display name to be safe against ordering drift.
          if (apiDev.name !== local.display_name) continue;
          deviceState.set(local.device_id, {
            status: String(apiDev.state).toUpperCase() === "ON" ? "on" : "off",
            power_draw_w: apiDev.wattage ?? 0,
            last_changed: null,
          });
          paintDevice(local.device_id);
        }
      }
      if (typeof status.total_wattage === "number") {
        totalWattage = status.total_wattage;
      }
      paintTotals();
    } catch (err) {
      console.warn("Failed to load initial status:", err);
    }
  }

  // ----------------------------------------------------------
  // WebSocket management with auto-reconnect
  // ----------------------------------------------------------

  function setConnectionState(state) {
    const dot = document.getElementById("wsDot");
    const label = document.getElementById("wsLabel");
    dot.classList.remove("connected", "disconnected");
    if (state === "connected") {
      dot.classList.add("connected");
      label.textContent = "Live · WebSocket connected";
    } else if (state === "disconnected") {
      dot.classList.add("disconnected");
      label.textContent = "Disconnected — retrying…";
    } else {
      label.textContent = "Connecting…";
    }
  }

  function connectWebSocket(url, onMessage, label) {
    let attempts = 0;
    let stopped = false;

    function open() {
      if (stopped) return;
      let ws;
      try {
        ws = new WebSocket(url);
      } catch (err) {
        scheduleReconnect();
        return;
      }

      ws.addEventListener("open", () => {
        attempts = 0;
        setConnectionState("connected");
        console.info(`[${label}] connected`);
      });

      ws.addEventListener("message", (ev) => {
        try {
          const data = JSON.parse(ev.data);
          onMessage(data);
        } catch (err) {
          console.warn(`[${label}] bad JSON`, err);
        }
      });

      ws.addEventListener("close", () => {
        console.info(`[${label}] closed`);
        setConnectionState("disconnected");
        scheduleReconnect();
      });

      ws.addEventListener("error", () => {
        try { ws.close(); } catch (_) {}
      });
    }

    function scheduleReconnect() {
      if (stopped) return;
      attempts++;
      const delay = Math.min(10000, 1000 * Math.pow(1.5, attempts));
      setTimeout(open, delay);
    }

    open();
    return () => { stopped = true; };
  }

  // ----------------------------------------------------------
  // Helpers
  // ----------------------------------------------------------

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function formatTime(d) {
    return d.toLocaleTimeString();
  }

  // ----------------------------------------------------------
  // Boot
  // ----------------------------------------------------------

  document.getElementById("apiUrl").textContent = API_BASE;
  renderRooms();
  paintTotals();

  loadInitialStatus().then(refreshUsage);

  connectWebSocket(WS_DASHBOARD, applyStateDiff, "dashboard");
  connectWebSocket(WS_ALERTS, pushAlert, "alerts");

  // Periodic usage refresh every 30s so kWh catches up even without new ingest.
  setInterval(refreshUsage, 30_000);
})();