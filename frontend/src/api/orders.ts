import client from "./client";

export interface SalesOrderListParams {
  q?: string;
  order_number?: string;
  customer_name?: string;
  payment_terms?: string;
  start_date?: string;
  end_date?: string;
}

export interface SalesOrderItem {
  id?: number;
  sales_order_id?: number;
  product_name: string;
  color_spec?: string;
  total_boxes: number;
  per_box_qty: number;
  unit_price: number;
  box_size?: string;
  notes?: string;
  image?: string;
}

export interface SalesOrder {
  id: number;
  order_number: string;
  customer_name: string;
  customer_phone: string;
  delivery_address: string;
  sales_date: string;
  delivery_date: string | null;
  payment_terms: string;
  notes: string;
  sales_record_id: number | null;
  created_at: string;
  items: SalesOrderItem[];
}

export interface SalesOrderForm {
  customer_name: string;
  customer_phone?: string;
  delivery_address?: string;
  sales_date: string;
  delivery_date?: string | null;
  payment_terms?: string;
  notes?: string;
  items: Omit<SalesOrderItem, "id" | "sales_order_id">[];
}

export const ordersApi = {
  list: (params?: SalesOrderListParams) =>
    client.get<SalesOrder[]>("/orders", { params }),
  get: (id: number) => client.get<SalesOrder>(`/orders/${id}`),
  create: (data: SalesOrderForm) =>
    client.post<SalesOrder>("/orders", data),
  update: (id: number, data: SalesOrderForm) =>
    client.put<SalesOrder>(`/orders/${id}`, data),
  delete: (id: number) => client.delete(`/orders/${id}`),
};
