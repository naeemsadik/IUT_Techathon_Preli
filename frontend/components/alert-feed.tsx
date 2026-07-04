"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BellRing, Trash2 } from "lucide-react";
import { useAlertSocket } from "@/lib/use-live-store";
import { formatRelativeTime } from "@/lib/utils";
import type { LiveAlert } from "@/lib/types";

export function AlertFeed({ limit = 8 }: { limit?: number }) {
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);

  useAlertSocket((alert) => {
    setAlerts((prev) => [alert, ...prev].slice(0, 50));
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div className="flex items-center gap-2">
          <BellRing className="h-4 w-4 text-warning" />
          <CardTitle className="text-base">Live Alerts</CardTitle>
          {alerts.length > 0 && (
            <Badge variant="warning">{alerts.length}</Badge>
          )}
        </div>
        <Button variant="ghost" size="sm" onClick={() => setAlerts([])} disabled={alerts.length === 0}>
          <Trash2 className="h-3.5 w-3.5" />
          Clear
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {alerts.length === 0 ? (
          <div className="rounded-md border border-dashed bg-secondary/30 p-6 text-center text-sm text-muted-foreground">
            No alerts yet. Subscribe to <code className="rounded bg-muted px-1">/ws/alerts</code> — events appear here live.
          </div>
        ) : (
          alerts.slice(0, limit).map((a) => (
            <div key={a.id} className="rounded-md border border-warning/30 bg-warning/5 p-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-warning">{a.severity.toUpperCase()}</span>
                <span className="text-muted-foreground">{formatRelativeTime(a.created_at)}</span>
              </div>
              <div className="mt-1 text-sm">{a.message}</div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}