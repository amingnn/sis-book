import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { ordersApi, type SalesOrder } from "../api/orders";
import { purchasesApi, type PurchaseOrder } from "../api/purchases";
import { salesApi, type SalesRecord } from "../api/sales";
import { tasksApi, type Task, type TaskForm, type TaskPriority, type TaskStatus } from "../api/tasks";
import PageToolbar from "../components/PageToolbar";
import { createActionColumn } from "../components/TableActions";

const statusOptions: Array<{ label: string; value: TaskStatus }> = [
  { label: "待处理", value: "todo" },
  { label: "进行中", value: "doing" },
  { label: "已完成", value: "done" },
];

const priorityOptions: Array<{ label: string; value: TaskPriority }> = [
  { label: "高", value: "high" },
  { label: "中", value: "medium" },
  { label: "低", value: "low" },
];

const relatedTypeOptions = [
  { label: "无关联", value: "" },
  { label: "销售记录", value: "sales" },
  { label: "采购单", value: "purchases" },
  { label: "开单", value: "orders" },
];

const statusColorMap: Record<TaskStatus, string> = {
  todo: "default",
  doing: "processing",
  done: "success",
};

const statusLabelMap: Record<TaskStatus, string> = {
  todo: "待处理",
  doing: "进行中",
  done: "已完成",
};

const priorityColorMap: Record<TaskPriority, string> = {
  high: "red",
  medium: "orange",
  low: "blue",
};

const priorityLabelMap: Record<TaskPriority, string> = {
  high: "高优先级",
  medium: "中优先级",
  low: "低优先级",
};

interface RelatedOption {
  label: string;
  value: number;
}
type View = "list" | "form";

const relatedTypeLabelMap: Record<string, string> = {
  sales: "销售记录",
  purchases: "采购单",
  orders: "开单",
};

export default function Tasks() {
  const [view, setView] = useState<View>("list");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<TaskStatus | undefined>();
  const [priority, setPriority] = useState<TaskPriority | undefined>();
  const [category, setCategory] = useState("");
  const [relatedType, setRelatedType] = useState("");
  const [relatedOptions, setRelatedOptions] = useState<RelatedOption[]>([]);
  const [relatedSearching, setRelatedSearching] = useState(false);
  const [form] = Form.useForm();

  const categories = useMemo(() => {
    const allCategories = tasks.map((task) => task.category).filter(Boolean);
    return Array.from(new Set(allCategories));
  }, [tasks]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (keyword) params.keyword = keyword;
      if (status) params.status = status;
      if (priority) params.priority = priority;
      if (category) params.category = category;
      const res = await tasksApi.list(params);
      setTasks(res.data);
    } catch {
      message.error("加载任务失败");
    } finally {
      setLoading(false);
    }
  }, [category, keyword, priority, status]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdd = () => {
    setEditingId(null);
    setRelatedType("");
    setRelatedOptions([]);
    form.resetFields();
    form.setFieldsValue({
      category: "其他",
      priority: "medium",
      status: "todo",
    });
    setView("form");
  };

  const handleEdit = (task: Task) => {
    setEditingId(task.id);
    setRelatedType(task.related_type);
    setRelatedOptions(
      task.related_type && task.related_id
        ? [
            {
              value: task.related_id,
              label: `${relatedTypeLabelMap[task.related_type] ?? task.related_type} #${task.related_id}`,
            },
          ]
        : [],
    );
    form.setFieldsValue({
      ...task,
      due_date: task.due_date ? dayjs(task.due_date) : null,
    });
    setView("form");
  };

  const handleDelete = async (id: number) => {
    try {
      await tasksApi.delete(id);
      message.success("删除成功");
      fetchData();
    } catch {
      message.error("删除失败");
    }
  };

  const handleQuickStatus = async (task: Task, nextStatus: TaskStatus) => {
    try {
      await tasksApi.updateStatus(task.id, nextStatus);
      message.success("状态已更新");
      fetchData();
    } catch {
      message.error("状态更新失败");
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload: TaskForm = {
        ...values,
        due_date: values.due_date?.format("YYYY-MM-DD") ?? null,
      };
      if (editingId) {
        await tasksApi.update(editingId, payload);
        message.success("任务已更新");
      } else {
        await tasksApi.create(payload);
        message.success("任务已创建");
      }
      setView("list");
      fetchData();
    } catch {
      /* form validation or API error */
    }
  };

  const handleReset = () => {
    setKeyword("");
    setStatus(undefined);
    setPriority(undefined);
    setCategory("");
  };

  const searchRelatedOptions = useCallback(
    async (type: string, searchText: string) => {
      if (!type) {
        setRelatedOptions([]);
        return;
      }

      setRelatedSearching(true);
      try {
        if (type === "sales") {
          const res = await salesApi.list({ customer_name: searchText || undefined });
          setRelatedOptions(
            res.data.slice(0, 20).map((item: SalesRecord) => ({
              value: item.id,
              label: `#${item.id} ${item.customer_name} - ${item.product}`,
            })),
          );
          return;
        }

        if (type === "purchases") {
          const res = await purchasesApi.list({
            supplier_name: searchText || undefined,
            product_name: searchText || undefined,
          });
          setRelatedOptions(
            res.data.slice(0, 20).map((item: PurchaseOrder) => ({
              value: item.id,
              label: `#${item.id} ${item.supplier_name} - ${item.product_name}`,
            })),
          );
          return;
        }

        if (type === "orders") {
          const res = await ordersApi.list({
            customer_name: searchText || undefined,
            order_number: searchText || undefined,
          });
          setRelatedOptions(
            res.data.slice(0, 20).map((item: SalesOrder) => ({
              value: item.id,
              label: `#${item.id} ${item.order_number || "未编号"} - ${item.customer_name}`,
            })),
          );
        }
      } finally {
        setRelatedSearching(false);
      }
    },
    [],
  );

  const columns: ColumnsType<Task> = [
    {
      title: "任务",
      dataIndex: "title",
      width: 220,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 600 }}>{record.title}</div>
          {record.description ? (
            <Typography.Text type="secondary">{record.description}</Typography.Text>
          ) : null}
        </div>
      ),
    },
    {
      title: "分类",
      dataIndex: "category",
      width: 100,
      render: (value: string) => <Tag>{value || "其他"}</Tag>,
    },
    {
      title: "优先级",
      dataIndex: "priority",
      width: 110,
      render: (value: TaskPriority) => (
        <Tag color={priorityColorMap[value]}>{priorityLabelMap[value]}</Tag>
      ),
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 100,
      render: (value: TaskStatus) => (
        <Tag color={statusColorMap[value]}>{statusLabelMap[value]}</Tag>
      ),
    },
    {
      title: "截止日期",
      dataIndex: "due_date",
      width: 130,
      render: (value: string | null, record) => {
        if (!value) return "-";
        const overdue = record.status !== "done" && dayjs(value).isBefore(dayjs(), "day");
        return overdue ? <Tag color="error">{value}</Tag> : value;
      },
    },
    {
      title: "关联",
      width: 140,
      render: (_, record) => {
        if (!record.related_type || !record.related_id) return "-";
        return `${relatedTypeLabelMap[record.related_type] ?? record.related_type} #${record.related_id}`;
      },
    },
    {
      title: "备注",
      dataIndex: "notes",
      width: 180,
      ellipsis: true,
    },
    createActionColumn<Task>(
      [
        {
          key: "status",
          label: (record) => (record.status !== "done" ? "完成" : "重开"),
          icon: <CheckCircleOutlined />,
          onClick: (record) =>
            handleQuickStatus(record, record.status !== "done" ? "done" : "todo"),
        },
        { key: "edit", label: "编辑", icon: <EditOutlined />, onClick: handleEdit },
        {
          key: "delete",
          label: "删除",
          icon: <DeleteOutlined />,
          danger: true,
          confirmTitle: "确认删除这个任务？",
          onClick: (record) => handleDelete(record.id),
        },
      ],
      220,
    ),
  ];

  if (view === "form") {
    return (
      <div>
        <PageToolbar
          title={editingId ? "编辑任务" : "新增任务"}
          leading={<Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>}
        />
        <Card>
          <Form form={form} layout="vertical" style={{ maxWidth: 900 }}>
            <Form.Item name="title" label="任务标题" rules={[{ required: true, message: "请输入任务标题" }]}>
              <Input placeholder="例如：跟进未结清订单" />
            </Form.Item>
            <Form.Item name="description" label="任务说明">
              <Input.TextArea rows={3} placeholder="补充任务背景或执行要求" />
            </Form.Item>
            <Row gutter={12}>
              <Col span={8}>
                <Form.Item name="category" label="分类" initialValue="其他">
                  <Input placeholder="例如：催款、采购、发货" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="priority" label="优先级" initialValue="medium">
                  <Select options={priorityOptions} />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="status" label="状态" initialValue="todo">
                  <Select options={statusOptions} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={12}>
              <Col span={8}>
                <Form.Item name="due_date" label="截止日期">
                  <DatePicker style={{ width: "100%" }} />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="related_type" label="关联类型" initialValue="">
                  <Select
                    options={relatedTypeOptions}
                    onChange={(value) => {
                      setRelatedType(value);
                      setRelatedOptions([]);
                      form.setFieldValue("related_id", undefined);
                      if (value) {
                        searchRelatedOptions(value, "");
                      }
                    }}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="related_id" label="关联记录">
                  <Select
                    showSearch
                    allowClear
                    filterOption={false}
                    disabled={!relatedType}
                    placeholder={relatedType ? "输入关键词搜索并选择" : "请先选择关联类型"}
                    options={relatedOptions}
                    loading={relatedSearching}
                    onSearch={(value) => searchRelatedOptions(relatedType, value)}
                  />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="notes" label="备注">
              <Input.TextArea rows={2} placeholder="执行备注、风险点、补充信息" />
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
        title="任务"
        searchValue={keyword}
        searchPlaceholder="任务/分类/时间"
        onSearchChange={setKeyword}
        onSearch={() => fetchData()}
        primaryText="新增任务"
        primaryIcon={<PlusOutlined />}
        onPrimaryClick={handleAdd}
      />
      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <Select
            placeholder="状态"
            allowClear
            value={status}
            onChange={(value) => setStatus(value)}
            options={statusOptions}
            style={{ width: 120 }}
          />
          <Select
            placeholder="优先级"
            allowClear
            value={priority}
            onChange={(value) => setPriority(value)}
            options={priorityOptions}
            style={{ width: 120 }}
          />
          <Select
            placeholder="分类"
            allowClear
            value={category || undefined}
            onChange={(value) => setCategory(value ?? "")}
            options={categories.map((item) => ({ label: item, value: item }))}
            style={{ width: 140 }}
          />
          <Button type="primary" onClick={() => fetchData()}>
            筛选
          </Button>
          <Button onClick={handleReset}>重置</Button>
        </Space>
      </Card>

      <Card>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={tasks}
          columns={columns}
          scroll={{ x: 1180 }}
          pagination={{ pageSize: 10, showSizeChanger: false }}
        />
      </Card>
    </div>
  );
}
