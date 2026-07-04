"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  description?: string;
  icon: LucideIcon;
  accent?: "primary" | "success" | "warning" | "destructive";
  loading?: boolean;
}

const accentMap = {
  primary:     { bg: "bg-primary/10",     text: "text-primary" },
  success:     { bg: "bg-success/10",     text: "text-success" },
  warning:     { bg: "bg-warning/10",     text: "text-warning" },
  destructive: { bg: "bg-destructive/10", text: "text-destructive" },
};

export function KpiCard({ label, value, unit, description, icon: Icon, accent = "primary", loading }: KpiCardProps) {
  const a = accentMap[accent];
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
          {loading ? (
            <div className="h-8 w-24 animate-pulse rounded-md bg-muted" />
          ) : (
            <div className="flex items-baseline gap-1.5">
              <div className="text-3xl font-bold tabular-nums">{value}</div>
              {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
            </div>
          )}
          {description && (
            <div className="text-xs text-muted-foreground">{description}</div>
          )}
        </div>
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl", a.bg)}>
          <Icon className={cn("h-6 w-6", a.text)} />
        </div>
      </CardContent>
    </Card>
  );
}