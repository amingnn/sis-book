from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from sqlmodel import Session, SQLModel, select

from app.customer.models import Customer
from app.product.images import store_product_image
from app.product.models import Product
from app.purchases.models import PurchaseOrder
from app.sales.models import SalesRecord
from app.supplier.models import Supplier
from app.tasks.models import Task


class ImportExportError(Exception):
    pass


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    required: bool = False
    kind: str = "str"


@dataclass(frozen=True)
class TableSpec:
    key: str
    sheet_name: str
    model: type[SQLModel]
    fields: tuple[FieldSpec, ...]
    unique_field: str | None = None


TABLE_SPECS = (
    TableSpec(
        "customers",
        "客户",
        Customer,
        (
            FieldSpec("name", "客户名称", True),
            FieldSpec("phone", "电话"),
            FieldSpec("address", "地址"),
            FieldSpec("notes", "备注"),
        ),
        "name",
    ),
    TableSpec(
        "suppliers",
        "厂家",
        Supplier,
        (
            FieldSpec("name", "厂家名称", True),
            FieldSpec("phone", "电话"),
            FieldSpec("address", "地址"),
            FieldSpec("notes", "备注"),
        ),
        "name",
    ),
    TableSpec(
        "products",
        "产品",
        Product,
        (
            FieldSpec("name", "产品名称", True),
            FieldSpec("image", "图片"),
            FieldSpec("per_box_qty", "装箱数", kind="int"),
            FieldSpec("box_spec", "箱规"),
            FieldSpec("volume", "体积", kind="decimal"),
            FieldSpec("purchase_price", "进货价格", kind="decimal"),
            FieldSpec("stock_qty", "库存数量", kind="int"),
            FieldSpec("notes", "备注"),
        ),
        "name",
    ),
    TableSpec(
        "sales",
        "销售",
        SalesRecord,
        (
            FieldSpec("sale_time", "销售时间", True, "date"),
            FieldSpec("customer_name", "客户名称", True),
            FieldSpec("product", "产品", True),
            FieldSpec("amount", "销售金额", True, "decimal"),
            FieldSpec("delivery_time", "送货时间", kind="date"),
            FieldSpec("collection_time", "收款时间", kind="date"),
            FieldSpec("is_settled", "是否结清", kind="bool"),
            FieldSpec("payment_method", "交易方式"),
            FieldSpec("cost", "成本", True, "decimal"),
            FieldSpec("notes", "备注"),
        ),
    ),
    TableSpec(
        "purchases",
        "采购",
        PurchaseOrder,
        (
            FieldSpec("purchase_time", "采购时间", True, "date"),
            FieldSpec("supplier_name", "厂家名称", True),
            FieldSpec("product_name", "产品名称", True),
            FieldSpec("box_count", "箱数", True, "int"),
            FieldSpec("per_box_qty", "装箱数", True, "int"),
            FieldSpec("unit_price", "单价", True, "decimal"),
            FieldSpec("paid_amount", "已付金额", kind="decimal"),
            FieldSpec("notes", "备注"),
        ),
    ),
    TableSpec(
        "tasks",
        "任务",
        Task,
        (
            FieldSpec("title", "标题", True),
            FieldSpec("description", "描述"),
            FieldSpec("category", "分类"),
            FieldSpec("priority", "优先级"),
            FieldSpec("status", "状态"),
            FieldSpec("due_date", "到期日期", kind="date"),
            FieldSpec("related_type", "关联类型"),
            FieldSpec("related_id", "关联ID", kind="nullable_int"),
            FieldSpec("notes", "备注"),
        ),
    ),
)


def _cell_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bool):
        return "是" if value else "否"
    return value


def _rows_for_export(session: Session, spec: TableSpec) -> list[dict[str, Any]]:
    rows = session.exec(select(spec.model)).all()
    return [
        {field.label: _cell_value(getattr(row, field.name, "")) for field in spec.fields}
        for row in rows
    ]


def export_excel(session: Session, target_dir: str) -> dict:
    if not target_dir.strip():
        raise ImportExportError("请先填写导出目录")

    target_dir = Path(target_dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"sis-book-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"

    with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
        for spec in TABLE_SPECS:
            frame = pd.DataFrame(_rows_for_export(session, spec))
            if frame.empty:
                frame = pd.DataFrame(columns=[field.label for field in spec.fields])
            frame.to_excel(writer, sheet_name=spec.sheet_name, index=False)

    return {"cancelled": False, "path": str(target_path)}


def _read_workbook(payload: bytes) -> dict[str, pd.DataFrame]:
    if not payload:
        raise ImportExportError("请选择 Excel 文件")
    try:
        return pd.read_excel(BytesIO(payload), sheet_name=None, dtype=str, keep_default_na=False)
    except Exception as exc:
        raise ImportExportError("Excel 文件读取失败") from exc


def _normalized(text: str) -> str:
    return text.strip().lower().replace(" ", "").replace("_", "")


def _field_lookup(spec: TableSpec) -> dict[str, FieldSpec]:
    lookup: dict[str, FieldSpec] = {}
    for field in spec.fields:
        lookup[_normalized(field.name)] = field
        lookup[_normalized(field.label)] = field
    return lookup


def _match_spec(sheet_name: str, columns: list[str]) -> TableSpec | None:
    normalized_sheet = _normalized(sheet_name)
    for spec in TABLE_SPECS:
        if normalized_sheet in {_normalized(spec.key), _normalized(spec.sheet_name)}:
            return spec

    best_spec: TableSpec | None = None
    best_score = 0
    for spec in TABLE_SPECS:
        lookup = _field_lookup(spec)
        score = sum(1 for column in columns if _normalized(str(column)) in lookup)
        if score > best_score:
            best_score = score
            best_spec = spec
    return best_spec if best_score >= 2 else None


def _column_mapping(spec: TableSpec, columns: list[str]) -> dict[str, FieldSpec]:
    lookup = _field_lookup(spec)
    return {
        column: lookup[_normalized(str(column))]
        for column in columns
        if _normalized(str(column)) in lookup
    }


def preview_excel(payload: bytes) -> dict:
    workbook = _read_workbook(payload)
    sheets = []
    for sheet_name, frame in workbook.items():
        columns = [str(column) for column in frame.columns]
        spec = _match_spec(sheet_name, columns)
        mapping = _column_mapping(spec, columns) if spec else {}
        mapped_fields = {field.name for field in mapping.values()}
        warnings = []
        if spec:
            missing_required = [
                field.label for field in spec.fields if field.required and field.name not in mapped_fields
            ]
            if missing_required:
                warnings.append(f"缺少必填列：{'、'.join(missing_required)}")
        else:
            warnings.append("未匹配到可导入的数据表")

        sheets.append(
            {
                "name": sheet_name,
                "matched_table": spec.key if spec else "",
                "matched_label": spec.sheet_name if spec else "",
                "total_rows": len(frame.index),
                "columns": columns,
                "mappings": [
                    {
                        "column": column,
                        "field": field.name,
                        "label": field.label,
                        "required": field.required,
                    }
                    for column, field in mapping.items()
                ],
                "rows": frame.head(10).to_dict(orient="records"),
                "warnings": warnings,
            }
        )
    return {"sheets": sheets}


def _empty(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _to_date(value: Any) -> date | None:
    if _empty(value):
        return None
    parsed = pd.to_datetime(value, errors="raise")
    return parsed.date()


def _to_bool(value: Any) -> bool:
    if _empty(value):
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "是", "已结清", "结清"}


def _coerce_value(field: FieldSpec, value: Any) -> Any:
    if field.kind == "date":
        return _to_date(value)
    if field.kind == "bool":
        return _to_bool(value)
    if field.kind == "int":
        return 0 if _empty(value) else int(Decimal(str(value)))
    if field.kind == "nullable_int":
        return None if _empty(value) else int(Decimal(str(value)))
    if field.kind == "decimal":
        return Decimal("0") if _empty(value) else Decimal(str(value))
    return "" if value is None else str(value).strip()


def _payload_from_row(spec: TableSpec, mapping: dict[str, FieldSpec], row: dict) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column, field in mapping.items():
        payload[field.name] = _coerce_value(field, row.get(column, ""))

    missing_required = [
        field.label
        for field in spec.fields
        if field.required and _empty(payload.get(field.name))
    ]
    if missing_required:
        raise ImportExportError(f"{spec.sheet_name} 缺少必填值：{'、'.join(missing_required)}")

    if spec.key == "products" and payload.get("image"):
        payload["image"] = store_product_image(payload["image"], payload["name"])
    return payload


def _upsert_or_create(session: Session, spec: TableSpec, payload: dict[str, Any]) -> str:
    if spec.unique_field:
        unique_value = payload.get(spec.unique_field)
        column = getattr(spec.model, spec.unique_field)
        entity = session.exec(select(spec.model).where(column == unique_value)).first()
        if entity:
            for key, value in payload.items():
                setattr(entity, key, value)
            if hasattr(entity, "updated_at"):
                setattr(entity, "updated_at", datetime.now())
            session.add(entity)
            return "updated"

    session.add(spec.model(**payload))
    return "created"


def import_excel(session: Session, payload: bytes) -> dict:
    workbook = _read_workbook(payload)
    summary = []
    for sheet_name, frame in workbook.items():
        columns = [str(column) for column in frame.columns]
        spec = _match_spec(sheet_name, columns)
        if not spec:
            continue

        mapping = _column_mapping(spec, columns)
        created = 0
        updated = 0
        for row in frame.to_dict(orient="records"):
            if all(_empty(value) for value in row.values()):
                continue
            try:
                payload = _payload_from_row(spec, mapping, row)
            except Exception as exc:
                raise ImportExportError(f"{spec.sheet_name} 第 {created + updated + 1} 行导入失败：{exc}") from exc
            action = _upsert_or_create(session, spec, payload)
            if action == "updated":
                updated += 1
            else:
                created += 1

        summary.append(
            {
                "sheet": sheet_name,
                "table": spec.sheet_name,
                "created": created,
                "updated": updated,
            }
        )

    session.commit()
    return {"summary": summary}
