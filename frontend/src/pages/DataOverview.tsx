import { useEffect, useMemo, useState } from "react";
import { Alert, Card, Col, Empty, Row, Segmented, Space, Spin, Statistic, Typography } from "antd";
import dayjs, { type Dayjs } from "dayjs";

import { purchasesApi, type PurchaseOrder } from "../api/purchases";
import { salesApi, type SalesRecord } from "../api/sales";

type RangeMode = "week" | "month" | "year";

interface TimeBucket {
  label: string;
  start: Dayjs;
  end: Dayjs;
}

interface TrendPoint {
  label: string;
  sales: number;
  profit: number;
  purchase: number;
}

interface DistributionPoint {
  label: string;
  value: number;
}

interface LineSeries {
  label: string;
  color: string;
  getValue: (point: TrendPoint) => number;
}

interface ActiveTrendPoint {
  seriesLabel: string;
  label: string;
  value: number;
  x: number;
  y: number;
  color: string;
}

interface ActiveSlice {
  label: string;
  value: number;
  percent: number;
  x: number;
  y: number;
  color: string;
}

const chartColors = ["#1677ff", "#fa8c16", "#52c41a", "#eb2f96", "#13c2c2", "#722ed1"];

const currencyFormatter = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  maximumFractionDigits: 0,
});

function formatCurrency(value: number): string {
  return currencyFormatter.format(Number(value || 0));
}

function formatCompactCurrency(value: number): string {
  const current = Number(value || 0);
  const sign = current < 0 ? "-" : "";
  const absoluteValue = Math.abs(current);
  if (absoluteValue >= 10000) return `${sign}¥${(absoluteValue / 10000).toFixed(1)}万`;
  return `${sign}¥${absoluteValue.toFixed(0)}`;
}

function buildBuckets(mode: RangeMode): TimeBucket[] {
  const now = dayjs();
  if (mode === "week") {
    return Array.from({ length: 7 }, (_, index) => {
      const day = now.subtract(6 - index, "day");
      return {
        label: day.format("MM/DD"),
        start: day.startOf("day"),
        end: day.endOf("day"),
      };
    });
  }

  if (mode === "month") {
    return Array.from({ length: 30 }, (_, index) => {
      const day = now.subtract(29 - index, "day");
      return {
        label: day.format("MM/DD"),
        start: day.startOf("day"),
        end: day.endOf("day"),
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

function groupDistribution(
  records: Array<{ label: string; value: number }>,
  limit = 5,
): DistributionPoint[] {
  const grouped = records.reduce<Record<string, number>>((acc, record) => {
    if (record.value <= 0) return acc;
    acc[record.label] = (acc[record.label] ?? 0) + record.value;
    return acc;
  }, {});
  const sorted = Object.entries(grouped)
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
  const top = sorted.slice(0, limit);
  const rest = sorted.slice(limit).reduce((sum, item) => sum + item.value, 0);
  return rest > 0 ? [...top, { label: "其他", value: rest }] : top;
}

function polarToCartesian(centerX: number, centerY: number, radius: number, angleInDegrees: number) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
}

function describePieSlice(
  centerX: number,
  centerY: number,
  radius: number,
  startAngle: number,
  endAngle: number,
) {
  const start = polarToCartesian(centerX, centerY, radius, endAngle);
  const end = polarToCartesian(centerX, centerY, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return [
    `M ${centerX} ${centerY}`,
    `L ${start.x} ${start.y}`,
    `A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`,
    "Z",
  ].join(" ");
}

function TrendLineChart({ data }: { data: TrendPoint[] }) {
  const width = 960;
  const height = 320;
  const padding = { top: 32, right: 34, bottom: 52, left: 70 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const [activePoint, setActivePoint] = useState<ActiveTrendPoint | null>(null);
  const series: LineSeries[] = [
    { label: "销售额", color: "#1677ff", getValue: (point) => point.sales },
    { label: "采购额", color: "#fa8c16", getValue: (point) => point.purchase },
    { label: "毛利", color: "#52c41a", getValue: (point) => point.profit },
  ];
  const maxValue = Math.max(...data.flatMap((point) => series.map((item) => Math.max(item.getValue(point), 0))), 1);

  const buildPoints = (line: LineSeries) =>
    data.map((point, index) => {
      const x = padding.left + (data.length === 1 ? innerWidth / 2 : (index / (data.length - 1)) * innerWidth);
      const y = padding.top + innerHeight - (Math.max(line.getValue(point), 0) / maxValue) * innerHeight;
      return { label: point.label, value: line.getValue(point), x, y };
    });

  return (
    <Card
      title="经营趋势"
      extra={
        <div className="data-overview-legend">
          {series.map((line) => (
            <span key={line.label}>
              <i style={{ background: line.color }} />
              {line.label}
            </span>
          ))}
        </div>
      }
      className="data-overview-card"
    >
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        height={height}
        role="img"
        aria-label="经营趋势折线图"
        onMouseLeave={() => setActivePoint(null)}
      >
        <title>经营趋势折线图</title>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + innerHeight - ratio * innerHeight;
          return (
            <g key={ratio}>
              <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#edf2f7" />
              <text x={padding.left - 10} y={y + 4} textAnchor="end" fontSize={11} fill="#6b7280">
                {formatCompactCurrency(maxValue * ratio)}
              </text>
            </g>
          );
        })}
        {series.map((line) => {
          const points = buildPoints(line);
          const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
          return (
            <g key={line.label}>
              <path d={path} fill="none" stroke={line.color} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
              {points.map((point) => {
                const active = activePoint?.seriesLabel === line.label && activePoint.label === point.label;
                const nextPoint = {
                  seriesLabel: line.label,
                  label: point.label,
                  value: point.value,
                  x: point.x,
                  y: point.y,
                  color: line.color,
                };
                return (
                  <g
                    key={`${line.label}-${point.label}`}
                    role="button"
                    tabIndex={0}
                    aria-label={`${point.label} ${line.label} ${formatCurrency(point.value)}`}
                    style={{ cursor: "pointer" }}
                    onMouseEnter={() => setActivePoint(nextPoint)}
                    onFocus={() => setActivePoint(nextPoint)}
                    onClick={() => setActivePoint(nextPoint)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setActivePoint(nextPoint);
                      }
                    }}
                  >
                    <circle cx={point.x} cy={point.y} r={12} fill="transparent" />
                    <circle cx={point.x} cy={point.y} r={active ? 6 : 4} fill="#fff" stroke={line.color} strokeWidth={2} />
                    <title>{`${point.label} ${line.label}：${formatCurrency(point.value)}`}</title>
                  </g>
                );
              })}
            </g>
          );
        })}
        {activePoint
          ? (() => {
              const tooltipWidth = 168;
              const tooltipHeight = 52;
              const tooltipX = Math.min(Math.max(activePoint.x - tooltipWidth / 2, 8), width - tooltipWidth - 8);
              const tooltipY = activePoint.y > 96 ? activePoint.y - tooltipHeight - 14 : activePoint.y + 18;
              return (
                <g pointerEvents="none">
                  <line x1={activePoint.x} y1={padding.top} x2={activePoint.x} y2={height - padding.bottom} stroke="#d9e2ec" strokeDasharray="4 4" />
                  <rect x={tooltipX} y={tooltipY} width={tooltipWidth} height={tooltipHeight} rx={6} fill="#111827" opacity={0.92} />
                  <circle cx={tooltipX + 14} cy={tooltipY + 18} r={4} fill={activePoint.color} />
                  <text x={tooltipX + 26} y={tooltipY + 22} fontSize={12} fill="#fff">
                    {activePoint.label} · {activePoint.seriesLabel}
                  </text>
                  <text x={tooltipX + 14} y={tooltipY + 40} fontSize={14} fontWeight={700} fill="#fff">
                    {formatCurrency(activePoint.value)}
                  </text>
                </g>
              );
            })()
          : null}
        {data.map((point, index) => {
          const showLabel = data.length <= 10 || index % 2 === 0 || index === data.length - 1;
          const x = padding.left + (data.length === 1 ? innerWidth / 2 : (index / (data.length - 1)) * innerWidth);
          return showLabel ? (
            <text key={point.label} x={x} y={height - 20} textAnchor="middle" fontSize={11} fill="#595959">
              {point.label}
            </text>
          ) : null;
        })}
      </svg>
    </Card>
  );
}

function PieChart({ title, data }: { title: string; data: DistributionPoint[] }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const [activeSlice, setActiveSlice] = useState<ActiveSlice | null>(null);
  const slices = data.reduce<
    Array<{
      item: DistributionPoint;
      index: number;
      startAngle: number;
      endAngle: number;
      nextAngle: number;
    }>
  >((acc, item, index) => {
    const startAngle = acc.at(-1)?.nextAngle ?? 0;
    const angle = total > 0 ? (item.value / total) * 360 : 0;
    return [
      ...acc,
      {
        item,
        index,
        startAngle,
        endAngle: startAngle + (angle >= 360 ? 359.99 : angle),
        nextAngle: startAngle + angle,
      },
    ];
  }, []);

  return (
    <Card title={title} className="data-overview-card">
      {total <= 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <div className="data-overview-pie-content">
          <svg
            viewBox="0 0 240 220"
            width="100%"
            height={220}
            role="img"
            aria-label={`${title}饼图`}
            onMouseLeave={() => setActiveSlice(null)}
          >
            <title>{`${title}饼图`}</title>
            {slices.map(({ item, index, startAngle, endAngle }) => {
              const color = chartColors[index % chartColors.length];
              const percent = total > 0 ? (item.value / total) * 100 : 0;
              const middleAngle = (startAngle + endAngle) / 2;
              const labelPosition = polarToCartesian(120, 104, 70, middleAngle);
              const active = activeSlice?.label === item.label;
              const nextSlice = {
                label: item.label,
                value: item.value,
                percent,
                x: labelPosition.x,
                y: labelPosition.y,
                color,
              };
              return (
                <path
                  key={item.label}
                  d={describePieSlice(120, 104, 82, startAngle, endAngle)}
                  fill={color}
                  stroke="#fff"
                  strokeWidth={active ? 4 : 2}
                  role="button"
                  tabIndex={0}
                  aria-label={`${item.label} ${formatCurrency(item.value)} ${percent.toFixed(1)}%`}
                  style={{ cursor: "pointer" }}
                  transform={active ? `translate(${(labelPosition.x - 120) * 0.04} ${(labelPosition.y - 104) * 0.04})` : undefined}
                  onMouseEnter={() => setActiveSlice(nextSlice)}
                  onFocus={() => setActiveSlice(nextSlice)}
                  onClick={() => setActiveSlice(nextSlice)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setActiveSlice(nextSlice);
                    }
                  }}
                >
                  <title>{`${item.label}：${formatCurrency(item.value)}，${percent.toFixed(1)}%`}</title>
                </path>
              );
            })}
            <circle cx={120} cy={104} r={44} fill="#fff" />
            <text x={120} y={98} textAnchor="middle" fontSize={12} fill="#6b7280">
              {activeSlice ? "已选择" : "合计"}
            </text>
            <text x={120} y={120} textAnchor="middle" fontSize={15} fontWeight={700} fill="#111827">
              {formatCompactCurrency(activeSlice?.value ?? total)}
            </text>
            {activeSlice
              ? (() => {
                  const tooltipWidth = 152;
                  const tooltipHeight = 52;
                  const tooltipX = Math.min(Math.max(activeSlice.x - tooltipWidth / 2, 8), 240 - tooltipWidth - 8);
                  const tooltipY = activeSlice.y > 110 ? activeSlice.y - tooltipHeight - 12 : activeSlice.y + 12;
                  return (
                    <g pointerEvents="none">
                      <rect x={tooltipX} y={tooltipY} width={tooltipWidth} height={tooltipHeight} rx={6} fill="#111827" opacity={0.92} />
                      <circle cx={tooltipX + 14} cy={tooltipY + 18} r={4} fill={activeSlice.color} />
                      <text x={tooltipX + 26} y={tooltipY + 22} fontSize={12} fill="#fff">
                        {activeSlice.label}
                      </text>
                      <text x={tooltipX + 14} y={tooltipY + 40} fontSize={13} fontWeight={700} fill="#fff">
                        {formatCurrency(activeSlice.value)} · {activeSlice.percent.toFixed(1)}%
                      </text>
                    </g>
                  );
                })()
              : null}
          </svg>
          <div className="data-overview-pie-legend">
            {data.map((item, index) => (
              <div key={item.label} className="data-overview-pie-row">
                <span className="data-overview-pie-name">
                  <i style={{ background: chartColors[index % chartColors.length] }} />
                  {item.label}
                </span>
                <span>{((item.value / total) * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

export default function DataOverview() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [rangeMode, setRangeMode] = useState<RangeMode>("year");
  const [salesRecords, setSalesRecords] = useState<SalesRecord[]>([]);
  const [purchases, setPurchases] = useState<PurchaseOrder[]>([]);

  useEffect(() => {
    Promise.all([salesApi.list(), purchasesApi.list()])
      .then(([salesRes, purchaseRes]) => {
        setSalesRecords(salesRes.data);
        setPurchases(purchaseRes.data);
      })
      .catch(() => setLoadError("数据总览加载失败"))
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

  const trendData = useMemo(
    () =>
      buckets.map((bucket) => ({
        label: bucket.label,
        sales: salesRecords
          .filter((record) => inBucket(record.sale_time, bucket))
          .reduce((sum, record) => sum + Number(record.amount), 0),
        profit: salesRecords
          .filter((record) => inBucket(record.sale_time, bucket))
          .reduce((sum, record) => sum + Number(record.gross_profit), 0),
        purchase: purchases
          .filter((record) => inBucket(record.purchase_time, bucket))
          .reduce((sum, record) => sum + Number(record.total_amount), 0),
      })),
    [buckets, purchases, salesRecords],
  );

  const summary = useMemo(() => {
    const sales = filteredSales.reduce((sum, record) => sum + Number(record.amount), 0);
    const profit = filteredSales.reduce((sum, record) => sum + Number(record.gross_profit), 0);
    const purchase = filteredPurchases.reduce((sum, record) => sum + Number(record.total_amount), 0);
    const unsettledAmount = filteredSales
      .filter((record) => !record.is_settled)
      .reduce((sum, record) => sum + Number(record.amount), 0);
    return {
      sales,
      profit,
      purchase,
      margin: sales > 0 ? (profit / sales) * 100 : 0,
      unsettledAmount,
    };
  }, [filteredPurchases, filteredSales]);

  const productDistribution = useMemo(
    () =>
      groupDistribution(
        filteredSales.map((record) => ({ label: record.product, value: Number(record.amount) })),
      ),
    [filteredSales],
  );

  const customerDistribution = useMemo(
    () =>
      groupDistribution(
        filteredSales.map((record) => ({ label: record.customer_name, value: Number(record.amount) })),
      ),
    [filteredSales],
  );

  const purchaseProductDistribution = useMemo(
    () =>
      groupDistribution(
        filteredPurchases.map((record) => ({ label: record.product_name, value: Number(record.total_amount) })),
      ),
    [filteredPurchases],
  );

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="data-overview-page">
      <Space className="data-overview-header" align="center" wrap>
        <Typography.Title level={4} style={{ margin: 0 }}>数据总览</Typography.Title>
        <Typography.Text type="secondary">按一周、一月、一年查看经营数据</Typography.Text>
        <Segmented
          value={rangeMode}
          onChange={(value) => setRangeMode(value as RangeMode)}
          options={[
            { label: "周", value: "week" },
            { label: "月", value: "month" },
            { label: "年", value: "year" },
          ]}
        />
      </Space>

      {loadError ? <Alert type="error" showIcon message={loadError} style={{ marginBottom: 16 }} /> : null}

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}>
          <Card className="data-overview-card">
            <Statistic title="销售额" value={formatCurrency(summary.sales)} />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="data-overview-card">
            <Statistic
              title="毛利"
              value={formatCurrency(summary.profit)}
              suffix={<span className="data-overview-stat-suffix">{summary.margin.toFixed(1)}%</span>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="data-overview-card">
            <Statistic title="采购额" value={formatCurrency(summary.purchase)} />
          </Card>
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <Card className="data-overview-card">
            <Statistic title="未结清销售" value={formatCurrency(summary.unsettledAmount)} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <TrendLineChart data={trendData} />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={8}>
          <PieChart title="产品销售分布" data={productDistribution} />
        </Col>
        <Col xs={24} lg={8}>
          <PieChart title="客户销售分布" data={customerDistribution} />
        </Col>
        <Col xs={24} lg={8}>
          <PieChart title="采购产品分布" data={purchaseProductDistribution} />
        </Col>
      </Row>
    </div>
  );
}
