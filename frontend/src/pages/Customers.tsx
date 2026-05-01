import { useEffect, useState } from "react";
import { Button, Card, Form, Input, message, Table } from "antd";
import { ArrowLeftOutlined, DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

import PageToolbar from "../components/PageToolbar";
import { createActionColumn } from "../components/TableActions";
import { customersApi, type Customer, type CustomerForm } from "../api/customers";

type View = "list" | "form";

export default function Customers() {
  const [view, setView] = useState<View>("list");
  const [data, setData] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
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
    setView("form");
  };

  const openEdit = (record: Customer) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setView("form");
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
    setView("list");
    fetchData();
  };

  const handleDelete = async (id: number) => {
    await customersApi.delete(id);
    message.success("客户已删除");
    fetchData();
  };

  const columns: ColumnsType<Customer> = [
    {
      title: "客户名称",
      dataIndex: "name",
      width: 180,
      ellipsis: true,
    },
    {
      title: "电话",
      dataIndex: "phone",
      width: 150,
      ellipsis: true,
      render: (value: string) => value || "-",
    },
    {
      title: "地址",
      dataIndex: "address",
      width: 260,
      ellipsis: true,
      render: (value: string) => value || "-",
    },
    { title: "备注", dataIndex: "notes", ellipsis: true },
    createActionColumn<Customer>(
      [
        { key: "edit", label: "编辑", icon: <EditOutlined />, onClick: openEdit },
        {
          key: "delete",
          label: "删除",
          icon: <DeleteOutlined />,
          danger: true,
          confirmTitle: "确认删除该客户？",
          onClick: (record) => handleDelete(record.id),
        },
      ],
      // 180,
    ),
  ];

  if (view === "form") {
    return (
      <div>
        <PageToolbar
          title={editingId ? "编辑客户" : "新建客户"}
          leading={<Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>}
        />
        <Card>
          <Form form={form} layout="vertical" style={{ maxWidth: 720 }}>
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
        title="客户"
        searchValue={query}
        searchPlaceholder="模糊搜索"
        onSearchChange={setQuery}
        onSearch={fetchData}
        primaryText="新建客户"
        primaryIcon={<PlusOutlined />}
        onPrimaryClick={openCreate}
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        scroll={{ x: 900 }}
      />
    </div>
  );
}
