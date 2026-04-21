import { useEffect, useRef, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Popconfirm,
  Select,
  Space,
  Table,
  Typography,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  PrinterOutlined,
  EyeOutlined,
  ArrowLeftOutlined,
  EditOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";
import {
  ordersApi,
  type SalesOrder,
  type SalesOrderForm,
  type SalesOrderItem,
  type SalesOrderListParams,
} from "../api/orders";

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
  };
}

export default function Orders() {
  const [view, setView] = useState<View>("list");
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<SalesOrder | null>(null);
  const [editingOrderId, setEditingOrderId] = useState<number | null>(null);
  const printRef = useRef<HTMLDivElement>(null);
  const [filters, setFilters] = useState<SalesOrderListParams>({});

  const [form] = Form.useForm();
  const [items, setItems] = useState<ItemRow[]>([newItemRow()]);

  const fetchOrders = async (params: SalesOrderListParams = filters) => {
    setLoading(true);
    try {
      const { data } = await ordersApi.list(params);
      setOrders(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (view === "list") fetchOrders();
  }, [view, filters]);

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

  const handlePrint = () => window.print();

  // ========== 列表视图 ==========
  if (view === "list") {
    return (
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>销售单管理</Typography.Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建销售单</Button>
        </div>
        <Card style={{ marginBottom: 16 }}>
          <OrderFilters
            onSearch={(nextFilters) => setFilters(nextFilters)}
            onReset={() => setFilters({})}
          />
        </Card>
        <Card>
          <Table
            dataSource={orders}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 15 }}
            columns={[
              { title: "单号", dataIndex: "order_number", width: 180 },
              { title: "客户名称", dataIndex: "customer_name", width: 150 },
              { title: "销售日期", dataIndex: "sales_date", width: 120 },
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
              { title: "付款方式", dataIndex: "payment_terms", width: 120 },
              {
                title: "操作", key: "actions", width: 200,
                render: (_, record) => (
                  <Space>
                    <Button size="small" icon={<EyeOutlined />} onClick={() => handleView(record.id)}>查看</Button>
                    <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record.id)}>编辑</Button>
                    <Button size="small" icon={<PrinterOutlined />} onClick={async () => { await handleView(record.id); }}>打印</Button>
                    <Popconfirm title="确定删除此销售单？" onConfirm={() => handleDelete(record.id)}>
                      <Button size="small" danger icon={<DeleteOutlined />}>删除</Button>
                    </Popconfirm>
                  </Space>
                ),
              },
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
              <Input style={{ width: 180 }} />
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
                  <Input value={record.product_name} onChange={(e) => updateItem(record.key, "product_name", e.target.value)} placeholder="产品名称" />
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
        <Button type="primary" icon={<PrinterOutlined />} onClick={handlePrint}>打印</Button>
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
              <td colSpan={2}></td>
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
          合同金额：{orderTotal.toFixed(2)}　　产品合计：{orderTotal.toFixed(2)}
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
              <td>订货电话：18989438186　　QQ：1015352162</td>
              <td style={{ textAlign: "right" }}>制单人：</td>
            </tr>
            <tr>
              <td>订货地址：义乌市国际商贸城三区64号门25220店面</td>
              <td style={{ textAlign: "right" }}>收货人(签字)：</td>
            </tr>
          </tbody>
        </table>
      </div>

      <style>{`
        .slip {
          max-width: 820px;
          margin: 0 auto;
          padding: 24px 32px;
          background: #fff;
          border: 1px solid #e0e0e0;
          font-family: "SimSun", "宋体", serif;
          font-size: 13px;
          color: #333;
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
          margin-bottom: 8px;
        }
        .slip-info td {
          padding: 4px 0;
          font-size: 13px;
          border: 1px solid #999;
          padding: 5px 8px;
        }
        .slip-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 0;
        }
        .slip-table th,
        .slip-table td {
          border: 1px solid #999;
          padding: 5px 4px;
          text-align: center;
          font-size: 12px;
        }
        .slip-table th {
          background: #d6eaf8;
          font-weight: 600;
          color: #1a5276;
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
        }
        .slip-footer-info td {
          border: 1px solid #999;
          padding: 5px 8px;
          font-size: 12px;
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
            padding: 15px;
          }
          .no-print { display: none !important; }
        }
      `}</style>
    </div>
  );
}

function OrderFilters({
  onSearch,
  onReset,
}: {
  onSearch: (filters: SalesOrderListParams) => void;
  onReset: () => void;
}) {
  const [orderNumber, setOrderNumber] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);

  const handleSearch = () => {
    const nextFilters: SalesOrderListParams = {};
    if (orderNumber.trim()) nextFilters.order_number = orderNumber.trim();
    if (customerName.trim()) nextFilters.customer_name = customerName.trim();
    if (dateRange?.[0]) nextFilters.start_date = dateRange[0].format("YYYY-MM-DD");
    if (dateRange?.[1]) nextFilters.end_date = dateRange[1].format("YYYY-MM-DD");
    onSearch(nextFilters);
  };

  const handleReset = () => {
    setOrderNumber("");
    setCustomerName("");
    setDateRange(null);
    onReset();
  };

  return (
    <Space wrap>
      <Input
        placeholder="单号"
        value={orderNumber}
        onChange={(e) => setOrderNumber(e.target.value)}
        onPressEnter={handleSearch}
        allowClear
        style={{ width: 180 }}
      />
      <Input
        placeholder="客户名称"
        value={customerName}
        onChange={(e) => setCustomerName(e.target.value)}
        onPressEnter={handleSearch}
        allowClear
        style={{ width: 180 }}
      />
      <DatePicker.RangePicker
        value={dateRange}
        onChange={(dates) => setDateRange(dates as [Dayjs | null, Dayjs | null] | null)}
      />
      <Button type="primary" onClick={handleSearch}>查询</Button>
      <Button onClick={handleReset}>重置</Button>
    </Space>
  );
}
