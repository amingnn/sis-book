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
} from "@ant-design/icons";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";
import {
  ordersApi,
  type SalesOrder,
  type SalesOrderForm,
  type SalesOrderItem,
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
  { label: "其他", value: "其他" },
];

function calcSubtotal(row: ItemRow): number {
  return row.total_boxes * row.per_box_qty * row.unit_price;
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
  const printRef = useRef<HTMLDivElement>(null);

  const [form] = Form.useForm();
  const [items, setItems] = useState<ItemRow[]>([newItemRow()]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const { data } = await ordersApi.list();
      setOrders(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (view === "list") fetchOrders();
  }, [view]);

  const totalAmount = items.reduce((sum, r) => sum + calcSubtotal(r), 0);

  const updateItem = (key: string, field: keyof ItemRow, value: unknown) => {
    setItems((prev) =>
      prev.map((r) => (r.key === key ? { ...r, [field]: value } : r))
    );
  };

  const removeItem = (key: string) => {
    setItems((prev) => (prev.length <= 1 ? prev : prev.filter((r) => r.key !== key)));
  };

  const handleCreate = () => {
    setCurrentOrder(null);
    form.resetFields();
    form.setFieldsValue({ sales_date: dayjs(), payment_terms: "现金" });
    setItems([newItemRow()]);
    setView("create");
  };

  const handleView = async (id: number) => {
    const { data } = await ordersApi.get(id);
    setCurrentOrder(data);
    setView("detail");
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
    const { data } = await ordersApi.create(payload);
    message.success(`销售单 ${data.order_number} 创建成功`);
    setCurrentOrder(data);
    setView("detail");
  };

  const handlePrint = () => {
    window.print();
  };

  // ========== 列表视图 ==========
  if (view === "list") {
    return (
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            销售单管理
          </Typography.Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建销售单
          </Button>
        </div>
        <Card>
          <Table
            dataSource={orders}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 15 }}
            columns={[
              { title: "单号", dataIndex: "order_number", width: 180 },
              { title: "客户名称", dataIndex: "customer_name", width: 150 },
              {
                title: "销售日期",
                dataIndex: "sales_date",
                width: 120,
              },
              {
                title: "合计金额",
                key: "total",
                width: 120,
                render: (_, record) => {
                  const total = record.items.reduce(
                    (s: number, item: SalesOrderItem) =>
                      s + item.total_boxes * item.per_box_qty * Number(item.unit_price),
                    0
                  );
                  return `¥${total.toFixed(2)}`;
                },
              },
              { title: "付款方式", dataIndex: "payment_terms", width: 100 },
              {
                title: "操作",
                key: "actions",
                width: 200,
                render: (_, record) => (
                  <Space>
                    <Button
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handleView(record.id)}
                    >
                      查看
                    </Button>
                    <Button
                      size="small"
                      icon={<PrinterOutlined />}
                      onClick={async () => {
                        await handleView(record.id);
                      }}
                    >
                      打印
                    </Button>
                    <Popconfirm
                      title="确定删除此销售单？"
                      onConfirm={() => handleDelete(record.id)}
                    >
                      <Button size="small" danger icon={<DeleteOutlined />}>
                        删除
                      </Button>
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
          <Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>
            返回
          </Button>
          <Typography.Title level={4} style={{ margin: 0 }}>
            新建销售单
          </Typography.Title>
        </div>
        <Card>
          <Form form={form} layout="inline" style={{ flexWrap: "wrap", gap: "8px 0" }}>
            <Form.Item
              label="客户名称"
              name="customer_name"
              rules={[{ required: true, message: "请输入客户名称" }]}
            >
              <Input style={{ width: 150 }} />
            </Form.Item>
            <Form.Item label="电话" name="customer_phone">
              <Input style={{ width: 140 }} />
            </Form.Item>
            <Form.Item label="送货地址" name="delivery_address">
              <Input style={{ width: 200 }} />
            </Form.Item>
            <Form.Item
              label="销售日期"
              name="sales_date"
              rules={[{ required: true, message: "请选择日期" }]}
            >
              <DatePicker />
            </Form.Item>
            <Form.Item label="送货日期" name="delivery_date">
              <DatePicker />
            </Form.Item>
            <Form.Item label="付款方式" name="payment_terms">
              <Select options={PAYMENT_OPTIONS} style={{ width: 120 }} />
            </Form.Item>
          </Form>
        </Card>

        <Card style={{ marginTop: 16 }} title="产品明细">
          <Table
            dataSource={items}
            rowKey="key"
            pagination={false}
            size="small"
            footer={() => (
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <Button
                  type="dashed"
                  icon={<PlusOutlined />}
                  onClick={() => setItems((prev) => [...prev, newItemRow()])}
                >
                  添加产品
                </Button>
                <Typography.Text strong style={{ fontSize: 16 }}>
                  合计: ¥{totalAmount.toFixed(2)}
                </Typography.Text>
              </div>
            )}
            columns={[
              {
                title: "产品名称",
                dataIndex: "product_name",
                width: 160,
                render: (_, record) => (
                  <Input
                    value={record.product_name}
                    onChange={(e) => updateItem(record.key, "product_name", e.target.value)}
                    placeholder="产品名称"
                  />
                ),
              },
              {
                title: "颜色/规格",
                dataIndex: "color_spec",
                width: 120,
                render: (_, record) => (
                  <Input
                    value={record.color_spec}
                    onChange={(e) => updateItem(record.key, "color_spec", e.target.value)}
                    placeholder="颜色/规格"
                  />
                ),
              },
              {
                title: "总箱数",
                dataIndex: "total_boxes",
                width: 90,
                render: (_, record) => (
                  <InputNumber
                    min={1}
                    value={record.total_boxes}
                    onChange={(v) => updateItem(record.key, "total_boxes", v ?? 1)}
                    style={{ width: "100%" }}
                  />
                ),
              },
              {
                title: "每箱数量",
                dataIndex: "per_box_qty",
                width: 90,
                render: (_, record) => (
                  <InputNumber
                    min={1}
                    value={record.per_box_qty}
                    onChange={(v) => updateItem(record.key, "per_box_qty", v ?? 1)}
                    style={{ width: "100%" }}
                  />
                ),
              },
              {
                title: "单价",
                dataIndex: "unit_price",
                width: 100,
                render: (_, record) => (
                  <InputNumber
                    min={0}
                    step={0.01}
                    value={record.unit_price}
                    onChange={(v) => updateItem(record.key, "unit_price", v ?? 0)}
                    style={{ width: "100%" }}
                    prefix="¥"
                  />
                ),
              },
              {
                title: "小计",
                key: "subtotal",
                width: 100,
                render: (_, record) => `¥${calcSubtotal(record).toFixed(2)}`,
              },
              {
                title: "",
                key: "action",
                width: 50,
                render: (_, record) => (
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => removeItem(record.key)}
                    disabled={items.length <= 1}
                  />
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
              <Button onClick={() => setView("list")}>取消</Button>
              <Button type="primary" onClick={handleSubmit}>
                保存
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  // ========== 查看/打印视图 ==========
  const order = currentOrder!;
  const orderTotal = order.items.reduce(
    (s, item) => s + item.total_boxes * item.per_box_qty * Number(item.unit_price),
    0
  );

  return (
    <div>
      <div
        className="no-print"
        style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}
      >
        <Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>
          返回
        </Button>
        <Typography.Title level={4} style={{ margin: 0 }}>
          销售单详情
        </Typography.Title>
        <Button type="primary" icon={<PrinterOutlined />} onClick={handlePrint}>
          打印
        </Button>
      </div>

      <div ref={printRef} className="print-area">
        <div className="print-header">
          <h1>暮橙体育销售单</h1>
          <div className="print-order-number">单号: {order.order_number}</div>
        </div>

        <table className="print-info-table">
          <tbody>
            <tr>
              <td>客户名称: {order.customer_name}</td>
              <td>电话: {order.customer_phone}</td>
              <td>销售日期: {order.sales_date}</td>
            </tr>
            <tr>
              <td>送货地址: {order.delivery_address}</td>
              <td>送货日期: {order.delivery_date || "-"}</td>
              <td>付款方式: {order.payment_terms}</td>
            </tr>
          </tbody>
        </table>

        <table className="print-items-table">
          <thead>
            <tr>
              <th>序号</th>
              <th>产品名称</th>
              <th>颜色/规格</th>
              <th>总箱数</th>
              <th>每箱数量</th>
              <th>单价</th>
              <th>小计</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item, idx) => (
              <tr key={item.id}>
                <td>{idx + 1}</td>
                <td>{item.product_name}</td>
                <td>{item.color_spec}</td>
                <td>{item.total_boxes}</td>
                <td>{item.per_box_qty}</td>
                <td>¥{Number(item.unit_price).toFixed(2)}</td>
                <td>
                  ¥{(item.total_boxes * item.per_box_qty * Number(item.unit_price)).toFixed(2)}
                </td>
              </tr>
            ))}
            <tr className="total-row">
              <td colSpan={6} style={{ textAlign: "right", fontWeight: "bold" }}>
                合计
              </td>
              <td style={{ fontWeight: "bold" }}>¥{orderTotal.toFixed(2)}</td>
            </tr>
          </tbody>
        </table>

        {order.notes && (
          <div className="print-notes">备注: {order.notes}</div>
        )}

        <div className="print-footer">
          <div>制单人: ___________</div>
          <div>客户签收: ___________</div>
        </div>
      </div>

      <style>{`
        .print-area {
          max-width: 800px;
          margin: 0 auto;
          padding: 24px;
          background: #fff;
          border: 1px solid #e8e8e8;
          border-radius: 8px;
        }
        .print-header {
          text-align: center;
          margin-bottom: 20px;
        }
        .print-header h1 {
          font-size: 24px;
          margin: 0 0 8px;
          letter-spacing: 4px;
        }
        .print-order-number {
          font-size: 14px;
          color: #666;
        }
        .print-info-table {
          width: 100%;
          margin-bottom: 16px;
          border-collapse: collapse;
        }
        .print-info-table td {
          padding: 6px 8px;
          font-size: 14px;
          width: 33.33%;
        }
        .print-items-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 16px;
        }
        .print-items-table th,
        .print-items-table td {
          border: 1px solid #333;
          padding: 8px;
          text-align: center;
          font-size: 14px;
        }
        .print-items-table th {
          background: #f5f5f5;
          font-weight: 600;
        }
        .total-row td {
          border-top: 2px solid #333;
        }
        .print-notes {
          padding: 8px 0;
          font-size: 14px;
          color: #333;
          border-top: 1px dashed #ccc;
          margin-top: 8px;
        }
        .print-footer {
          display: flex;
          justify-content: space-between;
          margin-top: 40px;
          font-size: 14px;
        }

        @media print {
          body * {
            visibility: hidden;
          }
          .print-area,
          .print-area * {
            visibility: visible;
          }
          .print-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            border: none;
            box-shadow: none;
            padding: 20px;
          }
          .no-print {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
