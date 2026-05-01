import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Row,
  Select,
  Space,
  Table,
} from "antd";
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import {
  purchasesApi,
  type PurchaseOrder,
  type PurchaseOrderForm,
} from "../api/purchases";
import { productsApi, type Product } from "../api/products";
import { suppliersApi, type Supplier } from "../api/suppliers";
import PageToolbar from "../components/PageToolbar";
import { createActionColumn } from "../components/TableActions";

const { RangePicker } = DatePicker;
type View = "list" | "form";

export default function Purchases() {
  const [view, setView] = useState<View>("list");
  const [data, setData] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm<PurchaseOrderForm>();
  const [query, setQuery] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [productName, setProductName] = useState("");
  const [dateRange, setDateRange] = useState<
    [dayjs.Dayjs | null, dayjs.Dayjs | null] | null
  >(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const buildFilters = () => {
    const params: Record<string, unknown> = {};
    if (query) params.q = query;
    if (supplierName) params.supplier_name = supplierName;
    if (productName) params.product_name = productName;
    if (dateRange?.[0]) params.start_date = dateRange[0].format("YYYY-MM-DD");
    if (dateRange?.[1]) params.end_date = dateRange[1].format("YYYY-MM-DD");
    return params;
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const listRes = await purchasesApi.list(buildFilters());
      setData(listRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [query, supplierName, productName, dateRange]);

  useEffect(() => {
    Promise.all([suppliersApi.list(), productsApi.list()]).then(([supplierRes, productRes]) => {
      setSuppliers(supplierRes.data);
      setProducts(productRes.data);
    });
  }, []);

  const resetFilters = () => {
    setQuery("");
    setSupplierName("");
    setProductName("");
    setDateRange(null);
  };

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      purchase_time: dayjs().format("YYYY-MM-DD"),
      paid_amount: 0,
    });
    setView("form");
  };

  const openEdit = (record: PurchaseOrder) => {
    setEditingId(record.id);
    form.setFieldsValue({
      purchase_time: record.purchase_time,
      supplier_name: record.supplier_name,
      product_name: record.product_name,
      box_count: record.box_count,
      per_box_qty: record.per_box_qty,
      unit_price: record.unit_price,
      paid_amount: record.paid_amount,
      notes: record.notes,
    });
    setView("form");
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingId) {
      await purchasesApi.update(editingId, values);
      message.success("修改成功");
    } else {
      await purchasesApi.create(values);
      message.success("新增成功");
    }
    setView("list");
    fetchData();
  };

  const handleDelete = async (id: number) => {
    await purchasesApi.delete(id);
    message.success("删除成功");
    fetchData();
  };

  const columns: ColumnsType<PurchaseOrder> = [
    {
      title: "时间",
      dataIndex: "purchase_time",
      width: 120,
    },
    {
      title: "厂家",
      dataIndex: "supplier_name",
      width: 160,
      ellipsis: true,
    },
    {
      title: "货物",
      dataIndex: "product_name",
      width: 180,
      ellipsis: true,
    },
    { title: "件数", dataIndex: "box_count", width: 80, align: "right" },
    { title: "装箱数", dataIndex: "per_box_qty", width: 90, align: "right" },
    {
      title: "单价",
      dataIndex: "unit_price",
      width: 100,
      align: "right",
      render: (v: number) => `¥${Number(v).toFixed(2)}`,
    },
    { title: "总数量", dataIndex: "total_qty", width: 100, align: "right" },
    {
      title: "金额",
      dataIndex: "total_amount",
      width: 120,
      align: "right",
      render: (v: number) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: "已结金额",
      dataIndex: "paid_amount",
      width: 110,
      align: "right",
      render: (value: number) => `¥${Number(value).toFixed(2)}`,
    },
    { title: "备注", dataIndex: "notes", width: 220, ellipsis: true },
    createActionColumn<PurchaseOrder>(
      [
        { key: "edit", label: "编辑", icon: <EditOutlined />, onClick: openEdit },
        {
          key: "delete",
          label: "删除",
          icon: <DeleteOutlined />,
          danger: true,
          confirmTitle: "确认删除？",
          onClick: (record) => handleDelete(record.id),
        },
      ],
      150,
    ),
  ];

  if (view === "form") {
    return (
      <div>
        <PageToolbar
          title={editingId ? "编辑采购单" : "新增采购单"}
          leading={<Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>}
        />
        <Card>
          <PurchaseForm
            form={form}
            suppliers={suppliers}
            products={products}
            editingId={editingId}
            onSubmit={handleSubmit}
          />
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageToolbar
        title="采购"
        searchValue={query}
        searchPlaceholder="厂家/货物/时间"
        onSearchChange={setQuery}
        onSearch={() => fetchData()}
        primaryText="新增采购"
        primaryIcon={<PlusOutlined />}
        onPrimaryClick={openCreate}
      />

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            showSearch
            allowClear
            placeholder="厂家"
            value={supplierName || undefined}
            onChange={(value) => setSupplierName(value ?? "")}
            optionFilterProp="label"
            style={{ width: 180 }}
            options={suppliers.map((supplier) => ({ label: supplier.name, value: supplier.name }))}
          />
          <Select
            showSearch
            allowClear
            placeholder="货物"
            value={productName || undefined}
            onChange={(value) => setProductName(value ?? "")}
            optionFilterProp="label"
            style={{ width: 180 }}
            options={products.map((product) => ({ label: product.name, value: product.name }))}
          />
          <RangePicker
            allowClear
            placeholder={["开始日期", "结束日期"]}
            value={dateRange as [dayjs.Dayjs, dayjs.Dayjs] | null}
            onChange={(val) =>
              setDateRange(val as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)
            }
          />
          <Button type="primary" onClick={fetchData}>筛选</Button>
          <Button onClick={resetFilters}>重置</Button>
        </Space>
      </Card>

      <Card>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={data}
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
          scroll={{ x: 1280 }}
        />
      </Card>
    </div>
  );
}

function PurchaseForm({
  form,
  suppliers,
  products,
  editingId,
  onSubmit,
}: {
  form: ReturnType<typeof Form.useForm<PurchaseOrderForm>>[0];
  suppliers: Supplier[];
  products: Product[];
  editingId: number | null;
  onSubmit: () => void;
}) {
  const boxCount = Form.useWatch("box_count", form) ?? 0;
  const perBoxQty = Form.useWatch("per_box_qty", form) ?? 0;
  const unitPrice = Form.useWatch("unit_price", form) ?? 0;
  const totalQty = boxCount * perBoxQty;
  const totalAmount = unitPrice * totalQty;
  const remainingAmount = Math.max(totalAmount - (Form.useWatch("paid_amount", form) ?? 0), 0);

  return (
    <Form form={form} layout="vertical" style={{ maxWidth: 760 }}>
      <Form.Item
        label="采购时间"
        name="purchase_time"
        rules={[{ required: true, message: "请选择采购时间" }]}
        getValueProps={(v) => ({ value: v ? dayjs(v) : undefined })}
        getValueFromEvent={(d: dayjs.Dayjs) => d?.format("YYYY-MM-DD")}
      >
        <DatePicker style={{ width: 240 }} />
      </Form.Item>

      <Form.Item
        label="厂家"
        name="supplier_name"
        rules={[{ required: true, message: "请选择厂家" }]}
      >
        <Select
          showSearch
          optionFilterProp="label"
          options={suppliers.map((supplier) => ({
            label: supplier.name,
            value: supplier.name,
          }))}
        />
      </Form.Item>

      <Form.Item
        label="货物"
        name="product_name"
        rules={[{ required: true, message: "请选择货物" }]}
      >
        <Select
          showSearch
          optionFilterProp="label"
          options={products.map((product) => ({
            label: product.name,
            value: product.name,
          }))}
          onChange={(value) => {
            const product = products.find((item) => item.name === value);
            if (product) {
              form.setFieldsValue({
                per_box_qty: product.per_box_qty,
                unit_price: product.purchase_price,
              });
            }
          }}
        />
      </Form.Item>

      <Row gutter={12}>
        <Col span={12}>
          <Form.Item label="件数" name="box_count" rules={[{ required: true, message: "请输入件数" }]}>
            <InputNumber min={0} style={{ width: "100%" }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="装箱数" name="per_box_qty" rules={[{ required: true, message: "请输入装箱数" }]}>
            <InputNumber min={0} style={{ width: "100%" }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="单价" name="unit_price" rules={[{ required: true, message: "请输入单价" }]}>
            <InputNumber min={0} step={0.01} prefix="¥" style={{ width: "100%" }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="已付款"
            name="paid_amount"
            rules={[
              { required: true, message: "请输入已付款金额" },
              {
                validator: async (_, value) => {
                  if (value == null || value <= totalAmount) return;
                  throw new Error("已付款不能大于本单金额");
                },
              },
            ]}
          >
            <InputNumber min={0} step={0.01} prefix="¥" style={{ width: "100%" }} />
          </Form.Item>
        </Col>
      </Row>

      <div style={{ background: "#fafafa", padding: "8px 12px", borderRadius: 6, marginBottom: 16 }}>
        总数量：<strong>{totalQty}</strong> &nbsp;&nbsp; 金额：
        <strong>¥{totalAmount.toFixed(2)}</strong> &nbsp;&nbsp; 未付款：
        <strong>¥{remainingAmount.toFixed(2)}</strong>
      </div>

      <Form.Item label="备注" name="notes">
        <Input.TextArea rows={2} />
      </Form.Item>

      <Button type="primary" onClick={onSubmit}>
        {editingId ? "保存修改" : "保存"}
      </Button>
    </Form>
  );
}
