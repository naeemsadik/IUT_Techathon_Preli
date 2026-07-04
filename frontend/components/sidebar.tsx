"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Gauge,
  LayoutDashboard,
  ListChecks,
  Power,
  BellRing,
  Cog,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/",            label: "Overview",  icon: LayoutDashboard },
  { href: "/rooms",       label: "Rooms",     icon: Gauge },
  { href: "/analytics",   label: "Analytics", icon: Activity },
  { href: "/usage",       label: "Usage",     icon: Power },
  { href: "/alerts",      label: "Alerts",    icon: BellRing },
  { href: "/devices",     label: "Devices",   icon: ListChecks },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r bg-background/40 backdrop-blur md:block">
      <div className="flex h-16 items-center gap-2 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Power className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold">Office Energy</div>
          <div className="text-xs text-muted-foreground">Live Monitor</div>
        </div>
      </div>
      <nav className="px-3 py-2">
        {nav.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "mt-0.5 flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="absolute inset-x-0 bottom-0 px-3 py-4">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
        >
          <Cog className="h-4 w-4" />
          Settings
        </Link>
      </div>
    </aside>
  );
}