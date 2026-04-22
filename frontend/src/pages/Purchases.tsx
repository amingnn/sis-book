import { useEffect, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  message,
  Modal,
  Popconfirm,
  Space,
  Table,
  Typography,
} from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import {
  purchasesApi,
  type PurchaseOrder,
  type PurchaseOrderForm,
  type PurchaseOrderPage,
} from "../api/purchases";

const { RangePicker } = DatePicker;

export default function Purchases() {
  const [data, setData] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [supplierHistoryOpen, setSupplierHistoryOpen] = useState(false);
  const [supplierHistoryName, setSupplierHistoryName] = useState("");
  const [supplierHistory, setSupplierHistory] = useState<PurchaseOrderPage | null>(null);
  const [supplierHistoryLoading, setSupplierHistoryLoading] = useState(false);
  const [form] = Form.useForm<PurchaseOrderForm>();
  const [filters, setFilters] = useState<Record<string, unknown>>({});

  const fetchData = async (params?: Record<string, unknown>) => {
    setLoading(true);
    try {
      const listRes = await purchasesApi.list(params);
      setData(listRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(filters);
  }, [filters]);

  const fetchSupplierHistory = async (
    supplierName: string,
    page = 1,
    pageSize = 10,
  ) => {
    setSupplierHistoryLoading(true);
    try {
      const res = await purchasesApi.supplierHistory({
        supplier_name: supplierName,
        page,
        page_size: pageSize,
      });
      setSupplierHistory(res.data);
    } finally {
      setSupplierHistoryLoading(false);
    }
  };

  const openSupplierHistory = async (supplierName: string) => {
    setSupplierHistoryName(supplierName);
    setSupplierHistoryOpen(true);
    await fetchSupplierHistory(supplierName);
  };

  const handleSearch = (
    supplierName: string,
    productName: string,
    dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null,
  ) => {
    const params: Record<string, unknown> = {};
    if (supplierName) params.supplier_name = supplierName;
    if (productName) params.product_name = productName;
    if (dates?.[0]) params.start_date = dates[0].format("YYYY-MM-DD");
    if (dates?.[1]) params.end_date = dates[1].format("YYYY-MM-DD");
    setFilters(params);
  };

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      purchase_time: dayjs().format("YYYY-MM-DD"),
      paid_amount: 0,
    });
    setModalOpen(true);
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
    setModalOpen(true);
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
    setModalOpen(false);
    fetchData(filters);
  };

  const handleDelete = async (id: number) => {
    await purchasesApi.delete(id);
    message.success("删除成功");
    fetchData(filters);
  };

  const columns: ColumnsType<PurchaseOrder> = [
    {
      title: "时间",
      dataIndex: "purchase_time",
      width: 120,
    },
    {
      title: "厂家名称",
      dataIndex: "supplier_name",
      width: 160,
      ellipsis: true,
      render: (value: string) => <a onClick={() => openSupplierHistory(value)}>{value}</a>,
    },
    {
      title: "货物名称",
      dataIndex: "product_name",
      width: 180,
      ellipsis: true,
    },
    {
      title: "件数",
      dataIndex: "box_count",
      width: 80,
      align: "right",
    },
    {
      title: "装箱数",
      dataIndex: "per_box_qty",
      width: 90,
      align: "right",
    },
    {
      title: "单价",
      dataIndex: "unit_price",
      width: 100,
      align: "right",
      render: (v: number) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: "总数量",
      dataIndex: "total_qty",
      width: 100,
      align: "right",
    },
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
    {
      title: "备注",
      dataIndex: "notes",
      width: 220,
      ellipsis: true,
    },
    {
      title: "操作",
      key: "actions",
      width: 220,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => openSupplierHistory(record.supplier_name)}
          >
            查看
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          采购单
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新增采购
        </Button>
      </div>

      <FilterBar onSearch={handleSearch} />

      <Card style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={data}
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
          scroll={{ x: 1380 }}
        />
      </Card>

      <PurchaseModal
        open={modalOpen}
        editingId={editingId}
        form={form}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      />

      <SupplierHistoryModal
        open={supplierHistoryOpen}
        supplierName={supplierHistoryName}
        data={supplierHistory}
        loading={supplierHistoryLoading}
        onClose={() => setSupplierHistoryOpen(false)}
        onChangePage={(page, pageSize) => {
          if (!supplierHistoryName) {
            return;
          }
          fetchSupplierHistory(supplierHistoryName, page, pageSize);
        }}
      />
    </div>
  );
}

function SupplierHistoryModal({
  open,
  supplierName,
  data,
  loading,
  onClose,
  onChangePage,
}: {
  open: boolean;
  supplierName: string;
  data: PurchaseOrderPage | null;
  loading: boolean;
  onClose: () => void;
  onChangePage: (page: number, pageSize: number) => void;
}) {
  const columns: ColumnsType<PurchaseOrder> = [
    { title: "时间", dataIndex: "purchase_time", width: 120 },
    { title: "货物名称", dataIndex: "product_name", width: 180, ellipsis: true },
    { title: "件数", dataIndex: "box_count", width: 80, align: "right" },
    { title: "装箱数", dataIndex: "per_box_qty", width: 90, align: "right" },
    {
      title: "金额",
      dataIndex: "total_amount",
      width: 120,
      align: "right",
      render: (value: number) => `¥${Number(value).toFixed(2)}`,
    },
    {
      title: "已结多少钱",
      dataIndex: "paid_amount",
      width: 120,
      align: "right",
      render: (value: number) => `¥${Number(value).toFixed(2)}`,
    },
    { title: "备注", dataIndex: "notes", width: 220, ellipsis: true },
  ];

  return (
    <Modal
      title={supplierName ? `${supplierName} 厂家历史` : "厂家历史"}
      open={open}
      onCancel={onClose}
      footer={null}
      width={960}
      destroyOnHidden
    >
      <Table
        style={{ marginTop: 16 }}
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={loading}
        scroll={{ x: 980 }}
        pagination={{
          current: data?.page ?? 1,
          pageSize: data?.page_size ?? 10,
          total: data?.total ?? 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: onChangePage,
        }}
      />
    </Modal>
  );
}

function FilterBar({
  onSearch,
}: {
  onSearch: (
    supplier: string,
    product: string,
    dates: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null,
  ) => void;
}) {
  const [supplier, setSupplier] = useState("");
  const [product, setProduct] = useState("");
  const [dates, setDates] = useState<
    [dayjs.Dayjs | null, dayjs.Dayjs | null] | null
  >(null);

  const handleSearch = () => onSearch(supplier, product, dates);

  const handleReset = () => {
    setSupplier("");
    setProduct("");
    setDates(null);
    onSearch("", "", null);
  };

  return (
    <Card>
      <Space wrap>
        <Input
          placeholder="厂家名称"
          prefix={<SearchOutlined />}
          value={supplier}
          onChange={(e) => setSupplier(e.target.value)}
          onPressEnter={handleSearch}
          allowClear
          style={{ width: 180 }}
        />
        <Input
          placeholder="货物名称"
          prefix={<SearchOutlined />}
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          onPressEnter={handleSearch}
          allowClear
          style={{ width: 180 }}
        />
        <RangePicker
          allowClear
          placeholder={["开始日期", "结束日期"]}
          value={dates as [dayjs.Dayjs, dayjs.Dayjs] | null}
          onChange={(val) =>
            setDates(val as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)
          }
        />
        <Button type="primary" onClick={handleSearch}>
          查询
        </Button>
        <Button onClick={handleReset}>重置</Button>
      </Space>
    </Card>
  );
}

function PurchaseModal({
  open,
  editingId,
  form,
  onOk,
  onCancel,
}: {
  open: boolean;
  editingId: number | null;
  form: ReturnType<typeof Form.useForm<PurchaseOrderForm>>[0];
  onOk: () => void;
  onCancel: () => void;
}) {
  const boxCount = Form.useWatch("box_count", form) ?? 0;
  const perBoxQty = Form.useWatch("per_box_qty", form) ?? 0;
  const unitPrice = Form.useWatch("unit_price", form) ?? 0;
  const totalQty = boxCount * perBoxQty;
  const totalAmount = unitPrice * totalQty;
  const remainingAmount = Math.max(totalAmount - (Form.useWatch("paid_amount", form) ?? 0), 0);

  return (
    <Modal
      title={editingId ? "编辑采购单" : "新增采购单"}
      open={open}
      onOk={onOk}
      onCancel={onCancel}
      width={560}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item
          label="采购时间"
          name="purchase_time"
          rules={[{ required: true, message: "请选择采购时间" }]}
          getValueProps={(v) => ({ value: v ? dayjs(v) : undefined })}
          getValueFromEvent={(d: dayjs.Dayjs) => d?.format("YYYY-MM-DD")}
        >
          <DatePicker style={{ width: "100%" }} />
        </Form.Item>

        <Form.Item
          label="厂家名称"
          name="supplier_name"
          rules={[{ required: true, message: "请输入厂家名称" }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="货物名称"
          name="product_name"
          rules={[{ required: true, message: "请输入货物名称" }]}
        >
          <Input />
        </Form.Item>

        <Space style={{ width: "100%" }}>
          <Form.Item
            label="件数"
            name="box_count"
            rules={[{ required: true, message: "请输入件数" }]}
          >
            <InputNumber min={0} style={{ width: 150 }} />
          </Form.Item>

          <Form.Item
            label="装箱数"
            name="per_box_qty"
            rules={[{ required: true, message: "请输入装箱数" }]}
          >
            <InputNumber min={0} style={{ width: 150 }} />
          </Form.Item>

          <Form.Item
            label="单价"
            name="unit_price"
            rules={[{ required: true, message: "请输入单价" }]}
          >
            <InputNumber min={0} step={0.01} prefix="¥" style={{ width: 150 }} />
          </Form.Item>

          <Form.Item
            label="已付款"
            name="paid_amount"
            rules={[
              { required: true, message: "请输入已付款金额" },
              {
                validator: async (_, value) => {
                  if (value == null || value <= totalAmount) {
                    return;
                  }
                  throw new Error("已付款不能大于本单金额");
                },
              },
            ]}
          >
            <InputNumber min={0} step={0.01} prefix="¥" style={{ width: 150 }} />
          </Form.Item>
        </Space>

        <div
          style={{
            background: "#fafafa",
            padding: "8px 12px",
            borderRadius: 6,
            marginBottom: 16,
          }}
        >
          总数量：<strong>{totalQty}</strong> &nbsp;&nbsp; 金额：
          <strong>¥{totalAmount.toFixed(2)}</strong> &nbsp;&nbsp; 未付款：
          <strong>¥{remainingAmount.toFixed(2)}</strong>
        </div>

        <Form.Item label="备注" name="notes">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
