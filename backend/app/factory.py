from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.customer.router import router as customer_router
from app.dashboard.router import router as dashboard_router
from app.database import init_db
from app.debug import log
from app.import_export.router import router as import_export_router
from app.orders.router import router as orders_router
from app.product.router import router as product_router
from app.purchases.router import router as purchases_router
from app.sales.router import router as sales_router
from app.static import mount_static_files
from app.supplier.router import router as supplier_router
from app.sync.router import router as sync_router
from app.sync.service import start_scheduler, stop_scheduler
from app.tasks.router import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log("lifespan: init_db start")
    init_db()
    log("lifespan: init_db done")
    start_scheduler()
    yield
    stop_scheduler()


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_routers(app: FastAPI) -> None:
    app.include_router(sales_router)
    app.include_router(purchases_router)
    app.include_router(orders_router)
    app.include_router(tasks_router)
    app.include_router(sync_router)
    app.include_router(customer_router)
    app.include_router(supplier_router)
    app.include_router(product_router)
    app.include_router(import_export_router)
    app.include_router(dashboard_router)


def create_app(base_dir: Path) -> FastAPI:
    app = FastAPI(title="暮橙体育记账本", lifespan=lifespan)
    register_middleware(app)
    register_routers(app)
    mount_static_files(app, base_dir)
    return app
