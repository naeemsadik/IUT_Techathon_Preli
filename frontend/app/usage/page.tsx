"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { KpiCard } from "@/components/kpi-card";
import { UsageBarChart } from "@/components/charts";
import { getUsage } from "@/lib/api";
import { formatKwh } from "@/lib/utils";
import { Power, Calendar, BarChart3 } from "lucide-react";

export default function UsagePage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getUsage>> | null>(null);

  useEffect(() => {
    let mounted = true;
    function load() {
      getUsage().then((d) => mounted && setData(d)).catch(() => {});
    }
    load();
    const id = setInterval(load, 30_000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Energy Usage</h1>
        <p className="text-sm text-muted-foreground">
          kWh consumed — daily, weekly, and monthly — plus per-room breakdown.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard label="Today"      value={data ? data.daily_kwh.toFixed(3)  : "—"} unit="kWh" icon={Power} />
        <KpiCard label="Last 7 days" value={data ? data.weekly_kwh.toFixed(3) : "—"} unit="kWh" icon={Calendar} />
        <KpiCard label="This month" value={data ? data.monthly_kwh.toFixed(3) : "—"} unit="kWh" icon={BarChart3} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Per-room consumption (today, kWh)</CardTitle>
        </CardHeader>
        <CardContent>
          <UsageBarChart data={data?.per_room ?? []} labelKey="room_name" valueKey="kwh" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Per-room detail</CardTitle>
        </CardHeader>
        <CardContent>
          {!data?.per_room?.length ? (
            <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
              No usage data yet. Run the simulator for a few minutes and refresh.
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border">
              <table className="w-full text-sm">
                <thead className="bg-secondary/40 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="p-3">Room</th>
                    <th className="p-3 text-right">kWh today</th>
                    <th className="p-3 text-right">Share</th>
                  </tr>
                </thead>
                <tbody>
                  {data.per_room.map((r) => {
                    const total = data.daily_kwh || 1;
                    const pct = ((r.kwh / total) * 100).toFixed(1);
                    return (
                      <tr key={r.room_name} className="border-t">
                        <td className="p-3 font-medium">{r.room_name}</td>
                        <td className="p-3 text-right tabular-nums">{r.kwh.toFixed(3)}</td>
                        <td className="p-3 text-right tabular-nums text-muted-foreground">{pct}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}