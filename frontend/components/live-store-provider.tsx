"use client";

import { useEffect } from "react";
import { useLiveStateSocket } from "@/lib/use-live-store";
import { getStatus } from "@/lib/api";
import { useLiveStore } from "@/lib/use-live-store";
import { ROOMS } from "@/lib/types";

export function LiveStoreProvider({ children }: { children: React.ReactNode }) {
  const seedFromStatus = useLiveStore((s) => s.seedFromStatus);
  const setConnected = useLiveStore((s) => s.setConnected);

  // Establish the WebSocket once at app start.
  useLiveStateSocket();

  // Initial REST seed — load /api/status, then refresh every 30s as a safety net.
  useEffect(() => {
    let cancelled = false;
    async function seed() {
      try {
        const status = await getStatus();
        if (!cancelled) seedFromStatus(status.rooms);
      } catch {
        setConnected(false);
      }
    }
    seed();
    const id = setInterval(seed, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, [seedFromStatus, setConnected]);

  return <>{children}</>;
}
