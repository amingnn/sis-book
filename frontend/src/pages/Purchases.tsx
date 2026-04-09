import { useEffect, useMemo, useState } from "react";
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
import { PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import {
  purchasesApi,
  type PurchaseOrder,
  type PurchaseOrderForm,
} from "../api/purchases";

const { RangePicker } = DatePicker;

export default function Purchases() {
  const [data, setData] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm<PurchaseOrderForm>();
  const [filters, setFilters] = useState<Record<string, unknown>>({});

  const fetchData = async (params?: Record<string, unknown>) => {
    setLoading(true);
    try {
      const res = await purchasesApi.list(params);
      setData(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(filters);
  }, [filters]);

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
    form.setFieldsValue({ purchase_time: dayjs().format("YYYY-MM-DD") });
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

  const totalAmount = useMemo(
    () => data.reduce((sum, r) => sum + Number(r.total_amount), 0),
    [data],
  );

  const columns: ColumnsType<PurchaseOrder> = [
    {
      title: "时间",
      dataIndex: "purchase_time",
      width: 120,
    },
    {
      title: "厂家名称",
      dataIndex: "supplier_name",
    },
    {
      title: "货物名称",
      dataIndex: "product_name",
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
      title: "备注",
      dataIndex: "notes",
      ellipsis: true,
    },
    {
      title: "操作",
      width: 140,
      render: (_, record) => (
        <Space>
          <a onClick={() => openEdit(record)}>编辑</a>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(record.id)}>
            <a style={{ color: "#ff4d4f" }}>删除</a>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>采购单</Typography.Title>

      <FilterBar onSearch={handleSearch} />

      <Card
        title={`共 ${data.length} 条记录`}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新增采购
          </Button>
        }
        style={{ marginTop: 16 }}
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={data}
          loading={loading}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
          summary={() => (
            <Table.Summary fixed>
              <Table.Summary.Row>
                <Table.Summary.Cell index={0} colSpan={7} align="right">
                  <strong>合计金额</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={7} align="right">
                  <strong>¥{totalAmount.toFixed(2)}</strong>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={8} colSpan={2} />
              </Table.Summary.Row>
            </Table.Summary>
          )}
        />
      </Card>

      <PurchaseModal
        open={modalOpen}
        editingId={editingId}
        form={form}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      />
    </div>
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
          value={supplier}
          onChange={(e) => setSupplier(e.target.value)}
          onPressEnter={handleSearch}
          allowClear
          style={{ width: 180 }}
        />
        <Input
          placeholder="货物名称"
          value={product}
          onChange={(e) => setProduct(e.target.value)}
          onPressEnter={handleSearch}
          allowClear
          style={{ width: 180 }}
        />
        <RangePicker
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
          <strong>¥{totalAmount.toFixed(2)}</strong>
        </div>

        <Form.Item label="备注" name="notes">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
