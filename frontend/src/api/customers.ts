import client from "./client";

export interface Customer {
  id: number;
  name: string;
  phone: string;
  address: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerForm {
  name: string;
  phone?: string;
  address?: string;
  notes?: string;
}

export const customersApi = {
  list: (params?: { q?: string }) => client.get<Customer[]>("/customers", { params }),
  get: (id: number) => client.get<Customer>(`/customers/${id}`),
  create: (data: CustomerForm) => client.post<Customer>("/customers", data),
  update: (id: number, data: Partial<CustomerForm>) =>
    client.put<Customer>(`/customers/${id}`, data),
  delete: (id: number) => client.delete(`/customers/${id}`),
};
