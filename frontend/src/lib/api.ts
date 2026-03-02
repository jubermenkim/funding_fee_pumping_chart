const rawBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BASE = rawBase.replace(/\/+$/, "").replace(/\/api$/, "");

export interface FundingRecord {
  time: string;
  timestamp: number;
  rawRate: number;
  normalizedRate8h: number;
  markPrice: number;
  intervalHours: number;
  changePct: number | null;
}

export interface PriceSurgeRecord {
  date: string;
  changePct: number;
  fundingTime: number;
  rawRate: number;
  normalizedRate8h: number;
  intervalHours: number;
}

export interface ChartData {
  symbol: string;
  top5Funding: FundingRecord[];
  top5PriceSurge: PriceSurgeRecord[];
}

export async function fetchCoins(): Promise<string[]> {
  const res = await fetch(`${BASE}/api/coins`);
  if (!res.ok) throw new Error("Failed to fetch coin list");
  const data = await res.json();
  return data.symbols as string[];
}

export async function fetchChartData(symbol: string): Promise<ChartData> {
  const res = await fetch(`${BASE}/api/charts/${symbol}`);
  if (!res.ok) throw new Error(`Failed to fetch chart data for ${symbol}`);
  return res.json();
}
