"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RoomCard } from "@/components/room-card";
import { getRoom } from "@/lib/api";
import { ROOMS } from "@/lib/types";
import type { Room } from "@/lib/types";
import { formatWatts } from "@/lib/utils";

export default function RoomsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Rooms</h1>
        <p className="text-sm text-muted-foreground">
          Detailed device state for each of the three rooms. Click a room for breakdown.
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {ROOMS.map((room) => (
          <RoomDetail key={room.slug} slug={room.slug} name={room.name} />
        ))}
      </div>
    </div>
  );
}

function RoomDetail({ slug, name }: { slug: string; name: string }) {
  const [detail, setDetail] = useState<Room | null>(null);
  useEffect(() => {
    let mounted = true;
    getRoom(slug)
      .then((r) => mounted && setDetail(r))
      .catch(() => {});
    return () => { mounted = false; };
  }, [slug]);

  return (
    <RoomCard room={ROOMS.find((r) => r.slug === slug)!} />
  );
}