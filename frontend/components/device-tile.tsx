"use client";

import { useLiveStore } from "@/lib/use-live-store";
import type { DeviceSpec } from "@/lib/types";
import { cn, formatWatts } from "@/lib/utils";
import { Fan, Lightbulb } from "lucide-react";

interface DeviceTileProps {
  spec: DeviceSpec;
}

export function DeviceTile({ spec }: DeviceTileProps) {
  const state = useLiveStore((s) => s.devices[spec.device_id]);
  const on = state?.status === "ON";

  return (
    <div
      className={cn(
        "group relative flex aspect-square flex-col items-center justify-center gap-1.5 rounded-lg border p-2 transition-all",
        on
          ? "border-warning/60 bg-warning/10 shadow-[0_0_18px_-2px_hsl(var(--warning)/0.45)]"
          : "border-border bg-secondary/30"
      )}
      data-state={on ? "on" : "off"}
    >
      <div className={cn("transition-transform", on && spec.device_type === "fan" && "animate-spin-slow")}>
        {spec.device_type === "fan" ? (
          <Fan className={cn("h-7 w-7", on ? "text-warning" : "text-muted-foreground")} />
        ) : (
          <Lightbulb className={cn("h-7 w-7", on ? "text-warning" : "text-muted-foreground", on && "animate-pulse-glow [--tw-shadow-color:hsl(var(--warning)/0.7)]")} />
        )}
      </div>
      <div className="text-center text-[10px] font-medium leading-tight text-foreground">
        {spec.display_name}
      </div>
      <div className={cn(
        "rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider",
        on ? "bg-warning/20 text-warning" : "bg-muted text-muted-foreground"
      )}>
        {on ? "ON" : "OFF"}
      </div>
      <div className="absolute right-1 top-1 text-[9px] tabular-nums text-muted-foreground">
        {formatWatts(state?.power_draw_w ?? 0)}
      </div>
    </div>
  );
}