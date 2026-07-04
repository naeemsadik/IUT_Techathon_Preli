"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { RangeKey } from "@/lib/types";

interface RangePickerProps {
  value: RangeKey;
  onChange: (v: RangeKey) => void;
}

const RANGES: { label: string; value: RangeKey }[] = [
  { label: "1H",  value: "1h" },
  { label: "24H", value: "24h" },
  { label: "7D",  value: "7d" },
  { label: "30D", value: "30d" },
];

export function RangePicker({ value, onChange }: RangePickerProps) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as RangeKey)}>
      <TabsList>
        {RANGES.map((r) => (
          <TabsTrigger key={r.value} value={r.value}>{r.label}</TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}