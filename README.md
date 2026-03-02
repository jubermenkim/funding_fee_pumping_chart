# Funding Fee Pumping Chart

바이낸스 선물 코인의 펀딩피 차트 웹사이트입니다.

## 기능

- **Chart 1**: 역대 펀딩피가 가장 높았던 TOP 5 (8h 기준 환산)
- **Chart 2**: 24h 상승률이 가장 높았던 TOP 5 날짜의 펀딩피 (8h 기준 환산)
- 모든 코인의 펀딩피를 8h 기준으로 자동 환산 (1h/4h/8h 모두 지원)

## 실행 방법

### 1. 백엔드 (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드 (Next.js)

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 http://localhost:3000 접속

## 프로젝트 구조

```
funding_fee_pumping_chart/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── coins.py         # GET /api/coins
│   │   └── charts.py        # GET /api/charts/{symbol}
│   └── services/
│       ├── binance_client.py
│       ├── funding_service.py
│       └── price_service.py
├── frontend/
│   └── src/
│       ├── app/page.tsx
│       ├── components/
│       │   ├── CoinSelector.tsx
│       │   ├── FundingFeeChart.tsx
│       │   └── PriceRiseChart.tsx
│       └── lib/api.ts
└── README.md
```

## API 엔드포인트

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/coins` | USDT-M 무기한 선물 코인 목록 |
| `GET /api/charts/{symbol}` | 해당 코인의 차트 데이터 (top5Funding, top5PriceSurge) |
