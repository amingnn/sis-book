import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Space,
  Spin,
  Tooltip,
  Typography,
} from "antd";
import {
  CheckSquareOutlined,
  DollarOutlined,
  ReloadOutlined,
  RiseOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";

import {
  dashboardApi,
  type ActionItem,
  type DashboardData,
} from "../api/dashboard";

const currencyFormatter = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  maximumFractionDigits: 0,
});

function formatCurrency(value: number): string {
  return currencyFormatter.format(Number(value || 0));
}

function formatCurrencyDelta(value: number): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${formatCurrency(value)}`;
}

function metricTone(value: number): string {
  if (value > 0) return "#1677ff";
  if (value < 0) return "#cf1322";
  return "#595959";
}

function MetricCard({
  title,
  value,
  suffix,
  icon,
  color,
  onClick,
}: {
  title: string;
  value: string;
  suffix?: string;
  icon: ReactNode;
  color: string;
  onClick?: () => void;
}) {
  return (
    <Card
      hoverable={Boolean(onClick)}
      onClick={onClick}
      className="dashboard-metric-card"
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(event) => {
        if (!onClick || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        onClick();
      }}
    >
      <div className="dashboard-metric-icon" style={{ color, background: `${color}14` }}>
        {icon}
      </div>
      <div className="dashboard-metric-body">
        <div className="dashboard-metric-title">{title}</div>
        <div className="dashboard-metric-value" style={{ color }}>
          {value}
        </div>
        {suffix ? <div className="dashboard-metric-suffix">{suffix}</div> : null}
      </div>
    </Card>
  );
}

function ActionList({ items }: { items: ActionItem[] }) {
  const navigate = useNavigate();
  return (
    <Card
      title="待处理事项"
      extra={<Typography.Text type="secondary">到期收款 / 截止任务</Typography.Text>}
      className="dashboard-panel"
    >
      {items.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Space orientation="vertical" size={10} style={{ width: "100%" }}>
          {items.map((item, index) => (
            <button
              key={`${item.type}-${item.title}-${index}`}
              className="dashboard-action-item"
              onClick={() => navigate(item.target)}
              type="button"
            >
              <span className={`dashboard-action-type dashboard-action-${item.type}`}>
                {item.type === "collection" ? "收款" : "任务"}
              </span>
              <span className="dashboard-action-main">
                <span className="dashboard-action-title">{item.title}</span>
                <span className="dashboard-action-date">
                  {item.date ? dayjs(item.date).format("MM/DD") : "未设日期"}
                </span>
              </span>
              {item.amount !== null ? <span className="dashboard-action-amount">{formatCurrency(item.amount)}</span> : null}
            </button>
          ))}
        </Space>
      )}
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const requestIdRef = useRef(0);
  const navigate = useNavigate();

  const loadDashboard = useCallback(async (silent = false) => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    if (silent) setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      const res = await dashboardApi.get();
      if (requestId === requestIdRef.current) {
        setData(res.data);
      }
    } catch {
      if (requestId === requestIdRef.current) {
        setError("首页数据加载失败");
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const healthScore = useMemo(() => {
    if (!data) return 0;
    const profitScore = Math.max(0, Math.min(45, data.month_profit_margin * 1.5));
    const collectionPenalty = Math.min(25, data.due_collection_count * 6);
    const taskPenalty = Math.min(20, data.task_summary.overdue_count * 5);
    const base = 55 + profitScore - collectionPenalty - taskPenalty;
    return Math.max(0, Math.min(100, Math.round(base)));
  }, [data]);

  const monthComparison = useMemo(() => {
    if (!data || data.month_trend.length < 2) {
      return { salesDelta: 0 };
    }
    const current = data.month_trend[data.month_trend.length - 1];
    const previous = data.month_trend[data.month_trend.length - 2];
    return {
      salesDelta: current.sales - previous.sales,
    };
  }, [data]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) {
    return <Alert type="error" showIcon message={error || "首页数据为空"} />;
  }

  return (
    <div className="dashboard-page">
      <Space className="dashboard-header" align="center" wrap>
        <div>
          <Typography.Title level={4} style={{ margin: 0 }}>
            首页仪表盘
          </Typography.Title>
          <Typography.Text type="secondary">
            更新于 {dayjs(data.last_updated_at).format("YYYY-MM-DD HH:mm")}
          </Typography.Text>
        </div>
        <Tooltip title="刷新">
          <Button
            shape="circle"
            icon={<ReloadOutlined />}
            loading={refreshing}
            onClick={() => loadDashboard(true)}
          />
        </Tooltip>
      </Space>

      {error ? <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} /> : null}

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} xl={6}>
          <MetricCard
            title="本月销售"
            value={formatCurrency(data.month_sales)}
            suffix={[
              `毛利 ${formatCurrency(data.month_profit)} / ${data.month_profit_margin}%`,
              `较上月 ${formatCurrencyDelta(monthComparison.salesDelta)}`,
            ].join(" · ")}
            icon={<DollarOutlined />}
            color="#1677ff"
          />
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <MetricCard
            title="年度毛利"
            value={formatCurrency(data.year_profit)}
            suffix={`销售 ${formatCurrency(data.year_sales)} / ${data.year_profit_margin}%`}
            icon={<RiseOutlined />}
            color={metricTone(data.year_profit)}
          />
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <MetricCard
            title={`未结清 ${data.unsettled_count} 笔`}
            value={formatCurrency(data.unsettled_amount)}
            suffix={`到期 ${data.due_collection_count} 笔`}
            icon={<WarningOutlined />}
            color={data.due_collection_count > 0 ? "#cf1322" : "#d48806"}
            onClick={() => navigate("/sales?settled=unsettled")}
          />
        </Col>
        <Col xs={24} sm={12} xl={6}>
          <MetricCard
            title={`待办 ${data.task_summary.open_count} 项`}
            value={`${healthScore} 分`}
            suffix={`逾期 ${data.task_summary.overdue_count} / 7日内 ${data.task_summary.due_soon_count}`}
            icon={<CheckSquareOutlined />}
            color={healthScore >= 80 ? "#389e0d" : healthScore >= 60 ? "#d48806" : "#cf1322"}
            onClick={() => navigate("/tasks")}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <ActionList items={data.action_items} />
        </Col>
      </Row>
    </div>
  );
}
