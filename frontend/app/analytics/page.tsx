"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { RangePicker } from "@/components/range-picker";
import { PowerByRoomChart, TotalPowerChart, DeviceUsageLines, DistributionPie, OnTimeChart } from "@/components/charts";
import { getHistory } from "@/lib/api";
import { ROOMS, type RangeKey, type HistoryResponse } from "@/lib/types";

export default function AnalyticsPage() {
  const [range, setRange] = useState<RangeKey>("24h");
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    getHistory(range)
      .then((d) => mounted && setData(d))
      .catch((e) => mounted && setError(e.message ?? "Failed to load"))
      .finally(() => mounted && setLoading(false));
    return () => { mounted = false; };
  }, [range]);

  // Derived datasets
  const totalSeries = useMemo(() => data?.totals.series ?? [], [data]);
  const stackedData = useMemo(() => {
    if (!data) return [];
    return data.totals.series.map((p, i) => {
      const row: { t: string; watts: Record<string, number> } = { t: p.t, watts: {} };
      for (const room of data.rooms) {
        row.watts[room.slug] = room.series[i]?.watts ?? 0;
      }
      return row;
    });
  }, [data]);

  const deviceOnTime = useMemo(() => {
    if (!data) return [];
    return data.devices
      .map((d) => ({
        label: d.device_id.split("_").slice(-2).join(" "),
        minutes: Math.round((d.series.reduce((s, p) => s + (p.minutes_on ?? 0), 0))),
      }))
      .sort((a, b) => b.minutes - a.minutes)
      .slice(0, 10);
  }, [data]);

  const distribution = useMemo(() => {
    if (!data) return [];
    const totals = data.rooms.map((r) => ({
      name: r.name,
      value: Math.round(r.series.reduce((s, p) => s + p.watts, 0)),
    }));
    return totals;
  }, [data]);

  const perDeviceSeries = useMemo(() => {
    if (!data) return [];
    // Show top 5 most active devices
    return data.devices
      .filter((d) => d.series.some((p) => p.watts > 0))
      .sort((a, b) => b.series.reduce((s, p) => s + p.watts, 0) - a.series.reduce((s, p) => s + p.watts, 0))
      .slice(0, 5);
  }, [data]);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Time-series insights from the {range} history log.
          </p>
        </div>
        <RangePicker value={range} onChange={setRange} />
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="p-4 text-sm text-destructive">
            Failed to load history: {error}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Total Power Draw</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[240px] w-full" /> : <TotalPowerChart data={totalSeries} />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Room Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[260px] w-full" /> : <DistributionPie data={distribution} />}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Power by Room (stacked)</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? <Skeleton className="h-[300px] w-full" /> : <PowerByRoomChart data={stackedData} />}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top 10 Devices · ON-time</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[220px] w-full" /> : <OnTimeChart data={deviceOnTime} />}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Most Active Devices · Power Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-[300px] w-full" /> : <DeviceUsageLines devices={perDeviceSeries} />}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-[100px] w-full" />
          ) : !data?.alerts.length ? (
            <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
              No alerts in this range.
            </div>
          ) : (
            <div className="space-y-2">
              {data.alerts.slice().reverse().slice(0, 10).map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-md border border-border bg-secondary/30 p-3 text-sm">
                  <div>
                    <div className="font-medium">{a.message}</div>
                    <div className="text-xs text-muted-foreground">
                      {a.alert_type} · {a.target}
                      {a.resolved_at && <span className="ml-2 text-success">resolved</span>}
                    </div>
                  </div>
                  <div className="text-right text-xs text-muted-foreground">
                    {new Date(a.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}