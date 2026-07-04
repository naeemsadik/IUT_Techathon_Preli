"use client";

import { useEffect, useState } from "react";
import { Zap, AlertTriangle, Activity, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KpiCard } from "@/components/kpi-card";
import { PowerMeter } from "@/components/power-meter";
import { RoomCard } from "@/components/room-card";
import { AlertFeed } from "@/components/alert-feed";
import { ROOMS } from "@/lib/types";
import { useLiveStore } from "@/lib/use-live-store";
import { getUsage } from "@/lib/api";
import { formatKwh, formatRelativeTime } from "@/lib/utils";

export default function OverviewPage() {
  const devices = useLiveStore((s) => s.devices);
  const lastUpdate = useLiveStore((s) => s.lastUpdate);
  const [usage, setUsage] = useState<Awaited<ReturnType<typeof getUsage>> | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const u = await getUsage();
        if (mounted) setUsage(u);
      } catch { /* */ }
    }
    load();
    const id = setInterval(load, 30_000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  const onCount = Object.values(devices).filter((d) => d.status === "ON").length;
  const peakRoom = ROOMS.map((r) => ({
    name: r.name,
    watts: useLiveStore.getState().roomWattage[r.slug] ?? 0,
  })).sort((a, b) => b.watts - a.watts)[0];

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Overview</h1>
          <p className="text-sm text-muted-foreground">
            Real-time power across all 3 rooms · 15 devices ·{" "}
            {lastUpdate ? formatRelativeTime(lastUpdate) : "waiting for first update"}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Total Load"
          value={useLiveStore.getState().totalWattage}
          unit="W"
          icon={Zap}
          accent="primary"
        />
        <KpiCard
          label="Devices ON"
          value={`${onCount}/15`}
          icon={Activity}
          accent={onCount > 0 ? "success" : "primary"}
        />
        <KpiCard
          label="Today's kWh"
          value={usage ? usage.daily_kwh.toFixed(3) : "—"}
          icon={Clock}
          accent="primary"
        />
        <KpiCard
          label="Active Alerts"
          value={0}
          description="(feed below)"
          icon={AlertTriangle}
          accent="warning"
        />
      </div>

      <PowerMeter />

      <div className="grid gap-4 lg:grid-cols-3">
        {ROOMS.map((room) => (
          <RoomCard key={room.slug} room={room} />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AlertFeed limit={5} />
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Heaviest Room Right Now</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-3xl font-bold">{peakRoom?.name ?? "—"}</div>
            <div className="text-sm text-muted-foreground">{peakRoom?.watts ?? 0} W being drawn</div>
            <div className="mt-4 text-xs text-muted-foreground">
              {usage?.per_room?.length
                ? `Today: ${usage.per_room.map((r) => `${r.room_name} ${r.kwh.toFixed(2)} kWh`).join(" · ")}`
                : "No usage data yet."}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}