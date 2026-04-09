import client from "./client";

export interface PurchaseOrder {
  id: number;
  purchase_time: string;
  supplier_name: string;
  product_name: string;
  box_count: number;
  per_box_qty: number;
  unit_price: number;
  notes: string;
  created_at: string;
  total_qty: number;
  total_amount: number;
}

export interface PurchaseOrderForm {
  purchase_time: string;
  supplier_name: string;
  product_name: string;
  box_count: number;
  per_box_qty: number;
  unit_price: number;
  notes?: string;
}

export const purchasesApi = {
  list: (params?: Record<string, unknown>) =>
    client.get<PurchaseOrder[]>("/purchases", { params }),
  get: (id: number) => client.get<PurchaseOrder>(`/purchases/${id}`),
  create: (data: PurchaseOrderForm) =>
    client.post<PurchaseOrder>("/purchases", data),
  update: (id: number, data: Partial<PurchaseOrderForm>) =>
    client.put<PurchaseOrder>(`/purchases/${id}`, data),
  delete: (id: number) => client.delete(`/purchases/${id}`),
};
