import { useEffect, useMemo, useState } from "react";
import { Card, Col, Row, Spin, Typography } from "antd";
import dayjs from "dayjs";

import { purchasesApi, type PurchaseOrder } from "../api/purchases";
import { salesApi, type SalesRecord } from "../api/sales";

interface ChartPoint {
  label: string;
  value: number;
}

function formatCurrency(value: number): string {
  if (value >= 10000) return `${(value / 10000).toFixed(1)}万`;
  return `¥${value.toFixed(0)}`;
}

function getLastMonths(count: number) {
  const now = dayjs();
  return Array.from({ length: count }, (_, index) => now.subtract(count - index - 1, "month"));
}

function LineChart({
  title,
  data,
  color = "#1677ff",
}: {
  title: string;
  data: ChartPoint[];
  color?: string;
}) {
  const width = 760;
  const height = 280;
  const padding = { top: 26, right: 28, bottom: 46, left: 58 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...data.map((item) => item.value), 1);
  const points = data.map((item, index) => {
    const x = padding.left + (data.length === 1 ? 0 : (index / (data.length - 1)) * innerWidth);
    const y = padding.top + innerHeight - (item.value / maxValue) * innerHeight;
    return { ...item, x, y };
  });
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");

  return (
    <Card title={title}>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} role="img">
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + innerHeight - ratio * innerHeight;
          return (
            <g key={ratio}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#f0f0f0" />
              <text x={padding.left - 10} y={y + 4} textAnchor="end" fontSize={11} fill="#8c8c8c">
                {formatCurrency(maxValue * ratio)}
              </text>
            </g>
          );
        })}
        <path d={path} fill="none" stroke={color} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
        {points.map((point) => (
          <g key={point.label}>
            <circle cx={point.x} cy={point.y} r={4} fill="#fff" stroke={color} strokeWidth={2} />
            <text x={point.x} y={height - 20} textAnchor="middle" fontSize={11} fill="#595959">
              {point.label}
            </text>
          </g>
        ))}
      </svg>
    </Card>
  );
}

function BarChart({
  title,
  data,
  color = "#13c2c2",
  formatValue = formatCurrency,
}: {
  title: string;
  data: ChartPoint[];
  color?: string;
  formatValue?: (value: number) => string;
}) {
  const width = 760;
  const height = 280;
  const padding = { top: 26, right: 24, bottom: 54, left: 58 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const maxValue = Math.max(...data.map((item) => item.value), 1);
  const band = innerWidth / Math.max(data.length, 1);
  const barWidth = Math.max(18, band * 0.56);

  return (
    <Card title={title}>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} role="img">
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + innerHeight - ratio * innerHeight;
          return (
            <g key={ratio}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#f0f0f0" />
              <text x={padding.left - 10} y={y + 4} textAnchor="end" fontSize={11} fill="#8c8c8c">
                {formatValue(maxValue * ratio)}
              </text>
            </g>
          );
        })}
        {data.map((item, index) => {
          const valueHeight = (item.value / maxValue) * innerHeight;
          const x = padding.left + index * band + (band - barWidth) / 2;
          const y = padding.top + innerHeight - valueHeight;
          return (
            <g key={item.label}>
              <rect x={x} y={y} width={barWidth} height={Math.max(2, valueHeight)} rx={4} fill={color} />
              <text x={x + barWidth / 2} y={height - 30} textAnchor="middle" fontSize={11} fill="#595959">
                {item.label.length > 6 ? `${item.label.slice(0, 6)}...` : item.label}
              </text>
            </g>
          );
        })}
      </svg>
    </Card>
  );
}

export default function DataOverview() {
  const [loading, setLoading] = useState(true);
  const [salesRecords, setSalesRecords] = useState<SalesRecord[]>([]);
  const [purchases, setPurchases] = useState<PurchaseOrder[]>([]);

  useEffect(() => {
    Promise.all([salesApi.list(), purchasesApi.list()])
      .then(([salesRes, purchaseRes]) => {
        setSalesRecords(salesRes.data);
        setPurchases(purchaseRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const months = useMemo(() => getLastMonths(12), []);

  const monthlySales = useMemo(
    () =>
      months.map((month) => ({
        label: month.format("MM月"),
        value: salesRecords
          .filter((record) => dayjs(record.sale_time).format("YYYY-MM") === month.format("YYYY-MM"))
          .reduce((sum, record) => sum + Number(record.amount), 0),
      })),
    [months, salesRecords],
  );

  const monthlyProfit = useMemo(
    () =>
      months.map((month) => ({
        label: month.format("MM月"),
        value: salesRecords
          .filter((record) => dayjs(record.sale_time).format("YYYY-MM") === month.format("YYYY-MM"))
          .reduce((sum, record) => sum + Number(record.gross_profit), 0),
      })),
    [months, salesRecords],
  );

  const monthlyPurchases = useMemo(
    () =>
      months.map((month) => ({
        label: month.format("MM月"),
        value: purchases
          .filter((record) => dayjs(record.purchase_time).format("YYYY-MM") === month.format("YYYY-MM"))
          .reduce((sum, record) => sum + Number(record.total_amount), 0),
      })),
    [months, purchases],
  );

  const productDistribution = useMemo(() => {
    const grouped = salesRecords.reduce<Record<string, number>>((acc, record) => {
      acc[record.product] = (acc[record.product] ?? 0) + Number(record.amount);
      return acc;
    }, {});
    return Object.entries(grouped)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [salesRecords]);

  const settlementDistribution = useMemo(() => {
    const due = salesRecords.filter(
      (record) =>
        !record.is_settled &&
        record.collection_time &&
        dayjs(record.collection_time).isBefore(dayjs().add(1, "day"), "day"),
    ).length;
    const settled = salesRecords.filter((record) => record.is_settled).length;
    const unsettled = salesRecords.length - settled - due;
    return [
      { label: "到期/超时", value: due },
      { label: "未结清", value: Math.max(0, unsettled) },
      { label: "已结清", value: settled },
    ];
  }, [salesRecords]);

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
        <Col xs={24}>
          <LineChart title="销售额趋势" data={monthlySales} color="#1677ff" />
        </Col>
        <Col xs={24}>
          <LineChart title="毛利润趋势" data={monthlyProfit} color="#52c41a" />
        </Col>
        <Col xs={24}>
          <BarChart title="采购金额分布" data={monthlyPurchases} color="#fa8c16" />
        </Col>
        <Col xs={24} xl={12}>
          <BarChart title="产品销售分布" data={productDistribution} color="#722ed1" />
        </Col>
        <Col xs={24} xl={12}>
          <BarChart
            title="收款状态分布"
            data={settlementDistribution}
            color="#13c2c2"
            formatValue={(value) => `${Math.round(value)}`}
          />
        </Col>
      </Row>
    </div>
  );
}
