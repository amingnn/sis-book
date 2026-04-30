import client from "./client";

export interface Supplier {
  id: number;
  name: string;
  phone: string;
  address: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface SupplierForm {
  name: string;
  phone?: string;
  address?: string;
  notes?: string;
}

export const suppliersApi = {
  list: (params?: { q?: string }) => client.get<Supplier[]>("/suppliers", { params }),
  get: (id: number) => client.get<Supplier>(`/suppliers/${id}`),
  create: (data: SupplierForm) => client.post<Supplier>("/suppliers", data),
  update: (id: number, data: Partial<SupplierForm>) =>
    client.put<Supplier>(`/suppliers/${id}`, data),
  delete: (id: number) => client.delete(`/suppliers/${id}`),
};
