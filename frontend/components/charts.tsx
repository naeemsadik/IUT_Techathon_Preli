"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const chartTheme = {
  grid: "hsl(222 25% 22%)",
  axis: "hsl(215 20% 70%)",
  series: ["hsl(188 95% 60%)", "hsl(258 90% 65%)", "hsl(142 70% 50%)", "hsl(38 95% 55%)", "hsl(330 80% 60%)"],
};

const tooltipStyle = {
  contentStyle: {
    background: "hsl(222 35% 10%)",
    border: "1px solid hsl(222 25% 22%)",
    borderRadius: 8,
    fontSize: 12,
  },
  itemStyle: { color: "hsl(210 40% 98%)" },
  labelStyle: { color: "hsl(215 20% 70%)" },
};

function formatTick(t: string): string {
  const d = new Date(t);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Stack each room's wattage into stacked area.
export function PowerByRoomChart({ data }: { data: { t: string; watts: Record<string, number> }[] }) {
  if (!data?.length) return <EmptyChart label="No data yet" />;
  const rooms = Object.keys(data[0].watts || {});
  const rows = data.map((p) => ({ t: p.t, ...p.watts }));
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={rows} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
        <defs>
          {rooms.map((slug, i) => (
            <linearGradient key={slug} id={`grad-${slug}`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor={chartTheme.series[i % chartTheme.series.length]} stopOpacity={0.5} />
              <stop offset="95%" stopColor={chartTheme.series[i % chartTheme.series.length]} stopOpacity={0.05} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="t" tickFormatter={formatTick} stroke={chartTheme.axis} fontSize={11} />
        <YAxis stroke={chartTheme.axis} fontSize={11} width={40} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {rooms.map((slug, i) => (
          <Area
            key={slug}
            type="monotone"
            dataKey={slug}
            stackId="1"
            stroke={chartTheme.series[i % chartTheme.series.length]}
            fill={`url(#grad-${slug})`}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function TotalPowerChart({ data }: { data: { t: string; watts: number }[] }) {
  if (!data?.length) return <EmptyChart label="No data yet" />;
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
        <defs>
          <linearGradient id="gradTotal" x1="0" x2="0" y1="0" y2="1">
            <stop offset="5%" stopColor="hsl(188 95% 60%)" stopOpacity={0.6} />
            <stop offset="95%" stopColor="hsl(188 95% 60%)" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="t" tickFormatter={formatTick} stroke={chartTheme.axis} fontSize={11} />
        <YAxis stroke={chartTheme.axis} fontSize={11} width={40} />
        <Tooltip {...tooltipStyle} />
        <Area type="monotone" dataKey="watts" stroke="hsl(188 95% 60%)" strokeWidth={2} fill="url(#gradTotal)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function UsageBarChart({ data, labelKey = "room_name", valueKey = "kwh" }: { data: any[]; labelKey?: string; valueKey?: string }) {
  if (!data?.length) return <EmptyChart label="No usage data" />;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey={labelKey} stroke={chartTheme.axis} fontSize={11} />
        <YAxis stroke={chartTheme.axis} fontSize={11} width={50} />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey={valueKey} radius={[6, 6, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={chartTheme.series[i % chartTheme.series.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function OnTimeChart({ data }: { data: { label: string; minutes: number }[] }) {
  if (!data?.length) return <EmptyChart label="No on-time data" />;
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" stroke={chartTheme.axis} fontSize={11} />
        <YAxis stroke={chartTheme.axis} fontSize={11} width={40} unit="m" />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="minutes" radius={[6, 6, 0, 0]} fill="hsl(258 90% 65%)" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DistributionPie({ data }: { data: { name: string; value: number }[] }) {
  if (!data?.length) return <EmptyChart label="No breakdown" />;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
          nameKey="name"
          stroke="hsl(222 47% 6%)"
        >
          {data.map((_, i) => (
            <Cell key={i} fill={chartTheme.series[i % chartTheme.series.length]} />
          ))}
        </Pie>
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function DeviceUsageLines({ devices }: { devices: { device_id: string; series: { t: string; watts: number }[] }[] }) {
  if (!devices?.length) return <EmptyChart label="No device history yet" />;
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="t"
          type="category"
          allowDuplicatedCategory={false}
          tickFormatter={formatTick}
          stroke={chartTheme.axis}
          fontSize={11}
          ticks={devices[0].series.filter((_, i) => i % Math.ceil(devices[0].series.length / 12) === 0).map((p) => p.t)}
        />
        <YAxis stroke={chartTheme.axis} fontSize={11} width={40} />
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {devices.map((d, i) => (
          <Line
            key={d.device_id}
            data={d.series}
            type="monotone"
            dataKey="watts"
            name={d.device_id}
            stroke={chartTheme.series[i % chartTheme.series.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed text-sm text-muted-foreground">
      {label}
    </div>
  );
}