"use client";

import { useLiveStore } from "@/lib/use-live-store";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff, Activity } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

export function TopBar() {
  const connected = useLiveStore((s) => s.connected);
  const lastUpdate = useLiveStore((s) => s.lastUpdate);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/60 px-4 backdrop-blur md:px-6">
      <div className="flex items-center gap-2 md:hidden">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Activity className="h-5 w-5" />
        </div>
        <span className="text-sm font-semibold">Office Energy</span>
      </div>
      <div className="hidden md:block">
        <h1 className="text-sm font-medium text-muted-foreground">
          Live office power and energy across 3 rooms · 15 devices
        </h1>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant={connected ? "success" : "destructive"} className="gap-1.5">
          {connected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
          {connected ? "Live" : "Reconnecting"}
        </Badge>
        {lastUpdate && (
          <span className="hidden text-xs text-muted-foreground md:inline">
            Updated {formatRelativeTime(lastUpdate)}
          </span>
        )}
      </div>
    </header>
  );
}