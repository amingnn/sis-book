import { Button, Card, Col, Row, Space, Typography, Upload, message } from "antd";
import {
  DownloadOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  ImportOutlined,
} from "@ant-design/icons";

import { importExportApi } from "../api/importExport";

export default function ImportExport() {
  const runPlaceholder = async (
    action: () => Promise<unknown>,
    successText: string,
  ) => {
    await action();
    message.info(successText);
  };

  return (
    <div>
      <Typography.Title level={4}>导入导出</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="导出">
            <Space wrap>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() =>
                  runPlaceholder(importExportApi.exportCsv, "CSV 导出接口已预留")
                }
              >
                导出 CSV
              </Button>
              <Button
                icon={<FilePdfOutlined />}
                onClick={() =>
                  runPlaceholder(importExportApi.exportPdf, "PDF 导出接口已预留")
                }
              >
                导出 PDF
              </Button>
            </Space>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="导入">
            <Space wrap>
              <Upload
                accept=".csv"
                showUploadList={false}
                beforeUpload={() => {
                  void runPlaceholder(importExportApi.importCsv, "CSV 导入接口已预留");
                  return false;
                }}
              >
                <Button icon={<ImportOutlined />}>导入 CSV</Button>
              </Upload>
              <Upload
                accept=".xlsx,.xls"
                showUploadList={false}
                beforeUpload={() => {
                  void runPlaceholder(importExportApi.importExcel, "Excel 导入接口已预留");
                  return false;
                }}
              >
                <Button icon={<FileExcelOutlined />}>导入 Excel</Button>
              </Upload>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
