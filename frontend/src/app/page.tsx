"use client";

import { useEffect, useState, useCallback } from "react";
import CoinSelector from "@/components/CoinSelector";
import FundingFeeChart from "@/components/FundingFeeChart";
import PriceRiseChart from "@/components/PriceRiseChart";
import { fetchCoins, fetchChartData, ChartData } from "@/lib/api";

export default function Home() {
  const [coins, setCoins] = useState<string[]>([]);
  const [selected, setSelected] = useState("BTCUSDT");
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [coinsLoading, setCoinsLoading] = useState(true);

  useEffect(() => {
    fetchCoins()
      .then(setCoins)
      .catch(() => setError("코인 목록을 불러오지 못했습니다."))
      .finally(() => setCoinsLoading(false));
  }, []);

  const loadChart = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    setChartData(null);
    try {
      const data = await fetchChartData(symbol);
      setChartData(data);
    } catch {
      setError(`${symbol} 데이터를 불러오지 못했습니다. 백엔드 서버가 실행 중인지 확인하세요.`);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSelect = (symbol: string) => {
    setSelected(symbol);
    loadChart(symbol);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-yellow-400 rounded-lg flex items-center justify-center">
              <span className="text-gray-900 font-bold text-sm">FF</span>
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">
                Funding Fee Chart
              </h1>
              <p className="text-gray-500 text-xs">Binance USDT-M Perpetual Futures</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-4 mb-8">
          {coinsLoading ? (
            <div className="w-72 h-10 bg-gray-800 rounded-lg animate-pulse" />
          ) : (
            <CoinSelector coins={coins} selected={selected} onSelect={handleSelect} />
          )}
          <button
            onClick={() => loadChart(selected)}
            disabled={loading}
            className="px-5 py-2.5 bg-yellow-400 text-gray-900 font-semibold rounded-lg hover:bg-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "조회 중..." : "조회"}
          </button>
          <p className="text-gray-500 text-sm">
            * 모든 펀딩피는 8h 기준으로 환산됩니다
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="grid gap-6">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 h-72 animate-pulse" />
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 h-72 animate-pulse" />
          </div>
        )}

        {/* Charts */}
        {!loading && chartData && (
          <div className="grid gap-6">
            <FundingFeeChart data={chartData.top5Funding} symbol={chartData.symbol} />
            <PriceRiseChart data={chartData.top5PriceSurge} symbol={chartData.symbol} />
          </div>
        )}

        {/* Empty state */}
        {!loading && !chartData && !error && (
          <div className="flex flex-col items-center justify-center py-24 text-gray-600">
            <svg className="w-16 h-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-lg font-medium">코인을 선택하고 조회 버튼을 눌러주세요</p>
          </div>
        )}
      </main>
    </div>
  );
}
