import client from "./client";

export interface MonthTrendPoint {
  period: string;
  label: string;
  sales: number;
  cost: number;
  profit: number;
  profit_margin: number;
  purchase_amount: number;
  sales_count: number;
  purchase_count: number;
}

export interface TopProduct {
  name: string;
  sales_count: number;
  sales: number;
  profit: number;
  profit_margin: number;
}

export interface TopCustomer {
  name: string;
  sales_count: number;
  sales: number;
  profit: number;
  last_sale_time: string;
}

export interface TopSupplier {
  name: string;
  purchase_count: number;
  amount: number;
  unpaid_amount: number;
}

export interface TaskSummary {
  open_count: number;
  overdue_count: number;
  due_soon_count: number;
  recent_open_tasks: {
    id: number;
    title: string;
    priority: string;
    status: string;
    due_date: string | null;
  }[];
}

export interface ActionItem {
  type: "collection" | "task";
  title: string;
  amount: number | null;
  date: string | null;
  target: string;
}

export interface DashboardData {
  last_updated_at: string;
  month_sales: number;
  month_cost: number;
  month_profit: number;
  month_profit_margin: number;
  year_sales: number;
  year_cost: number;
  year_profit: number;
  year_profit_margin: number;
  unsettled_count: number;
  unsettled_amount: number;
  due_collection_count: number;
  due_collection_amount: number;
  due_collection_records: {
    id: number;
    customer_name: string;
    product: string;
    amount: number;
    collection_time: string | null;
  }[];
  month_trend: MonthTrendPoint[];
  top_products: TopProduct[];
  top_customers: TopCustomer[];
  top_suppliers: TopSupplier[];
  task_summary: TaskSummary;
  action_items: ActionItem[];
  recent_sales: {
    id: number;
    sale_time: string;
    customer_name: string;
    product: string;
    amount: number;
    gross_profit: number;
    is_settled: boolean;
  }[];
  recent_purchases: {
    id: number;
    purchase_time: string;
    supplier_name: string;
    product_name: string;
    total_amount: number;
    unpaid_amount: number;
  }[];
}

export const dashboardApi = {
  get: () => client.get<DashboardData>("/dashboard"),
};
