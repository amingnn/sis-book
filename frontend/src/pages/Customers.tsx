import { useEffect, useState } from "react";
import {
  Button,
  Form,
  Input,
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
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

import { customersApi, type Customer, type CustomerForm } from "../api/customers";

export default function Customers() {
  const [data, setData] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm<CustomerForm>();

  const fetchData = async (q = query) => {
    setLoading(true);
    try {
      const res = await customersApi.list(q ? { q } : undefined);
      setData(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData("");
  }, []);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (record: Customer) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingId) {
      await customersApi.update(editingId, values);
      message.success("客户已更新");
    } else {
      await customersApi.create(values);
      message.success("客户已新增");
    }
    setModalOpen(false);
    fetchData();
  };

  const handleDelete = async (id: number) => {
    await customersApi.delete(id);
    message.success("客户已删除");
    fetchData();
  };

  const columns: ColumnsType<Customer> = [
    { title: "客户名称", dataIndex: "name", width: 180, ellipsis: true },
    { title: "电话", dataIndex: "phone", width: 150, ellipsis: true },
    { title: "地址", dataIndex: "address", width: 260, ellipsis: true },
    { title: "备注", dataIndex: "notes", ellipsis: true },
    {
      title: "操作",
      key: "actions",
      width: 150,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确认删除该客户？" onConfirm={() => handleDelete(record.id)}>
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
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, gap: 16 }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          客户
        </Typography.Title>
        <Space wrap>
          <Input.Search
            placeholder="可模糊搜索"
            allowClear
            prefix={<SearchOutlined />}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={(value) => fetchData(value)}
            style={{ width: 260 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建客户
          </Button>
        </Space>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        scroll={{ x: 900 }}
      />

      <CustomerModal
        open={modalOpen}
        editingId={editingId}
        form={form}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      />
    </div>
  );
}

function CustomerModal({
  open,
  editingId,
  form,
  onOk,
  onCancel,
}: {
  open: boolean;
  editingId: number | null;
  form: ReturnType<typeof Form.useForm<CustomerForm>>[0];
  onOk: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      title={editingId ? "编辑客户" : "新建客户"}
      open={open}
      onOk={onOk}
      onCancel={onCancel}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="name" label="客户名称" rules={[{ required: true, message: "请输入客户名称" }]}>
          <Input />
        </Form.Item>
        <Form.Item name="phone" label="电话">
          <Input />
        </Form.Item>
        <Form.Item name="address" label="地址">
          <Input />
        </Form.Item>
        <Form.Item name="notes" label="备注">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
