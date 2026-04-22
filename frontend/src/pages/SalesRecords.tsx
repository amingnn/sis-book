import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { useSearchParams } from "react-router-dom";
import {
  salesApi,
  type SalesRecord,
  type SalesRecordForm,
} from "../api/sales";

const { RangePicker } = DatePicker;

export default function SalesRecords() {
  const [searchParams] = useSearchParams();
  const [records, setRecords] = useState<SalesRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm();

  const [customerName, setCustomerName] = useState("");
  const [isSettled, setIsSettled] = useState<boolean | undefined>();
  const [isDueCollection, setIsDueCollection] = useState<boolean | undefined>();
  const [dateRange, setDateRange] = useState<
    [dayjs.Dayjs, dayjs.Dayjs] | null
  >(null);

  useEffect(() => {
    const settledParam = searchParams.get("settled");
    const dueParam = searchParams.get("due");
    if (settledParam === "unsettled" || dueParam === "collection") {
      setIsSettled(false);
    } else {
      setIsSettled(undefined);
    }
    setIsDueCollection(dueParam === "collection" ? true : undefined);
  }, [searchParams]);

  const buildParams = useCallback(() => {
    const params: Record<string, unknown> = {};
    if (customerName) params.customer_name = customerName;
    if (isSettled !== undefined) params.is_settled = isSettled;
    if (isDueCollection) params.due_collection = true;
    if (dateRange) {
      params.start_date = dateRange[0].format("YYYY-MM-DD");
      params.end_date = dateRange[1].format("YYYY-MM-DD");
    }
    return params;
  }, [customerName, isSettled, isDueCollection, dateRange]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = buildParams();
      const listRes = await salesApi.list(params);
      setRecords(listRes.data);
    } catch {
      message.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  }, [buildParams]);

  const handleResetFilters = () => {
    const dueParam = searchParams.get("due");
    setCustomerName("");
    setDateRange(null);
    setIsSettled(dueParam === "collection" ? false : undefined);
    setIsDueCollection(dueParam === "collection" ? true : undefined);
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ sale_time: dayjs(), is_settled: false });
    setModalOpen(true);
  };

  const handleEdit = (record: SalesRecord) => {
    setEditingId(record.id);
    form.setFieldsValue({
      ...record,
      sale_time: dayjs(record.sale_time),
      delivery_time: record.delivery_time ? dayjs(record.delivery_time) : null,
      collection_time: record.collection_time ? dayjs(record.collection_time) : null,
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await salesApi.delete(id);
      message.success("删除成功");
      fetchData();
    } catch {
      message.error("删除失败");
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data: SalesRecordForm = {
        ...values,
        sale_time: values.sale_time.format("YYYY-MM-DD"),
        delivery_time: values.delivery_time?.format("YYYY-MM-DD") ?? null,
        collection_time: values.collection_time?.format("YYYY-MM-DD") ?? null,
      };
      if (editingId) {
        await salesApi.update(editingId, data);
        message.success("更新成功");
      } else {
        await salesApi.create(data);
        message.success("新增成功");
      }
      setModalOpen(false);
      fetchData();
    } catch {
      /* form validation or API error */
    }
  };

  const columns: ColumnsType<SalesRecord> = [
    { title: "时间", dataIndex: "sale_time", width: 120 },
    { title: "客户名称", dataIndex: "customer_name", width: 120 },
    { title: "产品", dataIndex: "product", width: 120 },
    {
      title: "金额",
      dataIndex: "amount",
      width: 110,
      align: "right",
      render: (v: number | string) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: "收货时间",
      dataIndex: "delivery_time",
      width: 120,
      render: (v: string) => v || "-",
    },
    {
      title: "收款时间",
      dataIndex: "collection_time",
      width: 120,
      render: (v: string | null, record) => {
        if (!v) return "-";
        const isDue = !record.is_settled && dayjs(v).isBefore(dayjs().add(1, "day"), "day");
        return isDue ? <Tag color="orange">{v}</Tag> : v;
      },
    },
    {
      title: "是否结清",
      dataIndex: "is_settled",
      width: 90,
      align: "center",
      render: (v: boolean) => (
        <Tag color={v ? "green" : "red"}>{v ? "已结清" : "未结清"}</Tag>
      ),
    },
    { title: "交易方式", dataIndex: "payment_method", width: 100 },
    {
      title: "成本",
      dataIndex: "cost",
      width: 110,
      align: "right",
      render: (v: number | string) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: "毛利润",
      dataIndex: "gross_profit",
      width: 110,
      align: "right",
      render: (v: number | string) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: "利润率",
      dataIndex: "profit_margin",
      width: 100,
      align: "right",
      render: (v: number | string) => `${Number(v).toFixed(2)}%`,
    },
    {
      title: "备注",
      dataIndex: "notes",
      width: 220,
      ellipsis: true,
    },
    {
      title: "操作",
      width: 110,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
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
          销售记录
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增销售记录
        </Button>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Input
            placeholder="客户名称"
            prefix={<SearchOutlined />}
            allowClear
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            onPressEnter={() => fetchData()}
            style={{ width: 180 }}
          />
          <Select
            placeholder="是否结清"
            allowClear
            value={isSettled}
            onChange={(v) => setIsSettled(v)}
            style={{ width: 120 }}
            options={[
              { label: "已结清", value: true },
              { label: "未结清", value: false },
            ]}
          />
          <Select
            placeholder="是否到期"
            allowClear
            value={isDueCollection}
            onChange={(v) => setIsDueCollection(v)}
            style={{ width: 120 }}
            options={[
              { label: "已到期", value: true },
            ]}
          />
          <RangePicker
            allowClear
            placeholder={["开始日期", "结束日期"]}
            value={dateRange}
            onChange={(dates) =>
              setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)
            }
          />
          <Button type="primary" onClick={fetchData}>
            查询
          </Button>
          <Button onClick={handleResetFilters}>重置</Button>
        </Space>
      </Card>

      <Card>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={records}
          loading={loading}
          scroll={{ x: 1490 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>

      <Modal
        title={editingId ? "编辑销售记录" : "新增销售记录"}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={600}
        destroyOnHidden
      >
        <Form form={form} layout="vertical">
          <Space style={{ display: "flex", gap: 16 }}>
            <Form.Item
              name="sale_time"
              label="销售时间"
              rules={[{ required: true, message: "请选择时间" }]}
            >
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item
              name="customer_name"
              label="客户名称"
              rules={[{ required: true, message: "请输入客户名称" }]}
            >
              <Input />
            </Form.Item>
          </Space>
          <Form.Item
            name="product"
            label="产品"
            rules={[{ required: true, message: "请输入产品" }]}
          >
            <Input />
          </Form.Item>
          <Space style={{ display: "flex", gap: 16 }}>
            <Form.Item
              name="amount"
              label="金额"
              rules={[{ required: true, message: "请输入金额" }]}
            >
              <InputNumber min={0} precision={2} style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item
              name="cost"
              label="成本"
              rules={[{ required: true, message: "请输入成本" }]}
            >
              <InputNumber min={0} precision={2} style={{ width: "100%" }} />
            </Form.Item>
          </Space>
          <Space style={{ display: "flex", gap: 16 }}>
            <Form.Item name="delivery_time" label="收货时间">
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="collection_time" label="收款时间">
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>
          </Space>
          <Space style={{ display: "flex", gap: 16 }}>
            <Form.Item name="payment_method" label="交易方式">
              <Input />
            </Form.Item>
          </Space>
          <Form.Item name="is_settled" label="是否结清" valuePropName="checked">
            <Switch checkedChildren="已结清" unCheckedChildren="未结清" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
