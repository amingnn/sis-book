import client from "./client";

export interface SalesRecord {
  id: number;
  sale_time: string;
  customer_name: string;
  product: string;
  amount: number;
  delivery_time: string | null;
  collection_time: string | null;
  is_settled: boolean;
  payment_method: string;
  cost: number;
  notes: string;
  created_at: string;
  gross_profit: number;
  profit_margin: number;
}

export interface SalesRecordForm {
  sale_time: string;
  customer_name: string;
  product: string;
  amount: number;
  delivery_time?: string | null;
  collection_time?: string | null;
  is_settled?: boolean;
  payment_method?: string;
  cost: number;
  notes?: string;
}

export interface SalesSummary {
  total_amount: number;
  total_cost: number;
  total_profit: number;
  avg_margin: number;
  unsettled_count: number;
}

export const salesApi = {
  list: (params?: Record<string, unknown>) =>
    client.get<SalesRecord[]>("/sales", { params }),
  get: (id: number) => client.get<SalesRecord>(`/sales/${id}`),
  create: (data: SalesRecordForm) => client.post<SalesRecord>("/sales", data),
  update: (id: number, data: Partial<SalesRecordForm>) =>
    client.put<SalesRecord>(`/sales/${id}`, data),
  delete: (id: number) => client.delete(`/sales/${id}`),
  summary: (params?: Record<string, unknown>) =>
    client.get<SalesSummary>("/sales/summary", { params }),
};
