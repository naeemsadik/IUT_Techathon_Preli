"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DeviceTile } from "@/components/device-tile";
import { ROOMS } from "@/lib/types";
import { useLiveStore } from "@/lib/use-live-store";
import { Cpu, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export default function DevicesPage() {
  const devices = useLiveStore((s) => s.devices);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "on" | "off" | "fan" | "light">("all");

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return ROOMS.flatMap((r) =>
      r.devices
        .filter((d) => {
          const state = devices[d.device_id];
          if (!state) return false;
          if (filter === "on" && state.status !== "ON") return false;
          if (filter === "off" && state.status !== "OFF") return false;
          if (filter === "fan" && d.device_type !== "fan") return false;
          if (filter === "light" && d.device_type !== "light") return false;
          if (q && !d.device_id.toLowerCase().includes(q) && !d.display_name.toLowerCase().includes(q)) return false;
          return true;
        })
        .map((d) => ({ ...d, roomName: r.name }))
    );
  }, [devices, query, filter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Devices</h1>
        <p className="text-sm text-muted-foreground">
          All 15 devices — search, filter, and inspect live state.
        </p>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search device id or name"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-64 pl-8"
            />
          </div>
          <div className="flex gap-2">
            {(["all", "on", "off", "fan", "light"] as const).map((f) => (
              <Badge
                key={f}
                variant={filter === f ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setFilter(f)}
              >
                {f.toUpperCase()}
              </Badge>
            ))}
          </div>
          <div className="ml-auto text-sm text-muted-foreground">
            Showing {filtered.length} device{filtered.length === 1 ? "" : "s"}
          </div>
        </CardContent>
      </Card>

      {!devices ? (
        <Skeleton className="h-32 w-full" />
      ) : (
        <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-5">
          {filtered.map((d) => (
            <div key={d.device_id} className="space-y-1">
              <DeviceTile spec={d} />
              <div className="text-center text-[10px] text-muted-foreground">
                {d.roomName} · <span className="font-mono">{d.device_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}