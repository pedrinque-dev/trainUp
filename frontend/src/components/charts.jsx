import { Area, Bar, BarChart, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dayLong, dayShort, num } from "../lib/format";

const axis = { fontSize: 12, fill: "#5B6B80" };
const tip = { borderRadius: 12, border: "1px solid #DDE4EE", fontSize: 12 };

const defs = (
  <defs>
    <linearGradient id="gArea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#5FC28A" stopOpacity="0.35" /><stop offset="100%" stopColor="#5FC28A" stopOpacity="0" />
    </linearGradient>
    <linearGradient id="gBar" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#9BD64A" /><stop offset="100%" stopColor="#5FC28A" />
    </linearGradient>
  </defs>
);

/** Evolução de carga (máxima e média por sessão). points: [{date:"YYYY-MM-DD", max_load, avg_load}] */
export function LoadChart({ points, height = 260 }) {
  return (
    <div style={{ height }} role="img" aria-label="Gráfico de evolução de carga por sessão">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={points} margin={{ left: -8, right: 8, top: 8 }}>
          {defs}
          <CartesianGrid stroke="#DDE4EE" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="date" tickFormatter={dayShort} tick={axis} tickLine={false} axisLine={false} minTickGap={24} />
          <YAxis tick={axis} tickLine={false} axisLine={false} unit=" kg" width={58}
            domain={[(min) => Math.max(0, Math.floor(min - 5)), (max) => Math.ceil(max + 5)]} />
          <Tooltip contentStyle={tip} labelFormatter={dayLong} formatter={(v, n) => [`${num(v)} kg`, n]} />
          <Area type="monotone" dataKey="max_load" name="Carga máxima" stroke="#0B8FDB" strokeWidth={3}
            fill="url(#gArea)" dot={{ r: 3, fill: "#0B8FDB" }} />
          <Line type="monotone" dataKey="avg_load" name="Carga média" stroke="#5B6B80" strokeWidth={1.5}
            strokeDasharray="4 4" dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Volume semanal. data: [{week:"YYYY-MM-DD", volume}] */
/** Volume semanal. data: [{week:"YYYY-MM-DD", volume}] */
export function VolumeChart({ data, height = 220 }) {
  return (
    <div style={{ height }} role="img" aria-label="Gráfico de volume semanal de treino">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: -4, right: 8, top: 8 }}>
          {defs}
          <CartesianGrid stroke="#DDE4EE" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="week" tickFormatter={dayShort} tick={axis} tickLine={false} axisLine={false} minTickGap={20} />
          <YAxis tick={axis} tickLine={false} axisLine={false} width={52} tickFormatter={(v) => (v >= 1000 ? `${num(v / 1000)}k` : v)} />
          <Tooltip contentStyle={tip} labelFormatter={(d) => `Semana de ${dayLong(d)}`} formatter={(v) => [`${num(v, 0)} kg`, "Volume"]} cursor={{ fill: "#F3F6FA" }} />
          <Bar dataKey="volume" name="Volume" fill="#5FC28A" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
