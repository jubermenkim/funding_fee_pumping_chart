import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import coins, charts

app = FastAPI(title="Funding Fee Pumping Chart API", version="1.0.0")

# CORS 설정: 환경 변수에서 허용된 origins 읽기
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")
allow_origins = [origin.strip() for origin in allow_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(coins.router, prefix="/api")
app.include_router(charts.router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
