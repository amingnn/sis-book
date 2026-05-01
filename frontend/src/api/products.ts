import client from "./client";

export interface Product {
  id: number;
  name: string;
  image: string;
  per_box_qty: number;
  box_spec: string;
  volume: number;
  purchase_price: number;
  stock_qty: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface ProductForm {
  name: string;
  image?: string;
  per_box_qty?: number;
  box_spec?: string;
  volume?: number;
  purchase_price?: number;
  stock_qty?: number;
  notes?: string;
}

export const productsApi = {
  list: (params?: { q?: string }) => client.get<Product[]>("/products", { params }),
  get: (id: number) => client.get<Product>(`/products/${id}`),
  create: (data: ProductForm) => client.post<Product>("/products", data),
  update: (id: number, data: Partial<ProductForm>) =>
    client.put<Product>(`/products/${id}`, data),
  delete: (id: number) => client.delete(`/products/${id}`),
};
