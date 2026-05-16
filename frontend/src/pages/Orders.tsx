import { useCallback, useEffect, useRef, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Select,
  Space,
  Table,
  Typography,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  ArrowLeftOutlined,
  EditOutlined,
  FileImageOutlined,
  FilePdfOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";
import html2canvas from "html2canvas";
import {
  ordersApi,
  type SalesOrder,
  type SalesOrderForm,
  type SalesOrderItem,
  type SalesOrderListParams,
} from "../api/orders";
import { customersApi, type Customer } from "../api/customers";
import { productsApi, type Product } from "../api/products";
import PageToolbar from "../components/PageToolbar";
import { createActionColumn } from "../components/TableActions";

type DesktopSavePayload = {
  filename: string;
  data_url: string;
  file_types?: string[];
};

type DesktopSaveResult = {
  saved?: boolean;
  cancelled?: boolean;
  path?: string;
  error?: string;
};

declare global {
  interface Window {
    pywebview?: {
      api?: {
        save_file?: (payload: DesktopSavePayload) => Promise<DesktopSaveResult>;
      };
    };
  }
}

type View = "list" | "create" | "detail";

interface ItemRow {
  key: string;
  product_name: string;
  color_spec: string;
  total_boxes: number;
  per_box_qty: number;
  unit_price: number;
  box_size: string;
  notes: string;
  image: string;
}

const PAYMENT_OPTIONS = [
  { label: "现金", value: "现金" },
  { label: "微信", value: "微信" },
  { label: "支付宝", value: "支付宝" },
  { label: "银行转账", value: "银行转账" },
  { label: "月结", value: "月结" },
  { label: "10%定金 发货付尾款", value: "10%定金 发货付尾款" },
  { label: "其他", value: "其他" },
];

function calcSubtotal(row: { total_boxes: number; per_box_qty: number; unit_price: number }): number {
  return row.total_boxes * row.per_box_qty * Number(row.unit_price);
}

function newItemRow(): ItemRow {
  return {
    key: crypto.randomUUID(),
    product_name: "",
    color_spec: "",
    total_boxes: 1,
    per_box_qty: 1,
    unit_price: 0,
    box_size: "",
    notes: "",
    image: "",
  };
}

function resolveImageSrc(image?: string): string {
  if (!image) return "";
  if (image.startsWith("data:") || image.startsWith("http")) return image;
  return image.startsWith("/") ? image : `/${image}`;
}

function safeFilename(name: string): string {
  return name.replace(/[\\/:*?"<>|]/g, "-");
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function saveExportBlob(blob: Blob, filename: string, fileTypes: string[]): Promise<boolean> {
  if (window.pywebview?.api?.save_file) {
    const result = await window.pywebview.api.save_file({
      filename,
      data_url: await blobToDataUrl(blob),
      file_types: fileTypes,
    });
    if (result?.error) {
      throw new Error(result.error);
    }
    return Boolean(result?.saved);
  }

  downloadBlob(blob, filename);
  return true;
}

function dataUrlToBytes(dataUrl: string): Uint8Array {
  const base64 = dataUrl.split(",")[1] ?? "";
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function bytesToArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
}

function buildPdfFromJpeg(jpegDataUrl: string, imageWidth: number, imageHeight: number): Blob {
  const encoder = new TextEncoder();
  const imageBytes = dataUrlToBytes(jpegDataUrl);
  const pageWidth = 595.28;
  const pageHeight = 841.89;
  const margin = 24;
  const scale = Math.min(
    (pageWidth - margin * 2) / imageWidth,
    (pageHeight - margin * 2) / imageHeight,
  );
  const drawWidth = imageWidth * scale;
  const drawHeight = imageHeight * scale;
  const drawX = (pageWidth - drawWidth) / 2;
  const drawY = pageHeight - margin - drawHeight;
  const content = `q\n${drawWidth.toFixed(2)} 0 0 ${drawHeight.toFixed(2)} ${drawX.toFixed(2)} ${drawY.toFixed(2)} cm\n/Im1 Do\nQ\n`;
  const contentBytes = encoder.encode(content);
  const chunks: Uint8Array[] = [];
  const offsets = [0];
  let offset = 0;

  const append = (part: string | Uint8Array) => {
    const bytes = typeof part === "string" ? encoder.encode(part) : part;
    chunks.push(bytes);
    offset += bytes.length;
  };
  const startObject = (id: number) => {
    offsets[id] = offset;
    append(`${id} 0 obj\n`);
  };
  const endObject = () => append("endobj\n");

  append("%PDF-1.4\n");
  startObject(1);
  append("<< /Type /Catalog /Pages 2 0 R >>\n");
  endObject();
  startObject(2);
  append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n");
  endObject();
  startObject(3);
  append(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /XObject << /Im1 5 0 R >> >> /Contents 4 0 R >>\n`);
  endObject();
  startObject(4);
  append(`<< /Length ${contentBytes.length} >>\nstream\n`);
  append(contentBytes);
  append("endstream\n");
  endObject();
  startObject(5);
  append(`<< /Type /XObject /Subtype /Image /Width ${imageWidth} /Height ${imageHeight} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${imageBytes.length} >>\nstream\n`);
  append(imageBytes);
  append("\nendstream\n");
  endObject();

  const xrefOffset = offset;
  append("xref\n0 6\n0000000000 65535 f \n");
  for (let id = 1; id <= 5; id += 1) {
    append(`${String(offsets[id]).padStart(10, "0")} 00000 n \n`);
  }
  append(`trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`);

  return new Blob(chunks.map(bytesToArrayBuffer), { type: "application/pdf" });
}

function waitForImage(image: HTMLImageElement): Promise<void> {
  if (image.complete) return Promise.resolve();
  return new Promise((resolve) => {
    image.onload = () => resolve();
    image.onerror = () => resolve();
  });
}

async function captureDomSlipCanvas(element: HTMLElement): Promise<HTMLCanvasElement> {
  await document.fonts?.ready;
  await Promise.all(Array.from(element.querySelectorAll("img")).map(waitForImage));
  return html2canvas(element, {
    backgroundColor: "#fff",
    scale: Math.min(window.devicePixelRatio || 2, 3),
    useCORS: true,
    allowTaint: false,
    logging: false,
    imageTimeout: 8000,
    scrollX: 0,
    scrollY: 0,
  });
}

const slipStyles = `
  .slip {
    max-width: 820px;
    margin: 0 auto;
    padding: 24px 28px 28px;
    background: #fff;
    border: 1px solid #e0e0e0;
    font-family: "SimSun", "宋体", serif;
    font-size: 13px;
    color: #333;
    box-sizing: border-box;
  }
  .slip-title {
    text-align: center;
    font-size: 22px;
    font-weight: bold;
    color: #1a5276;
    border-bottom: 2px solid #2980b9;
    padding-bottom: 6px;
    margin: 0 0 12px;
    letter-spacing: 6px;
  }
  .slip-info {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
    table-layout: fixed;
  }
  .slip-info td {
    font-size: 13px;
    border: 1px solid #999;
    padding: 5px 8px;
    word-break: break-all;
  }
  .slip-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 0;
    table-layout: fixed;
  }
  .slip-table th,
  .slip-table td {
    border: 1px solid #999;
    padding: 6px 4px;
    text-align: center;
    font-size: 12px;
    vertical-align: middle;
    word-break: break-word;
  }
  .slip-table th {
    background: #d6eaf8;
    font-weight: 600;
    color: #1a5276;
  }
  .slip-item-image {
    width: 64px;
    height: 64px;
    object-fit: contain;
    display: block;
    margin: 0 auto;
  }
  .slip-total-row td {
    font-weight: bold;
    background: #eaf2f8;
  }
  .slip-amount-row {
    border: 1px solid #999;
    border-top: none;
    padding: 6px 8px;
    font-size: 13px;
  }
  .slip-highlight-row {
    border: 1px solid #999;
    border-top: none;
    padding: 6px 8px;
    font-size: 13px;
    background: #fef9e7;
  }
  .slip-notes-row {
    border: 1px solid #999;
    border-top: none;
    padding: 6px 8px;
    font-size: 12px;
    line-height: 1.6;
  }
  .slip-footer-info {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0;
    table-layout: fixed;
  }
  .slip-footer-info td {
    border: 1px solid #999;
    padding: 8px 10px;
    font-size: 12px;
    vertical-align: middle;
  }
  .slip-sign-cell {
    width: 220px;
    text-align: left;
    white-space: nowrap;
  }

  @media print {
    body * { visibility: hidden; }
    .slip, .slip * { visibility: visible; }
    .slip {
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      border: none;
      max-width: none;
      padding: 12px 14px 18px;
    }
    .no-print { display: none !important; }
    .slip-table tr,
    .slip-info tr,
    .slip-footer-info tr,
    .slip-amount-row,
    .slip-highlight-row,
    .slip-notes-row {
      break-inside: avoid;
      page-break-inside: avoid;
    }
  }
`;

export default function Orders() {
  const [view, setView] = useState<View>("list");
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<SalesOrder | null>(null);
  const [editingOrderId, setEditingOrderId] = useState<number | null>(null);
  const printRef = useRef<HTMLDivElement>(null);
  const [filters, setFilters] = useState<SalesOrderListParams>({});
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const [form] = Form.useForm();
  const [items, setItems] = useState<ItemRow[]>([newItemRow()]);

  const fetchOrders = useCallback(async (params: SalesOrderListParams = filters) => {
    setLoading(true);
    try {
      const { data } = await ordersApi.list(params);
      setOrders(data);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    if (view === "list") void fetchOrders();
  }, [view, fetchOrders]);

  useEffect(() => {
    Promise.all([customersApi.list(), productsApi.list()]).then(([customerRes, productRes]) => {
      setCustomers(customerRes.data);
      setProducts(productRes.data);
    });
  }, []);

  const totalAmount = items.reduce((sum, r) => sum + calcSubtotal(r), 0);
  const totalBoxes = items.reduce((sum, r) => sum + r.total_boxes, 0);
  const totalQty = items.reduce((sum, r) => sum + r.total_boxes * r.per_box_qty, 0);

  const updateItem = (key: string, field: keyof ItemRow, value: unknown) => {
    setItems((prev) =>
      prev.map((r) => (r.key === key ? { ...r, [field]: value } : r))
    );
  };

  const removeItem = (key: string) => {
    setItems((prev) => (prev.length <= 1 ? prev : prev.filter((r) => r.key !== key)));
  };

  const handleCreate = () => {
    setEditingOrderId(null);
    setCurrentOrder(null);
    form.resetFields();
    form.setFieldsValue({ sales_date: dayjs(), payment_terms: "现金" });
    setItems([newItemRow()]);
    setView("create");
  };

  const fillOrderForm = (order: SalesOrder) => {
    form.setFieldsValue({
      customer_name: order.customer_name,
      customer_phone: order.customer_phone,
      delivery_address: order.delivery_address,
      sales_date: dayjs(order.sales_date),
      delivery_date: order.delivery_date ? dayjs(order.delivery_date) : null,
      payment_terms: order.payment_terms,
      notes: order.notes,
    });
    setItems(
      order.items.map((item) => ({
        key: item.id ? `item-${item.id}` : crypto.randomUUID(),
        product_name: item.product_name,
        color_spec: item.color_spec || "",
        total_boxes: item.total_boxes,
        per_box_qty: item.per_box_qty,
        unit_price: Number(item.unit_price),
        box_size: item.box_size || "",
        notes: item.notes || "",
        image: item.image || "",
      }))
    );
  };

  const handleView = async (id: number) => {
    const { data } = await ordersApi.get(id);
    setEditingOrderId(null);
    setCurrentOrder(data);
    setView("detail");
  };

  const handleEdit = async (id: number) => {
    const { data } = await ordersApi.get(id);
    setEditingOrderId(id);
    setCurrentOrder(data);
    fillOrderForm(data);
    setView("create");
  };

  const handleDelete = async (id: number) => {
    await ordersApi.delete(id);
    message.success("已删除");
    fetchOrders();
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    const hasEmptyProduct = items.some((r) => !r.product_name.trim());
    if (hasEmptyProduct) {
      message.warning("请填写所有产品名称");
      return;
    }
    const payload: SalesOrderForm = {
      customer_name: values.customer_name,
      customer_phone: values.customer_phone || "",
      delivery_address: values.delivery_address || "",
      sales_date: (values.sales_date as Dayjs).format("YYYY-MM-DD"),
      delivery_date: values.delivery_date
        ? (values.delivery_date as Dayjs).format("YYYY-MM-DD")
        : null,
      payment_terms: values.payment_terms || "",
      notes: values.notes || "",
      items: items.map((r) => ({
        product_name: r.product_name,
        color_spec: r.color_spec,
        total_boxes: r.total_boxes,
        per_box_qty: r.per_box_qty,
        unit_price: r.unit_price,
        box_size: r.box_size,
        notes: r.notes,
        image: r.image,
      })),
    };
    const { data } = editingOrderId
      ? await ordersApi.update(editingOrderId, payload)
      : await ordersApi.create(payload);
    message.success(
      editingOrderId
        ? `销售单 ${data.order_number} 更新成功`
        : `销售单 ${data.order_number} 创建成功`
    );
    setCurrentOrder(data);
    setView("detail");
  };

  const handleExportImage = async () => {
    if (!currentOrder || !printRef.current) return;
    try {
      const canvas = await captureDomSlipCanvas(printRef.current);
      const dataUrl = canvas.toDataURL("image/png");
      const bytes = dataUrlToBytes(dataUrl);
      const saved = await saveExportBlob(
        new Blob([bytesToArrayBuffer(bytes)], { type: "image/png" }),
        `${safeFilename(currentOrder.order_number || "销售单")}.png`,
        ["PNG Files (*.png)"],
      );
      if (saved) message.success("图片已导出");
    } catch {
      message.error("导出图片失败，请确认销售单图片可以正常显示");
    }
  };

  const handleExportPdf = async () => {
    if (!currentOrder || !printRef.current) return;
    try {
      const canvas = await captureDomSlipCanvas(printRef.current);
      const pdf = buildPdfFromJpeg(
        canvas.toDataURL("image/jpeg", 0.92),
        canvas.width,
        canvas.height,
      );
      const saved = await saveExportBlob(
        pdf,
        `${safeFilename(currentOrder.order_number || "销售单")}.pdf`,
        ["PDF Files (*.pdf)"],
      );
      if (saved) message.success("PDF 已导出");
    } catch {
      message.error("导出 PDF 失败，请确认销售单图片可以正常显示");
    }
  };

  const updateFilters = (nextFilters: SalesOrderListParams) => {
    setFilters(nextFilters);
  };

  // ========== 列表视图 ==========
  if (view === "list") {
    return (
      <div>
        <PageToolbar
          title="开单"
          searchValue={filters.q ?? ""}
          searchPlaceholder="模糊搜索"
          onSearchChange={(value) => setFilters((prev) => ({ ...prev, q: value || undefined }))}
          onSearch={() => fetchOrders()}
          primaryText="新建销售单"
          primaryIcon={<PlusOutlined />}
          onPrimaryClick={handleCreate}
        />
        <Card style={{ marginBottom: 16 }}>
          <OrderFilters
            filters={filters}
            customers={customers}
            onSearch={updateFilters}
            onReset={() => setFilters({})}
          />
        </Card>
        <Card>
          <Table
            dataSource={orders}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 15 }}
            scroll={{ x: 1150 }}
            columns={[
              {
                title: "单号",
                dataIndex: "order_number",
                width: 180,
              },
              {
                title: "客户",
                dataIndex: "customer_name",
                width: 150,
                render: (value: string) => (
                  <Button type="link" onClick={() => setFilters((prev) => ({ ...prev, customer_name: value }))}>
                    {value}
                  </Button>
                ),
              },
              {
                title: "销售日期",
                dataIndex: "sales_date",
                width: 120,
              },
              {
                title: "产品",
                key: "products",
                width: 180,
                render: (_, record) => {
                  const names = Array.from(
                    new Set(record.items.map((item) => item.product_name).filter(Boolean)),
                  );
                  if (!names.length) return "-";
                  return (
                    <Space size={[4, 0]} wrap>
                      {names.map((name) => (
                        <Button
                          key={name}
                          type="link"
                          size="small"
                          onClick={() => setFilters((prev) => ({ ...prev, q: name }))}
                        >
                          {name}
                        </Button>
                      ))}
                    </Space>
                  );
                },
              },
              {
                title: "合计金额", key: "total", width: 120,
                render: (_, record) => {
                  const total = record.items.reduce(
                    (s: number, item: SalesOrderItem) =>
                      s + item.total_boxes * item.per_box_qty * Number(item.unit_price), 0
                  );
                  return `¥${total.toFixed(2)}`;
                },
              },
              {
                title: "付款方式",
                dataIndex: "payment_terms",
                width: 120,
                render: (value: string) => value ? (
                  <Button type="link" onClick={() => setFilters((prev) => ({ ...prev, payment_terms: value }))}>
                    {value}
                  </Button>
                ) : "-",
              },
              createActionColumn<SalesOrder>(
                [
                  { key: "view", label: "查看", icon: <EyeOutlined />, onClick: (record) => handleView(record.id) },
                  { key: "edit", label: "编辑", icon: <EditOutlined />, onClick: (record) => handleEdit(record.id) },
                  {
                    key: "delete",
                    label: "删除",
                    icon: <DeleteOutlined />,
                    danger: true,
                    confirmTitle: "确定删除此销售单？",
                    onClick: (record) => handleDelete(record.id),
                  },
                ],
                240,
              ),
            ]}
          />
        </Card>
      </div>
    );
  }

  // ========== 新建视图 ==========
  if (view === "create") {
    return (
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>
          <Typography.Title level={4} style={{ margin: 0 }}>
            {editingOrderId ? `编辑销售单 ${currentOrder?.order_number ?? ""}` : "新建销售单"}
          </Typography.Title>
        </div>
        <Card>
          <Form form={form} layout="inline" style={{ flexWrap: "wrap", gap: "8px 0" }}>
            <Form.Item label="客户名称" name="customer_name" rules={[{ required: true, message: "请输入客户名称" }]}>
              <Select
                showSearch
                optionFilterProp="label"
                style={{ width: 180 }}
                options={customers.map((customer) => ({
                  label: customer.name,
                  value: customer.name,
                }))}
                onChange={(value) => {
                  const customer = customers.find((item) => item.name === value);
                  if (customer) {
                    form.setFieldsValue({
                      customer_phone: customer.phone,
                      delivery_address: customer.address,
                    });
                  }
                }}
              />
            </Form.Item>
            <Form.Item label="电话" name="customer_phone">
              <Input style={{ width: 140 }} />
            </Form.Item>
            <Form.Item label="送货地址" name="delivery_address">
              <Input style={{ width: 240 }} />
            </Form.Item>
            <Form.Item label="销售日期" name="sales_date" rules={[{ required: true, message: "请选择日期" }]}>
              <DatePicker />
            </Form.Item>
            <Form.Item label="送货日期" name="delivery_date">
              <DatePicker />
            </Form.Item>
            <Form.Item label="付款方式" name="payment_terms">
              <Select options={PAYMENT_OPTIONS} style={{ width: 180 }} allowClear />
            </Form.Item>
          </Form>
        </Card>

        <Card style={{ marginTop: 16 }} title="产品明细">
          <Table
            dataSource={items}
            rowKey="key"
            pagination={false}
            size="small"
            scroll={{ x: 900 }}
            footer={() => (
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <Button type="dashed" icon={<PlusOutlined />} onClick={() => setItems((prev) => [...prev, newItemRow()])}>
                  添加产品
                </Button>
                <Space size="large">
                  <span>总箱数: <strong>{totalBoxes}</strong></span>
                  <span>总数量: <strong>{totalQty}</strong></span>
                  <Typography.Text strong style={{ fontSize: 16 }}>合计: ¥{totalAmount.toFixed(2)}</Typography.Text>
                </Space>
              </div>
            )}
            columns={[
              {
                title: "产品名称", dataIndex: "product_name", width: 150,
                render: (_, record) => (
                  <Select
                    showSearch
                    optionFilterProp="label"
                    value={record.product_name || undefined}
                    onChange={(value) => {
                      const product = products.find((item) => item.name === value);
                      updateItem(record.key, "product_name", value);
                      if (product) {
                        updateItem(record.key, "per_box_qty", product.per_box_qty || record.per_box_qty);
                        updateItem(record.key, "box_size", product.box_spec || record.box_size);
                        updateItem(record.key, "unit_price", product.purchase_price || record.unit_price);
                        updateItem(record.key, "image", product.image || record.image);
                      }
                    }}
                    placeholder="产品名称"
                    style={{ width: "100%" }}
                    options={products.map((product) => ({
                      label: product.name,
                      value: product.name,
                    }))}
                  />
                ),
              },
              {
                title: "图片", dataIndex: "image", width: 110,
                render: (_, record) => (
                  <Space orientation="vertical" size={6}>
                    {record.image ? (
                      <>
                        <img
                          src={resolveImageSrc(record.image)}
                          alt="产品预览"
                          style={{ width: 56, height: 56, objectFit: "contain", border: "1px solid #f0f0f0", borderRadius: 6 }}
                        />
                        <Button size="small" type="link" danger onClick={() => updateItem(record.key, "image", "")}>
                          移除
                        </Button>
                      </>
                    ) : (
                      <Typography.Text type="secondary">选择产品后显示</Typography.Text>
                    )}
                  </Space>
                ),
              },
              {
                title: "颜色", dataIndex: "color_spec", width: 100,
                render: (_, record) => (
                  <Input value={record.color_spec} onChange={(e) => updateItem(record.key, "color_spec", e.target.value)} placeholder="颜色" />
                ),
              },
              {
                title: "总箱数", dataIndex: "total_boxes", width: 80,
                render: (_, record) => (
                  <InputNumber min={1} value={record.total_boxes} onChange={(v) => updateItem(record.key, "total_boxes", v ?? 1)} style={{ width: "100%" }} />
                ),
              },
              {
                title: "每箱数量", dataIndex: "per_box_qty", width: 85,
                render: (_, record) => (
                  <InputNumber min={1} value={record.per_box_qty} onChange={(v) => updateItem(record.key, "per_box_qty", v ?? 1)} style={{ width: "100%" }} />
                ),
              },
              {
                title: "总数量", key: "total_qty", width: 70, align: "right" as const,
                render: (_, record) => record.total_boxes * record.per_box_qty,
              },
              {
                title: "单价", dataIndex: "unit_price", width: 90,
                render: (_, record) => (
                  <InputNumber min={0} step={0.01} value={record.unit_price} onChange={(v) => updateItem(record.key, "unit_price", v ?? 0)} style={{ width: "100%" }} />
                ),
              },
              {
                title: "金额", key: "subtotal", width: 90, align: "right" as const,
                render: (_, record) => `¥${calcSubtotal(record).toFixed(2)}`,
              },
              {
                title: "外箱尺寸", dataIndex: "box_size", width: 90,
                render: (_, record) => (
                  <Input value={record.box_size} onChange={(e) => updateItem(record.key, "box_size", e.target.value)} placeholder="m³" />
                ),
              },
              {
                title: "备注", dataIndex: "notes", width: 100,
                render: (_, record) => (
                  <Input value={record.notes} onChange={(e) => updateItem(record.key, "notes", e.target.value)} />
                ),
              },
              {
                title: "", key: "action", width: 40,
                render: (_, record) => (
                  <Button type="text" danger icon={<DeleteOutlined />} onClick={() => removeItem(record.key)} disabled={items.length <= 1} />
                ),
              },
            ]}
          />
        </Card>

        <Card style={{ marginTop: 16 }}>
          <Form form={form}>
            <Form.Item label="备注" name="notes">
              <Input.TextArea rows={2} placeholder="备注信息" />
            </Form.Item>
          </Form>
          <div style={{ textAlign: "right" }}>
            <Space>
              <Button onClick={() => {
                setEditingOrderId(null);
                setView("list");
              }}>取消</Button>
              <Button type="primary" onClick={handleSubmit}>
                {editingOrderId ? "保存修改" : "保存"}
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  // ========== 查看/打印视图（还原暮橙体育销售单样式） ==========
  const order = currentOrder!;
  const printItems = order.items.map((item) => ({
    ...item,
    unit_price: Number(item.unit_price),
    total_qty: item.total_boxes * item.per_box_qty,
    subtotal: item.total_boxes * item.per_box_qty * Number(item.unit_price),
  }));
  const orderTotal = printItems.reduce((s, item) => s + item.subtotal, 0);
  const orderTotalBoxes = printItems.reduce((s, item) => s + item.total_boxes, 0);
  const orderTotalQty = printItems.reduce((s, item) => s + item.total_qty, 0);

  return (
    <div>
      <div className="no-print" style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>
        <Typography.Title level={4} style={{ margin: 0 }}>销售单详情</Typography.Title>
        <Button icon={<EditOutlined />} onClick={() => handleEdit(order.id)}>编辑</Button>
        <Button icon={<FileImageOutlined />} onClick={() => void handleExportImage()}>导出图片</Button>
        <Button type="primary" icon={<FilePdfOutlined />} onClick={() => void handleExportPdf()}>导出 PDF</Button>
      </div>

      <div ref={printRef} className="slip">
        {/* 标题 */}
        <h1 className="slip-title">暮橙体育销售单</h1>

        {/* 客户信息区 */}
        <table className="slip-info">
          <tbody>
            <tr>
              <td style={{ width: "65%" }}>客户：{order.customer_name}{order.customer_phone ? `（${order.customer_phone}）` : ""}</td>
              <td>销售日期：{order.sales_date}</td>
            </tr>
            <tr>
              <td>备用电话：</td>
              <td>送货日期：{order.delivery_date || " "}</td>
            </tr>
            <tr>
              <td colSpan={2}>送货地址：{order.delivery_address}</td>
            </tr>
          </tbody>
        </table>

        {/* 产品明细表 */}
        <table className="slip-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}>编号</th>
              <th>产品</th>
              <th>颜色</th>
              <th style={{ width: 88 }}>图片</th>
              <th style={{ width: 55 }}>总箱数</th>
              <th style={{ width: 65 }}>每箱数量</th>
              <th style={{ width: 55 }}>总数量</th>
              <th style={{ width: 50 }}>单价</th>
              <th style={{ width: 80 }}>金额</th>
              <th style={{ width: 70 }}>外箱尺寸<br/>(m³)</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            {printItems.map((item, idx) => (
              <tr key={item.id}>
                <td>{idx + 1}</td>
                <td style={{ textAlign: "left" }}>{item.product_name}</td>
                <td>{item.color_spec}</td>
                <td>
                  {item.image ? (
                    <img src={resolveImageSrc(item.image)} alt={`${item.product_name} 图片`} className="slip-item-image" />
                  ) : null}
                </td>
                <td>{item.total_boxes}</td>
                <td>{item.per_box_qty}</td>
                <td>{item.total_qty}</td>
                <td>{item.unit_price}</td>
                <td>{item.subtotal.toFixed(2)}</td>
                <td>{item.box_size}</td>
                <td style={{ textAlign: "left" }}>{item.notes}</td>
              </tr>
            ))}
            <tr className="slip-total-row">
              <td>合计</td>
              <td colSpan={3}></td>
              <td>{orderTotalBoxes}</td>
              <td></td>
              <td>{orderTotalQty}</td>
              <td></td>
              <td>{orderTotal.toFixed(2)}</td>
              <td></td>
              <td></td>
            </tr>
          </tbody>
        </table>

        {/* 合同金额 */}
        <div className="slip-amount-row">
          合同金额：{orderTotal.toFixed(2)}
          <span style={{ marginLeft: 24 }}>产品合计：{orderTotal.toFixed(2)}</span>
        </div>

        {/* 付款方式 */}
        {order.payment_terms && (
          <div className="slip-highlight-row">
            付款方式：{order.payment_terms}
          </div>
        )}

        {/* 备注 */}
        {order.notes && (
          <div className="slip-notes-row">
            备注：<br/>{order.notes}
          </div>
        )}

        {/* 底部信息 */}
        <table className="slip-footer-info">
          <tbody>
            <tr>
              <td>
                订货电话：18989438186
                <span style={{ marginLeft: 24 }}>QQ：1015352162</span>
              </td>
              <td className="slip-sign-cell">制单人：</td>
            </tr>
            <tr>
              <td>订货地址：义乌市国际商贸城三区64号门25220店面</td>
              <td className="slip-sign-cell">收货人(签字)：</td>
            </tr>
          </tbody>
        </table>
      </div>

      <style>{slipStyles}</style>
    </div>
  );
}

function OrderFilters({
  filters,
  customers,
  onSearch,
  onReset,
}: {
  filters: SalesOrderListParams;
  customers: Customer[];
  onSearch: (filters: SalesOrderListParams) => void;
  onReset: () => void;
}) {
  const dateRange: [Dayjs | null, Dayjs | null] | null =
    filters.start_date || filters.end_date
      ? [
          filters.start_date ? dayjs(filters.start_date) : null,
          filters.end_date ? dayjs(filters.end_date) : null,
        ]
      : null;

  const handleSearch = () => {
    onSearch(filters);
  };

  const handleReset = () => {
    onReset();
  };

  return (
    <Space wrap>
      <Input
        placeholder="单号"
        value={filters.order_number ?? ""}
        onChange={(e) => onSearch({ ...filters, order_number: e.target.value || undefined })}
        onPressEnter={handleSearch}
        allowClear
        style={{ width: 180 }}
      />
      <Select
        showSearch
        allowClear
        placeholder="客户"
        value={filters.customer_name}
        onChange={(value) => onSearch({ ...filters, customer_name: value })}
        optionFilterProp="label"
        style={{ width: 180 }}
        options={customers.map((customer) => ({ label: customer.name, value: customer.name }))}
      />
      <Select
        allowClear
        placeholder="付款方式"
        value={filters.payment_terms}
        onChange={(value) => onSearch({ ...filters, payment_terms: value })}
        style={{ width: 180 }}
        options={PAYMENT_OPTIONS}
      />
      <DatePicker.RangePicker
        value={dateRange}
        onChange={(dates) =>
          onSearch({
            ...filters,
            start_date: dates?.[0] ? dates[0].format("YYYY-MM-DD") : undefined,
            end_date: dates?.[1] ? dates[1].format("YYYY-MM-DD") : undefined,
          })
        }
      />
      <Button type="primary" onClick={handleSearch}>筛选</Button>
      <Button onClick={handleReset}>重置</Button>
    </Space>
  );
}
