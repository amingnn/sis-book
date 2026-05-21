import client from "./client";

export interface ExcelPreviewSheet {
  name: string;
  matched_table: string;
  matched_label: string;
  total_rows: number;
  columns: string[];
  mappings: Array<{
    column: string;
    field: string;
    label: string;
    required: boolean;
  }>;
  rows: Record<string, string>[];
  warnings: string[];
}

export interface ExcelImportSummary {
  sheet: string;
  table: string;
  created: number;
  updated: number;
}

export const importExportApi = {
  exportExcel: (targetDir: string) =>
    client.post<{ cancelled: boolean; path: string }>("/import-export/export/excel", { target_dir: targetDir }),
  exportOrderExcel: (orderId: number, targetDir: string) =>
    client.post<{ cancelled: boolean; path: string }>(`/import-export/export/orders/${orderId}/excel`, { target_dir: targetDir }),
  previewExcel: (file: File) =>
    client.post<{ sheets: ExcelPreviewSheet[] }>("/import-export/import/excel/preview", file, {
      headers: { "Content-Type": file.type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
      timeout: 30000,
    }),
  importExcel: (file: File) =>
    client.post<{ summary: ExcelImportSummary[] }>("/import-export/import/excel", file, {
      headers: { "Content-Type": file.type || "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
      timeout: 30000,
    }),
};
