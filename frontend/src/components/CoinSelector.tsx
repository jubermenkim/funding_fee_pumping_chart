"use client";

import { useState, useMemo, useRef, useEffect } from "react";

interface Props {
  coins: string[];
  selected: string;
  onSelect: (symbol: string) => void;
}

export default function CoinSelector({ coins, selected, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(
    () =>
      query.trim() === ""
        ? coins
        : coins.filter((c) => c.toLowerCase().includes(query.toLowerCase())),
    [coins, query]
  );

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={containerRef} className="relative w-72">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5 text-white hover:border-yellow-400 transition-colors"
      >
        <span className="font-medium">{selected || "코인 선택"}</span>
        <svg
          className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full bg-gray-800 border border-gray-600 rounded-lg shadow-xl">
          <div className="p-2">
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="검색..."
              className="w-full bg-gray-700 text-white placeholder-gray-400 rounded px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-yellow-400"
            />
          </div>
          <ul className="max-h-60 overflow-y-auto">
            {filtered.length === 0 && (
              <li className="px-4 py-2 text-gray-400 text-sm">결과 없음</li>
            )}
            {filtered.map((coin) => (
              <li
                key={coin}
                onClick={() => {
                  onSelect(coin);
                  setOpen(false);
                  setQuery("");
                }}
                className={`px-4 py-2 cursor-pointer text-sm transition-colors ${
                  coin === selected
                    ? "bg-yellow-400 text-gray-900 font-semibold"
                    : "text-white hover:bg-gray-700"
                }`}
              >
                {coin}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
