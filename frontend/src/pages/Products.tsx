import { useCallback, useEffect, useState } from "react";
import { Button, Card, Form, Image, Input, InputNumber, message, Space, Table, Upload } from "antd";
import { ArrowLeftOutlined, DeleteOutlined, EditOutlined, PlusOutlined, UploadOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

import PageToolbar from "../components/PageToolbar";
import { createActionColumn } from "../components/TableActions";
import { productsApi, type Product, type ProductForm } from "../api/products";

type View = "list" | "form";

function resolveImageSrc(image?: string): string {
  if (!image) return "";
  if (image.startsWith("data:") || image.startsWith("http")) return image;
  return image.startsWith("/") ? image : `/${image}`;
}

function fileToJpegDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = document.createElement("img");
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const context = canvas.getContext("2d");
      if (!context) {
        URL.revokeObjectURL(url);
        reject(new Error("canvas unavailable"));
        return;
      }
      context.fillStyle = "#fff";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/jpeg", 0.92));
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("image load failed"));
    };
    image.src = url;
  });
}

export default function Products() {
  const [view, setView] = useState<View>("list");
  const [data, setData] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm<ProductForm>();
  const image = Form.useWatch("image", form);

  const fetchData = useCallback(async (q: string) => {
    setLoading(true);
    try {
      const res = await productsApi.list(q ? { q } : undefined);
      setData(res.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData("");
  }, [fetchData]);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      per_box_qty: 0,
      volume: 0,
      purchase_price: 0,
      stock_qty: 0,
    });
    setView("form");
  };

  const openEdit = (record: Product) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setView("form");
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
    setView("list");
    void fetchData(query);
  };

  const handleDelete = async (id: number) => {
    await productsApi.delete(id);
    message.success("产品已删除");
    void fetchData(query);
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
    {
      title: "产品名称",
      dataIndex: "name",
      width: 180,
      ellipsis: true,
    },
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
    createActionColumn<Product>(
      [
        { key: "edit", label: "编辑", icon: <EditOutlined />, onClick: openEdit },
        {
          key: "delete",
          label: "删除",
          icon: <DeleteOutlined />,
          danger: true,
          confirmTitle: "确认删除该产品？",
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
          title={editingId ? "编辑产品" : "新建产品"}
          leading={<Button icon={<ArrowLeftOutlined />} onClick={() => setView("list")}>返回</Button>}
        />
        <Card>
          <Form form={form} layout="vertical" style={{ maxWidth: 920 }}>
            <Form.Item name="name" label="产品名称" rules={[{ required: true, message: "请输入产品名称" }]}>
              <Input />
            </Form.Item>
            <Form.Item label="图片">
              <Space direction="vertical" size={12}>
                <Upload
                  accept="image/*"
                  showUploadList={false}
                  beforeUpload={(file) => {
                    fileToJpegDataUrl(file)
                      .then((dataUrl) => form.setFieldValue("image", dataUrl))
                      .catch(() => message.error("图片读取失败"));
                    return false;
                  }}
                >
                  <Button type="primary" icon={<UploadOutlined />}>上传图片</Button>
                </Upload>
                <Form.Item name="image" noStyle>
                  <Input placeholder="可选：粘贴图片地址、/img 路径或 data URL" style={{ width: 420, maxWidth: "100%" }} />
                </Form.Item>
              </Space>
            </Form.Item>
            {image ? (
              <Space align="start" style={{ marginBottom: 16 }}>
                <Image
                  src={resolveImageSrc(image)}
                  alt="产品预览"
                  width={96}
                  height={96}
                  style={{ objectFit: "contain" }}
                />
                <Button danger onClick={() => form.setFieldValue("image", "")}>
                  移除图片
                </Button>
              </Space>
            ) : null}
            <Space style={{ display: "flex", gap: 12 }} wrap>
              <Form.Item name="per_box_qty" label="装箱数">
                <InputNumber min={0} style={{ width: 180 }} />
              </Form.Item>
              <Form.Item name="box_spec" label="箱规">
                <Input style={{ width: 180 }} />
              </Form.Item>
              <Form.Item name="volume" label="体积">
                <InputNumber min={0} step={0.001} precision={3} style={{ width: 180 }} />
              </Form.Item>
              <Form.Item name="purchase_price" label="进货价格">
                <InputNumber min={0} step={0.01} precision={2} prefix="¥" style={{ width: 180 }} />
              </Form.Item>
              <Form.Item name="stock_qty" label="库存数量">
                <InputNumber style={{ width: 180 }} />
              </Form.Item>
            </Space>
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
        title="产品"
        searchValue={query}
        searchPlaceholder="模糊搜索"
        onSearchChange={setQuery}
        onSearch={fetchData}
        primaryText="新建产品"
        primaryIcon={<PlusOutlined />}
        onPrimaryClick={openCreate}
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 20, showTotal: (total) => `共 ${total} 条` }}
        scroll={{ x: 1180 }}
      />
    </div>
  );
}
