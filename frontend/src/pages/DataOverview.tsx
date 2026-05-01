import { useEffect, useMemo, useState } from "react";
import { Card, Col, Row, Spin, Statistic, Table, Tag, Typography } from "antd";
import {
  AppstoreOutlined,
  DollarOutlined,
  ShopOutlined,
  UserOutlined,
} from "@ant-design/icons";

import client from "../api/client";
import { customersApi, type Customer } from "../api/customers";
import { productsApi, type Product } from "../api/products";
import { suppliersApi, type Supplier } from "../api/suppliers";
import { purchasesApi, type PurchaseOrder } from "../api/purchases";
import { salesApi, type SalesRecord, type SalesSummary } from "../api/sales";

interface DashboardData {
  month_sales: number;
  month_profit: number;
  year_sales: number;
  year_profit: number;
  unsettled_count: number;
  unsettled_amount: number;
  due_collection_count: number;
  due_collection_amount: number;
}

export default function DataOverview() {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [salesSummary, setSalesSummary] = useState<SalesSummary | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [purchases, setPurchases] = useState<PurchaseOrder[]>([]);
  const [salesRecords, setSalesRecords] = useState<SalesRecord[]>([]);

  useEffect(() => {
    Promise.all([
      client.get<DashboardData>("/dashboard"),
      salesApi.summary(),
      customersApi.list(),
      suppliersApi.list(),
      productsApi.list(),
      purchasesApi.list(),
      salesApi.list(),
    ])
      .then(([dashboardRes, summaryRes, customerRes, supplierRes, productRes, purchaseRes, salesRes]) => {
        setDashboard(dashboardRes.data);
        setSalesSummary(summaryRes.data);
        setCustomers(customerRes.data);
        setSuppliers(supplierRes.data);
        setProducts(productRes.data);
        setPurchases(purchaseRes.data);
        setSalesRecords(salesRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const inventoryValue = useMemo(
    () =>
      products.reduce(
        (sum, product) => sum + Number(product.purchase_price) * Number(product.stock_qty),
        0,
      ),
    [products],
  );

  const unpaidPurchaseAmount = useMemo(
    () => purchases.reduce((sum, item) => sum + Number(item.unpaid_amount), 0),
    [purchases],
  );

  const salesChartData = useMemo(() => {
    const today = new Date();
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - 6);
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    const yearStart = new Date(today.getFullYear(), 0, 1);

    const sumFrom = (start: Date) =>
      salesRecords.reduce((sum, record) => {
        const saleDate = new Date(record.sale_time);
        return saleDate >= start ? sum + Number(record.amount) : sum;
      }, 0);

    return [
      { label: "本周", value: sumFrom(weekStart) },
      { label: "本月", value: dashboard?.month_sales ?? sumFrom(monthStart) },
      { label: "本年", value: dashboard?.year_sales ?? sumFrom(yearStart) },
    ];
  }, [dashboard, salesRecords]);

  const maxChartValue = Math.max(...salesChartData.map((item) => item.value), 1);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Typography.Title level={4}>数据总览</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="客户数" value={customers.length} prefix={<UserOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="厂家数" value={suppliers.length} prefix={<ShopOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="产品数" value={products.length} prefix={<AppstoreOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="库存参考金额"
              value={inventoryValue}
              precision={2}
              prefix={<><DollarOutlined /> ¥</>}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月销售"
              value={dashboard?.month_sales ?? 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="本月毛利"
              value={dashboard?.month_profit ?? 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="未结清销售"
              value={dashboard?.unsettled_amount ?? 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="未付款采购" value={unpaidPurchaseAmount} precision={2} prefix="¥" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="销售趋势">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
              {salesChartData.map((item) => (
                <div key={item.label}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <Typography.Text>{item.label}</Typography.Text>
                    <Typography.Text strong>¥{item.value.toFixed(2)}</Typography.Text>
                  </div>
                  <div style={{ height: 160, display: "flex", alignItems: "end", background: "#fafafa", borderRadius: 6, padding: 12 }}>
                    <div
                      style={{
                        width: "100%",
                        height: `${Math.max(8, (item.value / maxChartValue) * 100)}%`,
                        background: "#1677ff",
                        borderRadius: 4,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="库存关注">
            <Table
              rowKey="id"
              size="small"
              pagination={false}
              dataSource={[...products].sort((a, b) => a.stock_qty - b.stock_qty).slice(0, 8)}
              columns={[
                { title: "产品", dataIndex: "name" },
                {
                  title: "库存",
                  dataIndex: "stock_qty",
                  align: "right",
                  render: (value: number) =>
                    value <= 0 ? <Tag color="red">{value}</Tag> : value,
                },
              ]}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="销售概况">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic title="销售额" value={salesSummary?.total_amount ?? 0} precision={2} prefix="¥" />
              </Col>
              <Col span={12}>
                <Statistic title="销售成本" value={salesSummary?.total_cost ?? 0} precision={2} prefix="¥" />
              </Col>
              <Col span={12}>
                <Statistic title="毛利润" value={salesSummary?.total_profit ?? 0} precision={2} prefix="¥" />
              </Col>
              <Col span={12}>
                <Statistic title="利润率" value={salesSummary?.avg_margin ?? 0} precision={2} suffix="%" />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
