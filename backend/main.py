import sys
import threading
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
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


# 生产模式下托管前端静态文件
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


def start_server(port: int = 18234):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main():
    dev_mode = "--dev" in sys.argv
    port = 18234

    if dev_mode:
        uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
    else:
        server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
        server_thread.start()

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
