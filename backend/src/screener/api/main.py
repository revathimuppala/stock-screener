from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from screener.api.routers.backtest import router as backtest_router
from screener.api.routers.saved_screens import router as saved_screens_router
from screener.api.routers.screener import router as screener_router
from screener.api.routers.watchlist import router as watchlist_router

app = FastAPI(title="Stock Screener API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screener_router)
app.include_router(watchlist_router)
app.include_router(saved_screens_router)
app.include_router(backtest_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
