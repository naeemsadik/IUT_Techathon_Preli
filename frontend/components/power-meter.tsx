"use client";

import { Card, CardContent } from "@/components/ui/card";
import { useLiveStore } from "@/lib/use-live-store";
import { formatWatts } from "@/lib/utils";
import { Activity } from "lucide-react";

export function PowerMeter() {
  const total = useLiveStore((s) => s.totalWattage);
  // Theoretical max: 6 fans @ 60W + 9 lights @ 15W = 360 + 135 = 495W
  const max = 495;
  const pct = Math.min(100, (total / max) * 100);

  return (
    <Card className="overflow-hidden">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Total Office Load</div>
            <div className="mt-1 flex items-baseline gap-2">
              <div className="bg-gradient-to-br from-primary to-accent bg-clip-text text-5xl font-extrabold tabular-nums text-transparent">
                {total}
              </div>
              <span className="text-lg text-muted-foreground">W</span>
            </div>
            <div className="mt-1 text-xs text-muted-foreground">
              {pct.toFixed(0)}% of theoretical max · cap {max} W
            </div>
          </div>
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Activity className="h-7 w-7" />
          </div>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full rounded-full bg-gradient-to-r from-success via-warning to-destructive transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <span>0 W</span>
          <span>{Math.round(max / 2)} W</span>
          <span>{max} W</span>
        </div>
      </CardContent>
    </Card>
  );
}