// =============================================================================
//  Live state store - single source of truth for the frontend.
//  Receives WebSocket diffs from /ws/live and falls back to REST on load.
// =============================================================================

"use client";

import { create } from "zustand";
import { ROOMS, type DeviceState, type DeviceType } from "./types";

interface DeviceRuntime {
  status: DeviceState;
  power_draw_w: number;
  last_changed: string | null;
}

interface LiveStore {
  devices: Record<string, DeviceRuntime>;
  totalWattage: number;
  roomWattage: Record<string, number>;
  connected: boolean;
  lastUpdate: string | null;
  ingest: (diff: {
    changes: {
      device_id: string;
      status: "on" | "off";
      power_draw_w: number;
      last_changed: string;
      room: string;
      device_type: DeviceType;
    }[];
    total_wattage: number;
    room_wattage: Record<string, number>;
    server_time: string;
  }) => void;
  seedFromStatus: (rooms: { name: string; devices: { name: string; state: DeviceState; wattage: number }[]; total_wattage: number }[]) => void;
  setConnected: (v: boolean) => void;
}

function emptyDevices(): Record<string, DeviceRuntime> {
  const map: Record<string, DeviceRuntime> = {};
  for (const room of ROOMS) {
    for (const d of room.devices) {
      map[d.device_id] = { status: "OFF", power_draw_w: 0, last_changed: null };
    }
  }
  return map;
}

function emptyRoomWattage(): Record<string, number> {
  return Object.fromEntries(ROOMS.map((r) => [r.slug, 0]));
}

export const useLiveStore = create<LiveStore>((set) => ({
  devices: emptyDevices(),
  totalWattage: 0,
  roomWattage: emptyRoomWattage(),
  connected: false,
  lastUpdate: null,
  ingest: (diff) =>
    set((state) => {
      const devices = { ...state.devices };
      for (const c of diff.changes) {
        devices[c.device_id] = {
          status: c.status === "on" ? "ON" : "OFF",
          power_draw_w: c.power_draw_w,
          last_changed: c.last_changed,
        };
      }
      return {
        devices,
        totalWattage: diff.total_wattage ?? state.totalWattage,
        roomWattage: diff.room_wattage ?? state.roomWattage,
        lastUpdate: diff.server_time,
      };
    }),
  seedFromStatus: (rooms) =>
    set((state) => {
      const devices = { ...state.devices };
      const roomWattage: Record<string, number> = {};
      for (const room of ROOMS) {
        const apiRoom = rooms.find((r) => r.name === room.name);
        if (!apiRoom) {
          roomWattage[room.slug] = state.roomWattage[room.slug] ?? 0;
          continue;
        }
        roomWattage[room.slug] = apiRoom.total_wattage;
        for (const apiDev of apiRoom.devices) {
          const local = room.devices.find((d) => d.display_name === apiDev.name);
          if (!local) continue;
          devices[local.device_id] = {
            status: apiDev.state,
            power_draw_w: apiDev.wattage,
            last_changed: null,
          };
        }
      }
      const totalWattage = Object.values(roomWattage).reduce((s, w) => s + w, 0);
      return { devices, totalWattage, roomWattage, lastUpdate: new Date().toISOString() };
    }),
  setConnected: (v) => set({ connected: v }),
}));

// =============================================================================
//  WebSocket hook — auto-reconnects, fans out diffs to the store.
// =============================================================================
import { useEffect } from "react";
import type { StateDiff, LiveAlert } from "./types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL
  ?? (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/^http/, "ws");

export function useLiveStateSocket() {
  const ingest = useLiveStore((s) => s.ingest);
  const setConnected = useLiveStore((s) => s.setConnected);
  useEffect(() => {
    let ws: WebSocket | null = null;
    let attempts = 0;
    let stopped = false;

    function connect() {
      if (stopped) return;
      try {
        ws = new WebSocket(`${WS_BASE}/ws/live`);
      } catch {
        scheduleReconnect();
        return;
      }
      ws.addEventListener("open", () => {
        attempts = 0;
        setConnected(true);
      });
      ws.addEventListener("message", (ev) => {
        try {
          const msg = JSON.parse(ev.data) as StateDiff;
          if (msg.message_type === "state_diff") ingest(msg);
        } catch {
          /* ignore malformed */
        }
      });
      ws.addEventListener("close", () => {
        setConnected(false);
        scheduleReconnect();
      });
      ws.addEventListener("error", () => {
        try { ws?.close(); } catch { /* */ }
      });
    }

    function scheduleReconnect() {
      if (stopped) return;
      attempts++;
      const delay = Math.min(10000, 800 * Math.pow(1.5, attempts));
      setTimeout(connect, delay);
    }

    connect();
    return () => {
      stopped = true;
      try { ws?.close(); } catch { /* */ }
    };
  }, [ingest, setConnected]);
}

export function useAlertSocket(onAlert: (a: LiveAlert) => void) {
  useEffect(() => {
    let ws: WebSocket | null = null;
    let attempts = 0;
    let stopped = false;

    function connect() {
      if (stopped) return;
      try {
        ws = new WebSocket(`${WS_BASE}/ws/alerts`);
      } catch {
        scheduleReconnect();
        return;
      }
      ws.addEventListener("message", (ev) => {
        try {
          const msg = JSON.parse(ev.data) as LiveAlert;
          onAlert(msg);
        } catch {
          /* ignore */
        }
      });
      ws.addEventListener("close", scheduleReconnect);
      ws.addEventListener("error", () => {
        try { ws?.close(); } catch { /* */ }
      });
    }
    function scheduleReconnect() {
      if (stopped) return;
      attempts++;
      setTimeout(connect, Math.min(10000, 800 * Math.pow(1.5, attempts)));
    }

    connect();
    return () => {
      stopped = true;
      try { ws?.close(); } catch { /* */ }
    };
  }, [onAlert]);
}
