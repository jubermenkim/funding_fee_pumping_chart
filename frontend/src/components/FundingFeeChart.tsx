"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { FundingRecord } from "@/lib/api";

interface Props {
  data: FundingRecord[];
  symbol: string;
}

interface TooltipPayload {
  payload: FundingRecord & { label: string };
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-gray-900 border border-gray-600 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-yellow-400 font-semibold mb-1">{d.time}</p>
      <p className="text-white">
        8h 표준화 펀딩피:{" "}
        <span className={d.normalizedRate8h >= 0 ? "text-green-400" : "text-red-400"}>
          {d.normalizedRate8h.toFixed(4)}%
        </span>
      </p>
      <p className="text-gray-400">
        원본 펀딩피: {d.rawRate.toFixed(4)}% ({d.intervalHours}h 기준)
      </p>
      {d.markPrice > 0 && (
        <p className="text-gray-400">마크 가격: ${d.markPrice.toFixed(4)}</p>
      )}
      {d.changePct != null && (
        <p className="text-white">
          24h 상승률:{" "}
          <span className={d.changePct >= 0 ? "text-green-400" : "text-red-400"}>
            {d.changePct >= 0 ? "+" : ""}{d.changePct.toFixed(2)}%
          </span>
        </p>
      )}
    </div>
  );
}

export default function FundingFeeChart({ data, symbol }: Props) {
  const chartData = data.map((d, i) => ({
    ...d,
    label: `#${i + 1}\n${d.time.slice(5)}`,
    shortTime: d.time.slice(5, 13),
  }));

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-white">
          Chart 1 — 펀딩피 TOP 5
        </h2>
        <p className="text-gray-400 text-sm mt-0.5">
          {symbol} · 8h 기준 환산 · 역대 가장 낮은 펀딩피 5개
        </p>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="shortTime"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            tickFormatter={(v: number) => `${v.toFixed(3)}%`}
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
            width={70}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
          <ReferenceLine y={0} stroke="#6B7280" />
          <Bar dataKey="normalizedRate8h" radius={[4, 4, 0, 0]} maxBarSize={60}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.normalizedRate8h >= 0 ? "#F59E0B" : "#EF4444"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-5 gap-2">
        {data.map((d, i) => (
          <div key={i} className="bg-gray-700 rounded-lg p-2 text-center">
            <div className="text-yellow-400 text-xs font-bold">#{i + 1}</div>
            <div
              className={`text-sm font-semibold mt-0.5 ${
                d.normalizedRate8h >= 0 ? "text-green-400" : "text-red-400"
              }`}
            >
              {d.normalizedRate8h.toFixed(4)}%
            </div>
            <div className="text-gray-400 text-xs mt-0.5">{d.time.slice(5, 13)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
