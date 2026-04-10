import sys
import threading
import time
import traceback
import urllib.request
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, func, select

from app.database import get_session, init_db
from app.purchases.models import PurchaseOrder
from app.purchases.router import router as purchases_router
from app.sales.models import SalesRecord
from app.sales.router import router as sales_router
from app.orders.router import router as orders_router
from app.config import get_data_dir


def _get_base_dir() -> Path:
    """打包后用 sys._MEIPASS，开发时用项目根目录"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


# PyInstaller console=False 时 sys.stdout/stderr 为 None，会导致 uvicorn 等库崩溃
if getattr(sys, "frozen", False) and sys.stdout is None:
    import os
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")


# region agent log
_log_file = get_data_dir() / "debug.log"
def _log(msg: str):
    import json, time as _t
    with open(_log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _t.time(), "msg": msg}, ensure_ascii=False) + "\n")
# endregion


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    _log("lifespan: init_db start")
    init_db()
    _log("lifespan: init_db done")
    yield


app = FastAPI(title="暮橙体育记账本", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sales_router)
app.include_router(purchases_router)
app.include_router(orders_router)


@app.get("/api/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    today = date.today()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    month_sales, month_cost = session.exec(
        select(
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
        ).where(SalesRecord.sale_time >= month_start)
    ).one()

    year_sales, year_cost = session.exec(
        select(
            func.coalesce(func.sum(SalesRecord.amount), 0),
            func.coalesce(func.sum(SalesRecord.cost), 0),
        ).where(SalesRecord.sale_time >= year_start)
    ).one()

    unsettled_count, unsettled_amount = session.exec(
        select(
            func.count(SalesRecord.id),
            func.coalesce(func.sum(SalesRecord.amount), 0),
        ).where(SalesRecord.is_settled == False)  # noqa: E712
    ).one()

    recent_sales = session.exec(
        select(SalesRecord).order_by(SalesRecord.sale_time.desc()).limit(5)
    ).all()

    recent_purchases = session.exec(
        select(PurchaseOrder).order_by(PurchaseOrder.purchase_time.desc()).limit(5)
    ).all()

    month_sales = Decimal(str(month_sales))
    month_cost = Decimal(str(month_cost))
    year_sales = Decimal(str(year_sales))
    year_cost = Decimal(str(year_cost))

    return {
        "month_sales": float(month_sales),
        "month_cost": float(month_cost),
        "month_profit": float(month_sales - month_cost),
        "year_sales": float(year_sales),
        "year_cost": float(year_cost),
        "year_profit": float(year_sales - year_cost),
        "unsettled_count": unsettled_count,
        "unsettled_amount": float(Decimal(str(unsettled_amount))),
        "recent_sales": [
            {
                "id": r.id,
                "sale_time": r.sale_time.isoformat(),
                "customer_name": r.customer_name,
                "product": r.product,
                "amount": float(r.amount),
                "is_settled": r.is_settled,
            }
            for r in recent_sales
        ],
        "recent_purchases": [
            {
                "id": r.id,
                "purchase_time": r.purchase_time.isoformat(),
                "supplier_name": r.supplier_name,
                "product_name": r.product_name,
                "total_amount": float(r.unit_price * r.box_count * r.per_box_qty),
            }
            for r in recent_purchases
        ],
    }


BASE_DIR = _get_base_dir()
frontend_dist = BASE_DIR / "frontend" / "dist"
_log(f"frozen={getattr(sys, 'frozen', False)}, BASE_DIR={BASE_DIR}, frontend_dist={frontend_dist}, exists={frontend_dist.exists()}")

if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    _log("frontend static files mounted")
else:
    _log("WARNING: frontend dist NOT FOUND, static files not mounted")


def start_server(port: int = 18234):
    try:
        _log(f"start_server: starting uvicorn on port {port}")
        uvicorn.run(app, host="127.0.0.1", port=port, log_config=None)
    except Exception:
        _log(f"start_server CRASHED: {traceback.format_exc()}")


def main():
    _log(f"main() called, sys.argv={sys.argv}, frozen={getattr(sys, 'frozen', False)}")
    dev_mode = "--dev" in sys.argv
    port = 18234

    if dev_mode:
        uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
    else:
        server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
        server_thread.start()

        _log("waiting for backend to be ready...")
        ready = False
        for i in range(150):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/api/dashboard", timeout=1)
                _log(f"backend ready after {i * 0.1:.1f}s")
                ready = True
                break
            except Exception:
                time.sleep(0.1)

        if not ready:
            _log("WARNING: backend NOT ready after 15s, opening window anyway")

        import webview

        webview.create_window(
            "暮橙体育记账本",
            f"http://127.0.0.1:{port}",
            width=1280,
            height=800,
            min_size=(1024, 600),
        )
        webview.start()


if __name__ == "__main__":
    main()
