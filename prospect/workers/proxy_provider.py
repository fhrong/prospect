from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from workers.proxy_service import (
    get_best_proxies,
    mark_proxy_bad,
)
#uvicorn workers.proxy_provider:app --reload --host 0.0.0.0 --port 8000

router = APIRouter()


class ProxyReport(BaseModel):
    proxy: str


@router.get("/proxy/best")
def get_best_proxy():

    best = get_best_proxies(1)

    if not best:
        raise HTTPException(
            status_code=404,
            detail="No healthy proxy available",
        )

    return {
        "proxy": best[0]
    }


@router.post("/proxy/report_bad")
def report_bad_proxy(report: ProxyReport):

    ok = mark_proxy_bad(report.proxy)

    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Proxy not found",
        )

    return {
        "status": "reported",
        "proxy": report.proxy,
    }


app = FastAPI()

app.include_router(router)