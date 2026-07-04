// =============================================================================
//  Shared types — mirror the backend Pydantic models and the /api/history
//  shape produced by iut_server/app/api/history.py.
// =============================================================================

export type DeviceState = "ON" | "OFF";
export type DeviceType = "fan" | "light";
export type Severity = "warning" | "info" | "critical";

export interface Device {
  name: string;
  state: DeviceState;
  wattage: number;
}

export interface Room {
  name: string;
  devices: Device[];
  total_wattage: number;
}

export interface OfficeStatus {
  office_status: string;
  total_wattage: number;
  rooms: Room[];
}

export interface RoomUsage {
  room_name: string;
  kwh: number;
}

export interface Usage {
  daily_kwh: number;
  weekly_kwh: number;
  monthly_kwh: number;
  per_room: RoomUsage[];
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message?: string | null;
}

export type RangeKey = "1h" | "24h" | "7d" | "30d";

// ---- /api/history payload ----

export interface HistoryPoint {
  t: string; // ISO 8601 UTC
  watts: number;
  on_count?: number;
  minutes_on?: number;
}

export interface RoomHistory {
  slug: string;
  name: string;
  series: HistoryPoint[];
}

export interface DeviceHistory {
  device_id: string;
  room: string;
  device_type: DeviceType;
  series: HistoryPoint[];
}

export interface AlertEntry {
  id: string;
  alert_type: string;
  target: string;
  message: string;
  severity: Severity;
  created_at: string;
  resolved_at: string | null;
}

export interface HistoryResponse {
  range: RangeKey;
  bucket_minutes: number;
  since: string;
  now: string;
  rooms: RoomHistory[];
  devices: DeviceHistory[];
  totals: { series: { t: string; watts: number }[] };
  alerts: AlertEntry[];
}

// ---- Live state push ----

export interface StateDiff {
  message_type: "state_diff";
  server_time: string;
  changes: {
    device_id: string;
    room: string;
    device_type: DeviceType;
    status: "on" | "off";
    power_draw_w: number;
    last_changed: string;
  }[];
  total_wattage: number;
  room_wattage: Record<string, number>;
}

export interface LiveAlert {
  id: string;
  message: string;
  severity: Severity;
  created_at: string;
}

// ---- Device manifest (mirrors iut_server/app/state.py) ----

export interface DeviceSpec {
  device_id: string;
  room: string;
  device_type: DeviceType;
  display_name: string;
}

export interface RoomSpec {
  slug: string;
  name: string;
  devices: DeviceSpec[];
}

export const ROOMS: RoomSpec[] = [
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

export function findDeviceSpec(deviceId: string): { spec: DeviceSpec; room: RoomSpec } | null {
  for (const room of ROOMS) {
    const spec = room.devices.find((d) => d.device_id === deviceId);
    if (spec) return { spec, room };
  }
  return null;
}