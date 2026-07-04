"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { API_BASE } from "@/lib/api";
import { Cog, Server, Globe, Zap } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Read-only deployment info. Edit environment variables on the host.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0">
            <Server className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">Backend connection</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Row label="API base URL" value={API_BASE} mono />
            <Row label="Status" value={<Badge variant="success">Configured</Badge>} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center gap-2 space-y-0">
            <Globe className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">Deployment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <Row label="Frontend host" value={typeof window !== "undefined" ? window.location.host : "—"} />
            <Row label="Frontend env" value={process.env.NODE_ENV ?? "—"} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center gap-2 space-y-0">
            <Zap className="h-4 w-4 text-primary" />
            <CardTitle className="text-base">About</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>
              Office Energy Monitor - Next.js 14 frontend backed by a FastAPI service.
              All device state flows through <code className="rounded bg-muted px-1">POST /api/ingest</code>;
              live updates fan out via <code className="rounded bg-muted px-1">/ws/live</code> and{" "}
              <code className="rounded bg-muted px-1">/ws/alerts</code>.
            </p>
            <p>
              See <code className="rounded bg-muted px-1">doc/DEPLOYMENT.md</code> for the
              production deployment guide (Coolify + Vercel).
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border py-2 last:border-b-0">
      <span className="text-muted-foreground">{label}</span>
      <span className={mono ? "font-mono text-xs" : ""}>{value}</span>
    </div>
  );
}
