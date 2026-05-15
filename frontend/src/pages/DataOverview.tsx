import { useEffect, useMemo, useState } from "react";
import { Card, Col, Row, Segmented, Space, Spin, Typography } from "antd";
import dayjs, { type Dayjs } from "dayjs";

import { purchasesApi, type PurchaseOrder } from "../api/purchases";
import { salesApi, type SalesRecord } from "../api/sales";

type RangeMode = "day" | "week" | "year";

interface ChartPoint {
  label: string;
  value: number;
}

interface TimeBucket {
  label: string;
  start: Dayjs;
  end: Dayjs;
}

function formatCurrency(value: number): string {
  if (value >= 10000) return `${(value / 10000).toFixed(1)}万`;
  return `¥${value.toFixed(0)}`;
}

function buildBuckets(mode: RangeMode): TimeBucket[] {
  const now = dayjs();
  if (mode === "day") {
    return Array.from({ length: 14 }, (_, index) => {
      const day = now.subtract(13 - index, "day");
      return {
        label: day.format("MM/DD"),
        start: day.startOf("day"),
        end: day.endOf("day"),
      };
    });
  }

  if (mode === "week") {
    return Array.from({ length: 12 }, (_, index) => {
      const end = now.subtract((11 - index) * 7, "day").endOf("day");
      const start = end.subtract(6, "day").startOf("day");
      return {
        label: start.format("MM/DD"),
        start,
        end,
      };
    });
  }

  return Array.from({ length: 12 }, (_, index) => {
    const month = now.subtract(11 - index, "month");
    return {
      label: month.format("YY/MM"),
      start: month.startOf("month"),
      end: month.endOf("month"),
    };
  });
}

function inBucket(value: string | null | undefined, bucket: TimeBucket): boolean {
  if (!value) return false;
  const current = dayjs(value);
  return !current.isBefore(bucket.start) && !current.isAfter(bucket.end);
}

function inRange(value: string | null | undefined, buckets: TimeBucket[]): boolean {
  if (!value || buckets.length === 0) return false;
  const current = dayjs(value);
  return !current.isBefore(buckets[0].start) && !current.isAfter(buckets[buckets.length - 1].end);
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
  const [rangeMode, setRangeMode] = useState<RangeMode>("day");
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

  const buckets = useMemo(() => buildBuckets(rangeMode), [rangeMode]);

  const filteredSales = useMemo(
    () => salesRecords.filter((record) => inRange(record.sale_time, buckets)),
    [buckets, salesRecords],
  );

  const filteredPurchases = useMemo(
    () => purchases.filter((record) => inRange(record.purchase_time, buckets)),
    [buckets, purchases],
  );

  const salesTrend = useMemo(
    () =>
      buckets.map((bucket) => ({
        label: bucket.label,
        value: salesRecords
          .filter((record) => inBucket(record.sale_time, bucket))
          .reduce((sum, record) => sum + Number(record.amount), 0),
      })),
    [buckets, salesRecords],
  );

  const profitTrend = useMemo(
    () =>
      buckets.map((bucket) => ({
        label: bucket.label,
        value: salesRecords
          .filter((record) => inBucket(record.sale_time, bucket))
          .reduce((sum, record) => sum + Number(record.gross_profit), 0),
      })),
    [buckets, salesRecords],
  );

  const purchaseTrend = useMemo(
    () =>
      buckets.map((bucket) => ({
        label: bucket.label,
        value: purchases
          .filter((record) => inBucket(record.purchase_time, bucket))
          .reduce((sum, record) => sum + Number(record.total_amount), 0),
      })),
    [buckets, purchases],
  );

  const productDistribution = useMemo(() => {
    const grouped = filteredSales.reduce<Record<string, number>>((acc, record) => {
      acc[record.product] = (acc[record.product] ?? 0) + Number(record.amount);
      return acc;
    }, {});
    return Object.entries(grouped)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [filteredSales]);

  const customerDistribution = useMemo(() => {
    const grouped = filteredSales.reduce<Record<string, number>>((acc, record) => {
      acc[record.customer_name] = (acc[record.customer_name] ?? 0) + Number(record.amount);
      return acc;
    }, {});
    return Object.entries(grouped)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [filteredSales]);

  const purchaseProductDistribution = useMemo(() => {
    const grouped = filteredPurchases.reduce<Record<string, number>>((acc, record) => {
      acc[record.product_name] = (acc[record.product_name] ?? 0) + Number(record.total_amount);
      return acc;
    }, {});
    return Object.entries(grouped)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [filteredPurchases]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Space style={{ width: "100%", justifyContent: "space-between", marginBottom: 16 }} wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>数据总览</Typography.Title>
        <Segmented
          value={rangeMode}
          onChange={(value) => setRangeMode(value as RangeMode)}
          options={[
            { label: "日", value: "day" },
            { label: "周", value: "week" },
            { label: "年", value: "year" },
          ]}
        />
      </Space>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={12}>
          <LineChart title="销售额趋势" data={salesTrend} color="#1677ff" />
        </Col>
        <Col xs={24} xl={12}>
          <LineChart title="毛利润趋势" data={profitTrend} color="#52c41a" />
        </Col>
        <Col xs={24} xl={12}>
          <BarChart title="采购金额趋势" data={purchaseTrend} color="#fa8c16" />
        </Col>
        <Col xs={24} xl={12}>
          <BarChart title="产品销售分布" data={productDistribution} color="#722ed1" />
        </Col>
        <Col xs={24} xl={12}>
          <BarChart title="客户销售分布" data={customerDistribution} color="#13c2c2" />
        </Col>
        <Col xs={24} xl={12}>
          <BarChart title="采购产品分布" data={purchaseProductDistribution} color="#eb2f96" />
        </Col>
      </Row>
    </div>
  );
}
