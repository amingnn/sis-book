"""生成测试数据"""
import random
from datetime import date, timedelta
from decimal import Decimal

from app.database import init_db, get_session
from app.sales.models import SalesRecord
from app.purchases.models import PurchaseOrder
from app.orders.models import SalesOrder, SalesOrderItem
from app.customer.models import Customer
from app.product.models import Product
from app.supplier.models import Supplier

CUSTOMERS = ["福瑞鑫", "JT", "通远", "鑫达贸易", "华盛商行", "金利来", "宏达玩具", "乐天商贸", "万家福", "顺发百货"]
PRODUCTS = ["鹿牌球", "PVC球", "跳跳马", "弹力球", "充气玩具", "网棒混装", "贴标球", "新蛇混款", "足球", "篮球"]
SUPPLIERS = ["博扬球业", "昇利隆玩具", "金华塑胶", "永康运动", "浦江文体", "东阳玩具厂", "武义球业"]
COLORS = ["5款混色", "5色混标", "红蓝混", "彩色混装", "单色", "3色混", "随机混色"]
PAYMENT_METHODS = ["现金", "45天", "30天", "微信", "银行转账", "月结"]
BOX_QTYS = [50, 100, 200, 300, 500, 600]

def rand_date(start_year=2025) -> date:
    start = date(start_year, 1, 1)
    return start + timedelta(days=random.randint(0, 460))

def build_product_refs() -> dict[str, dict]:
    refs = {}
    for product in PRODUCTS:
        refs[product] = {
            "supplier_name": random.choice(SUPPLIERS),
            "per_box_qty": random.choice(BOX_QTYS),
            "box_spec": f"{random.randint(45, 80)}*{random.randint(30, 55)}*{random.randint(25, 50)}",
            "volume": Decimal(str(round(random.uniform(0.03, 0.18), 3))),
            "purchase_price": Decimal(str(round(random.uniform(0.3, 8.0), 2))),
            "stock_qty": random.randint(0, 5000),
        }
    return refs

def seed():
    init_db()
    session = next(get_session())
    product_refs = build_product_refs()

    # 客户资料
    for name in CUSTOMERS:
        session.add(
            Customer(
                name=name,
                phone=f"1{random.randint(3000000000, 9999999999)}",
                address=random.choice(["浙江省金华市义乌市", "广东省广州市白云区", "江苏省南京市", ""]),
                notes=random.choice(["", "", "重点客户", "月结客户"]),
            )
        )

    # 厂家资料
    for name in SUPPLIERS:
        session.add(
            Supplier(
                name=name,
                phone=f"1{random.randint(3000000000, 9999999999)}",
                address=random.choice(["义乌", "金华", "永康", "浦江", "东阳"]),
                notes=random.choice(["", "", "常用厂家", "价格稳定"]),
            )
        )

    # 产品资料
    for name, ref in product_refs.items():
        session.add(
            Product(
                name=name,
                per_box_qty=ref["per_box_qty"],
                box_spec=ref["box_spec"],
                volume=ref["volume"],
                purchase_price=ref["purchase_price"],
                stock_qty=ref["stock_qty"],
                notes=random.choice(["", "", "常规库存", "热销"]),
            )
        )

    # 销售记录 20 条
    for _ in range(20):
        product_name = random.choice(PRODUCTS)
        ref = product_refs[product_name]
        qty = random.randint(100, 3000)
        cost = (ref["purchase_price"] * qty).quantize(Decimal("0.01"))
        margin = Decimal(str(round(random.uniform(0.03, 0.12), 3)))
        amount = (cost * (1 + margin)).quantize(Decimal("0.01"))
        sale_time = rand_date()
        record = SalesRecord(
            sale_time=sale_time,
            customer_name=random.choice(CUSTOMERS),
            product=product_name,
            amount=amount,
            delivery_time=sale_time + timedelta(days=random.randint(3, 30)) if random.random() > 0.3 else None,
            collection_time=sale_time + timedelta(days=random.randint(20, 60)) if random.random() > 0.5 else None,
            is_settled=random.random() > 0.4,
            payment_method=random.choice(PAYMENT_METHODS),
            cost=cost,
            notes=random.choice(["", "", "", "加急", "含运费", "二次补货", "样品单"]),
        )
        session.add(record)

    # 采购记录 20 条
    for _ in range(20):
        product_name = random.choice(PRODUCTS)
        ref = product_refs[product_name]
        box_count = random.randint(1, 80)
        per_box_qty = ref["per_box_qty"]
        unit_price = ref["purchase_price"]
        po = PurchaseOrder(
            purchase_time=rand_date(),
            supplier_name=ref["supplier_name"],
            product_name=product_name,
            box_count=box_count,
            per_box_qty=per_box_qty,
            unit_price=unit_price,
            paid_amount=Decimal(str(round(random.uniform(0, float(unit_price * box_count * per_box_qty)), 2))),
            notes=random.choice(["", "", "", "中包贴标签", "常规包装", "客户提供标签"]),
        )
        session.add(po)

    # 销售单 10 条
    for i in range(10):
        sales_date = rand_date()
        order = SalesOrder(
            order_number=f"MC{sales_date.strftime('%Y%m%d')}{i+1:03d}",
            customer_name=random.choice(CUSTOMERS),
            customer_phone=f"1{random.randint(3000000000, 9999999999)}",
            delivery_address=random.choice(["浙江省金华市义乌市等通知", "广东省广州市白云区XX路", "江苏省南京市XX区", ""]),
            sales_date=sales_date,
            delivery_date=sales_date + timedelta(days=random.randint(5, 20)) if random.random() > 0.3 else None,
            payment_terms=random.choice(["现金", "10%定金 发货付尾款", "月结", "微信"]),
            notes="",
        )
        item_count = random.randint(1, 4)
        for _ in range(item_count):
            product_name = random.choice(PRODUCTS)
            ref = product_refs[product_name]
            item = SalesOrderItem(
                product_name=product_name,
                color_spec=random.choice(COLORS),
                total_boxes=random.randint(1, 50),
                per_box_qty=ref["per_box_qty"],
                unit_price=(ref["purchase_price"] * Decimal(str(round(random.uniform(1.03, 1.16), 2)))).quantize(Decimal("0.01")),
                box_size=ref["box_spec"],
                notes="",
            ) # type: ignore
            order.items.append(item)
        session.add(order)

    session.commit()
    print("测试数据生成完毕: 客户/厂家/产品资料 + 20条销售记录 + 20条采购记录 + 10张销售单")

if __name__ == "__main__":
    seed()
