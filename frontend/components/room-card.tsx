"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DeviceTile } from "./device-tile";
import type { RoomSpec } from "@/lib/types";
import { useLiveStore } from "@/lib/use-live-store";
import { formatWatts } from "@/lib/utils";

export function RoomCard({ room }: { room: RoomSpec }) {
  const wattage = useLiveStore((s) => s.roomWattage[room.slug] ?? 0);
  const onCount = useLiveStore((s) =>
    room.devices.filter((d) => s.devices[d.device_id]?.status === "ON").length
  );

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="text-base">{room.name}</CardTitle>
          <div className="mt-1 text-xs text-muted-foreground">
            {onCount} of {room.devices.length} devices on
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold tabular-nums text-primary">{formatWatts(wattage)}</div>
          <Badge variant={onCount > 0 ? "success" : "secondary"} className="mt-1">
            {onCount === 0 ? "Idle" : "Active"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-2">
          {room.devices.map((spec) => (
            <DeviceTile key={spec.device_id} spec={spec} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}