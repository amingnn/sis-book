import { useEffect, useState } from "react";
import {
  Row,
  Col,
  Card,
  Statistic,
  Alert,
  Table,
  Tag,
  Typography,
  Spin,
} from "antd";
import {
  DollarOutlined,
  RiseOutlined,
  CalendarOutlined,
  TrophyOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

interface DashboardData {
  month_sales: number;
  month_cost: number;
  month_profit: number;
  year_sales: number;
  year_cost: number;
  year_profit: number;
  unsettled_count: number;
  unsettled_amount: number;
  recent_sales: {
    id: number;
    sale_time: string;
    customer_name: string;
    product: string;
    amount: number;
    is_settled: boolean;
  }[];
  recent_purchases: {
    id: number;
    purchase_time: string;
    supplier_name: string;
    product_name: string;
    total_amount: number;
  }[];
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    client
      .get<DashboardData>("/dashboard")
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) return null;

  const salesColumns = [
    { title: "时间", dataIndex: "sale_time", key: "sale_time" },
    { title: "客户", dataIndex: "customer_name", key: "customer_name" },
    { title: "产品", dataIndex: "product", key: "product" },
    {
      title: "金额",
      dataIndex: "amount",
      key: "amount",
      render: (v: number) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: "结清",
      dataIndex: "is_settled",
      key: "is_settled",
      render: (v: boolean) =>
        v ? <Tag color="green">已结清</Tag> : <Tag color="red">未结清</Tag>,
    },
  ];

  const purchaseColumns = [
    { title: "时间", dataIndex: "purchase_time", key: "purchase_time" },
    { title: "厂家", dataIndex: "supplier_name", key: "supplier_name" },
    { title: "货物", dataIndex: "product_name", key: "product_name" },
    {
      title: "金额",
      dataIndex: "total_amount",
      key: "total_amount",
      render: (v: number) => `¥${Number(v).toFixed(2)}`,
    },
  ];

  return (
    <div>
      <Typography.Title level={4}>首页仪表盘</Typography.Title>

      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月销售额"
              value={data.month_sales}
              precision={2}
              prefix={<><DollarOutlined /> ¥</>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月毛利润"
              value={data.month_profit}
              precision={2}
              prefix={<><RiseOutlined /> ¥</>}
              styles={{ content: { color: data.month_profit >= 0 ? "#3f8600" : "#cf1322" } }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本年销售额"
              value={data.year_sales}
              precision={2}
              prefix={<><CalendarOutlined /> ¥</>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本年毛利润"
              value={data.year_profit}
              precision={2}
              prefix={<><TrophyOutlined /> ¥</>}
              styles={{ content: { color: data.year_profit >= 0 ? "#3f8600" : "#cf1322" } }}
            />
          </Card>
        </Col>
      </Row>

      {data.unsettled_count > 0 && (
        <Alert
          style={{ marginTop: 16, cursor: "pointer" }}
          type="warning"
          showIcon
          title={`有 ${data.unsettled_count} 笔未结清订单，合计 ¥${Number(data.unsettled_amount).toFixed(2)}`}
          description="点击查看未结清订单"
          onClick={() => navigate("/sales?settled=unsettled")}
        />
      )}

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="最近销售记录">
            <Table
              dataSource={data.recent_sales}
              columns={salesColumns}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="最近采购记录">
            <Table
              dataSource={data.recent_purchases}
              columns={purchaseColumns}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
