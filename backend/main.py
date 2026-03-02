from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import coins, charts

app = FastAPI(title="Funding Fee Pumping Chart API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
