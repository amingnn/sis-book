import { useCallback, useEffect, useRef, useState } from "react";
import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { useSearchParams } from "react-router-dom";
import {
  salesApi,
  type SalesRecord,
  type SalesRecordForm,
} from "../api/sales";
import { customersApi, type Customer } from "../api/customers";
import { productsApi, type Product } from "../api/products";
import PageToolbar from "../components/PageToolbar";
import { createActionColumn } from "../components/TableActions";

const { RangePicker } = DatePicker;
type View = "list" | "form";
type SettlementFilter = "due" | "unsettled" | "settled" | undefined;
const routeFilterKeys = ["q", "customer_name", "product", "payment_method", "due", "settled"];

function getSettlementFilterFromParams(searchParams: URLSearchParams): SettlementFilter {
  const settledParam = searchParams.get("settled");
  const dueParam = searchParams.get("due");
  if (dueParam === "collection") return "due";
  if (settledParam === "unsettled") return "unsettled";
  if (settledParam === "settled") return "settled";
  return undefined;
}

function hasRouteFilters(searchParams: URLSearchParams): boolean {
  return routeFilterKeys.some((key) => searchParams.has(key));
}

export default function SalesRecords() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [view, setView] = useState<View>("list");
  const [records, setRecords] = useState<SalesRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const requestIdRef = useRef(0);
  const suppressNextEmptyParamSyncRef = useRef(false);
  const [form] = Form.useForm();

  const [query, setQuery] = useState(() => searchParams.get("q") ?? "");
  const [customerName, setCustomerName] = useState(() => searchParams.get("customer_name") ?? "");
  const [productName, setProductName] = useState(() => searchParams.get("product") ?? "");
  const [settlementFilter, setSettlementFilter] = useState<SettlementFilter>(() =>
    getSettlementFilterFromParams(searchParams),
  );
  const [paymentMethod, setPaymentMethod] = useState(() => searchParams.get("payment_method") ?? "");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [dateRange, setDateRange] = useState<
    [dayjs.Dayjs, dayjs.Dayjs] | null
  >(null);

  useEffect(() => {
    const hasRouteFilter = hasRouteFilters(searchParams);
    if (hasRouteFilter) {
      suppressNextEmptyParamSyncRef.current = false;
      setQuery(searchParams.get("q") ?? "");
      setCustomerName(searchParams.get("customer_name") ?? "");
      setProductName(searchParams.get("product") ?? "");
      setPaymentMethod(searchParams.get("payment_method") ?? "");
      setSettlementFilter(getSettlementFilterFromParams(searchParams));
      return;
    }

    if (suppressNextEmptyParamSyncRef.current) {
      suppressNextEmptyParamSyncRef.current = false;
      return;
    }

    setSettlementFilter(undefined);
  }, [searchParams]);

  const buildParams = useCallback(() => {
    const params: Record<string, unknown> = {};
    if (query) params.q = query;
    if (customerName) params.customer_name = customerName;
    if (productName) params.product = productName;
    if (paymentMethod) params.payment_method = paymentMethod;
    if (settlementFilter === "settled") params.is_settled = true;
    if (settlementFilter === "unsettled") params.is_settled = false;
    if (settlementFilter === "due") {
      params.is_settled = false;
      params.due_collection = true;
    }
    if (dateRange) {
      params.start_date = dateRange[0].format("YYYY-MM-DD");
      params.end_date = dateRange[1].format("YYYY-MM-DD");
    }
    return params;
  }, [query, customerName, productName, paymentMethod, settlementFilter, dateRange]);

  const fetchData = useCallback(async () => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setLoading(true);
    try {
      const params = buildParams();
      const listRes = await salesApi.list(params);
      if (requestId === requestIdRef.current) {
        setRecords(listRes.data);
      }
    } catch {
      if (requestId === requestIdRef.current) {
        message.error("加载数据失败");
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }, [buildParams]);

  const clearRouteFilters = useCallback(() => {
    if (hasRouteFilters(searchParams)) {
      suppressNextEmptyParamSyncRef.current = true;
      setSearchParams({});
    }
  }, [searchParams, setSearchParams]);

  const handleResetFilters = () => {
    setQuery("");
    setCustomerName("");
    setProductName("");
    setPaymentMethod("");
    setDateRange(null);
    setSettlementFilter(undefined);
    clearRouteFilters();
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    Promise.all([customersApi.list(), productsApi.list()]).then(([customerRes, productRes]) => {
      setCustomers(customerRes.data);
      setProducts(productRes.data);
    });
  }, []);

  const handleAdd = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ sale_time: dayjs(), is_settled: false });
    setView("form");
  };

  const handleEdit = (record: SalesRecord) => {
    setEditingId(record.id);
    form.setFieldsValue({
      ...record,
      sale_time: dayjs(record.sale_time),
      delivery_time: record.delivery_time ? dayjs(record.delivery_time) : null,
      collection_time: record.collection_time ? dayjs(record.collection_time) : null,
    });
    setView("form");
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
      setView("list");
      fetchData();
    } catch {
      /* form validation or API error */
    }
  };

  const columns: ColumnsType<SalesRecord> = [
    {
      title: "销售时间",
      dataIndex: "sale_time",
      width: 120,
    },
    {
      title: "客户",
      dataIndex: "customer_name",
      width: 120,
      render: (value: string) => (
        <Button type="link" onClick={() => setCustomerName(value)}>
          {value}
        </Button>
      ),
    },
    {
      title: "产品",
      dataIndex: "product",
      width: 120,
      render: (value: string) => (
        <Button type="link" onClick={() => setProductName(value)}>
          {value}
        </Button>
      ),
    },
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
        <Tag
          color={v ? "green" : "red"}
          style={{ cursor: "pointer" }}
          onClick={() => {
            clearRouteFilters();
            setSettlementFilter(v ? "settled" : "unsettled");
          }}
        >
          {v ? "已结清" : "未结清"}
        </Tag>
      ),
    },
    {
      title: "交易方式",
      dataIndex: "payment_method",
      width: 100,
      render: (value: string) => value ? <Button type="link" onClick={() => setPaymentMethod(value)}>{value}</Button> : "-",
    },
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
    createActionColumn<SalesRecord>([
      { key: "edit", label: "编辑", icon: <EditOutlined />, onClick: handleEdit },
      {
        key: "delete",
        label: "删除",
        icon: <DeleteOutlined />,
        danger: true,
        confirmTitle: "确认删除？",
        onClick: (record) => handleDelete(record.id),
      },
    ]),
    // 180
  ];

  if (view === "form") {
    return (
      <div>
        <PageToolbar
          title={editingId ? "编辑销售记录" : "新增销售记录"}
          leading={<Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>}
        />
        <Card>
          <Form form={form} layout="vertical" style={{ maxWidth: 720 }}>
            <Space style={{ display: "flex", gap: 16 }} wrap>
              <Form.Item
                name="sale_time"
                label="销售时间"
                rules={[{ required: true, message: "请选择时间" }]}
              >
                <DatePicker style={{ width: 200 }} />
              </Form.Item>
              <Form.Item
                name="customer_name"
                label="客户"
                rules={[{ required: true, message: "请选择客户" }]}
              >
                <Select
                  showSearch
                  optionFilterProp="label"
                  style={{ width: 220 }}
                  options={customers.map((customer) => ({
                    label: customer.name,
                    value: customer.name,
                  }))}
                />
              </Form.Item>
            </Space>
            <Form.Item
              name="product"
              label="产品"
              rules={[{ required: true, message: "请选择产品" }]}
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
                    form.setFieldsValue({ cost: product.purchase_price });
                  }
                }}
              />
            </Form.Item>
            <Space style={{ display: "flex", gap: 16 }} wrap>
              <Form.Item
                name="amount"
                label="金额"
                rules={[{ required: true, message: "请输入金额" }]}
              >
                <InputNumber min={0} precision={2} style={{ width: 200 }} />
              </Form.Item>
              <Form.Item
                name="cost"
                label="成本"
                rules={[{ required: true, message: "请输入成本" }]}
              >
                <InputNumber min={0} precision={2} style={{ width: 200 }} />
              </Form.Item>
            </Space>
            <Space style={{ display: "flex", gap: 16 }} wrap>
              <Form.Item name="delivery_time" label="收货时间">
                <DatePicker style={{ width: 200 }} />
              </Form.Item>
              <Form.Item name="collection_time" label="收款时间">
                <DatePicker style={{ width: 200 }} />
              </Form.Item>
            </Space>
            <Form.Item name="payment_method" label="交易方式">
              <Select
                showSearch
                allowClear
                style={{ width: 240 }}
                options={["现金", "微信", "支付宝", "银行转账", "月结", "45天", "30天"].map((item) => ({
                  label: item,
                  value: item,
                }))}
              />
            </Form.Item>
            <Form.Item name="is_settled" label="是否结清" valuePropName="checked">
              <Switch checkedChildren="已结清" unCheckedChildren="未结清" />
            </Form.Item>
            <Form.Item name="notes" label="备注">
              <Input.TextArea rows={2} />
            </Form.Item>
            <Button type="primary" onClick={handleSubmit}>
              {editingId ? "保存修改" : "保存"}
            </Button>
          </Form>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageToolbar
        title="销售"
        searchValue={query}
        searchPlaceholder="模糊搜索"
        onSearchChange={setQuery}
        onSearch={() => fetchData()}
        primaryText="新增销售记录"
        primaryIcon={<PlusOutlined />}
        onPrimaryClick={handleAdd}
      />

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            showSearch
            allowClear
            placeholder="客户"
            value={customerName || undefined}
            onChange={(value) => setCustomerName(value ?? "")}
            optionFilterProp="label"
            style={{ width: 180 }}
            options={customers.map((customer) => ({
              label: customer.name,
              value: customer.name,
            }))}
          />
          <Select
            showSearch
            allowClear
            placeholder="产品"
            value={productName || undefined}
            onChange={(value) => setProductName(value ?? "")}
            optionFilterProp="label"
            style={{ width: 180 }}
            options={products.map((product) => ({
              label: product.name,
              value: product.name,
            }))}
          />
          <Select
            placeholder="是否结清"
            allowClear
            value={settlementFilter}
            onChange={(value) => {
              clearRouteFilters();
              setSettlementFilter(value);
            }}
            style={{ width: 160 }}
            options={[
              { label: "到期/超时", value: "due" },
              { label: "未结清", value: "unsettled" },
              { label: "已结清", value: "settled" },
            ]}
          />
          <Select
            showSearch
            allowClear
            placeholder="交易方式"
            value={paymentMethod || undefined}
            onChange={(value) => setPaymentMethod(value ?? "")}
            style={{ width: 150 }}
            options={["现金", "微信", "支付宝", "银行转账", "月结", "45天", "30天"].map((item) => ({
              label: item,
              value: item,
            }))}
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
            筛选
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
            showSizeChanger: false,
            showTotal: (t) => `共 ${t} 条`,
          }}
        />
      </Card>
    </div>
  );
}
