import { useEffect, useState } from "react";
import {
  Button,
  Form,
  Image,
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
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

import { productsApi, type Product, type ProductForm } from "../api/products";

function resolveImageSrc(image?: string): string {
  if (!image) return "";
  if (image.startsWith("data:") || image.startsWith("http")) return image;
  return image.startsWith("/") ? image : `/${image}`;
}

export default function Products() {
  const [data, setData] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm<ProductForm>();

  const fetchData = async (q = query) => {
    setLoading(true);
    try {
      const res = await productsApi.list(q ? { q } : undefined);
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
    form.setFieldsValue({
      per_box_qty: 0,
      volume: 0,
      purchase_price: 0,
      stock_qty: 0,
    });
    setModalOpen(true);
  };

  const openEdit = (record: Product) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingId) {
      await productsApi.update(editingId, values);
      message.success("产品已更新");
    } else {
      await productsApi.create(values);
      message.success("产品已新增");
    }
    setModalOpen(false);
    fetchData();
  };

  const handleDelete = async (id: number) => {
    await productsApi.delete(id);
    message.success("产品已删除");
    fetchData();
  };

  const columns: ColumnsType<Product> = [
    {
      title: "图片",
      dataIndex: "image",
      width: 88,
      render: (value: string, record) =>
        value ? (
          <Image
            src={resolveImageSrc(value)}
            alt={record.name}
            width={48}
            height={48}
            style={{ objectFit: "contain" }}
          />
        ) : "-",
    },
    { title: "产品名称", dataIndex: "name", width: 180, ellipsis: true },
    { title: "厂家", dataIndex: "supplier_name", width: 160, ellipsis: true },
    { title: "装箱数", dataIndex: "per_box_qty", width: 90, align: "right" },
    { title: "箱规", dataIndex: "box_spec", width: 120, ellipsis: true },
    {
      title: "体积",
      dataIndex: "volume",
      width: 90,
      align: "right",
      render: (value: number | string) => Number(value).toFixed(3),
    },
    {
      title: "进货价",
      dataIndex: "purchase_price",
      width: 110,
      align: "right",
      render: (value: number | string) => `¥${Number(value).toFixed(2)}`,
    },
    { title: "库存", dataIndex: "stock_qty", width: 90, align: "right" },
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
          <Popconfirm title="确认删除该产品？" onConfirm={() => handleDelete(record.id)}>
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
          产品
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
            新建产品
          </Button>
        </Space>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        scroll={{ x: 1180 }}
      />

      <ProductModal
        open={modalOpen}
        editingId={editingId}
        form={form}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      />
    </div>
  );
}

function ProductModal({
  open,
  editingId,
  form,
  onOk,
  onCancel,
}: {
  open: boolean;
  editingId: number | null;
  form: ReturnType<typeof Form.useForm<ProductForm>>[0];
  onOk: () => void;
  onCancel: () => void;
}) {
  const image = Form.useWatch("image", form);

  return (
    <Modal
      title={editingId ? "编辑产品" : "新建产品"}
      open={open}
      onOk={onOk}
      onCancel={onCancel}
      width={720}
      destroyOnHidden
    >
      <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
        <Form.Item name="name" label="产品名称" rules={[{ required: true, message: "请输入产品名称" }]}>
          <Input />
        </Form.Item>
        <Form.Item name="image" label="图片">
          <Input placeholder="图片地址、/img 路径或 data URL" />
        </Form.Item>
        {image ? (
          <Image
            src={resolveImageSrc(image)}
            alt="产品预览"
            width={80}
            height={80}
            style={{ objectFit: "contain", marginBottom: 16 }}
          />
        ) : null}
        <Form.Item name="supplier_name" label="厂家">
          <Input />
        </Form.Item>
        <Space style={{ display: "flex", gap: 12 }}>
          <Form.Item name="per_box_qty" label="装箱数">
            <InputNumber min={0} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="box_spec" label="箱规">
            <Input />
          </Form.Item>
          <Form.Item name="volume" label="体积">
            <InputNumber min={0} step={0.001} precision={3} style={{ width: "100%" }} />
          </Form.Item>
        </Space>
        <Space style={{ display: "flex", gap: 12 }}>
          <Form.Item name="purchase_price" label="进货价格">
            <InputNumber min={0} step={0.01} precision={2} prefix="¥" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="stock_qty" label="库存数量">
            <InputNumber style={{ width: "100%" }} />
          </Form.Item>
        </Space>
        <Form.Item name="notes" label="备注">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
