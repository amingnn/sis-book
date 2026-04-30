import client from "./client";

export const importExportApi = {
  exportCsv: () => client.get("/import-export/export/csv"),
  exportPdf: () => client.get("/import-export/export/pdf"),
  importCsv: () => client.post("/import-export/import/csv"),
  importExcel: () => client.post("/import-export/import/excel"),
};
