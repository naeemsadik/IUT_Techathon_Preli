"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { RangePicker } from "@/components/range-picker";
import { AlertFeed } from "@/components/alert-feed";
import { BellRing, CheckCircle2, AlertCircle } from "lucide-react";
import { getHistory } from "@/lib/api";
import { type AlertEntry, type RangeKey } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

export default function AlertsPage() {
  const [range, setRange] = useState<RangeKey>("24h");
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getHistory(range)
      .then((d) => mounted && setAlerts(d.alerts ?? []))
      .catch(() => {})
      .finally(() => mounted && setLoading(false));
    return () => { mounted = false; };
  }, [range]);

  const unresolved = alerts.filter((a) => !a.resolved_at);
  const resolved = alerts.filter((a) => !!a.resolved_at);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Alerts</h1>
          <p className="text-sm text-muted-foreground">
            Historical and live alerts from the engine.
          </p>
        </div>
        <RangePicker value={range} onChange={setRange} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div className="flex items-center gap-2">
              <BellRing className="h-4 w-4 text-warning" />
              <CardTitle className="text-base">Alert History ({range})</CardTitle>
            </div>
            <div className="flex gap-2">
              <Badge variant="destructive">{unresolved.length} unresolved</Badge>
              <Badge variant="success">{resolved.length} resolved</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : alerts.length === 0 ? (
              <div className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
                No alerts fired in this range.
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border">
                <table className="w-full text-sm">
                  <thead className="bg-secondary/40 text-left text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="p-3">Time</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Target</th>
                      <th className="p-3">Message</th>
                      <th className="p-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.slice().reverse().map((a) => (
                      <tr key={a.id} className="border-t">
                        <td className="p-3 text-xs text-muted-foreground whitespace-nowrap">
                          {formatRelativeTime(a.created_at)}
                        </td>
                        <td className="p-3 font-mono text-xs">{a.alert_type}</td>
                        <td className="p-3 font-mono text-xs">{a.target}</td>
                        <td className="p-3">{a.message}</td>
                        <td className="p-3 text-right">
                          {a.resolved_at ? (
                            <Badge variant="success" className="gap-1">
                              <CheckCircle2 className="h-3 w-3" />
                              Resolved
                            </Badge>
                          ) : (
                            <Badge variant="destructive" className="gap-1">
                              <AlertCircle className="h-3 w-3" />
                              Open
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <AlertFeed limit={12} />
      </div>
    </div>
  );
}