import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Divider,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import {
  CloudSyncOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";

import { syncApi, type SyncStatus } from "../api/sync";
import { importExportApi, type ExcelPreviewSheet } from "../api/importExport";

const directionLabelMap: Record<string, string> = {
  push: "已推送本机最新数据",
  pull: "已拉取同步目录最新数据",
  noop: "两边都没有变化",
};

function buildSyncRoot(path: string) {
  if (!path.trim()) return "";
  const normalized = path.replace(/[\\/]+$/, "");
  if (normalized.endsWith("/sis-book-sync") || normalized.endsWith("\\sis-book-sync")) {
    return normalized;
  }
  return `${normalized}/sis-book-sync`;
}

function previewColumns(sheet: ExcelPreviewSheet): ColumnsType<Record<string, string>> {
  return sheet.columns.map((column) => ({
    title: column,
    dataIndex: column,
    ellipsis: true,
    width: 140,
  }));
}

function getErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail || fallback;
}

export default function DataManagement() {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [browsingDir, setBrowsingDir] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewSheets, setPreviewSheets] = useState<ExcelPreviewSheet[]>([]);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [conflictData, setConflictData] = useState<{
    local_updated_at_ns: number;
    remote_updated_at_ns: number;
    local_device_name: string;
    remote_device_name: string;
  } | null>(null);
  const [form] = Form.useForm();

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await syncApi.getStatus();
      setStatus(res.data);
      form.setFieldsValue({
        sync_base_dir: res.data.sync_root || buildSyncRoot(res.data.sync_base_dir),
        enabled: res.data.enabled,
        interval_minutes: res.data.interval_minutes,
      });
    } catch {
      message.error("读取同步状态失败");
    } finally {
      setLoading(false);
    }
  }, [form]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await syncApi.saveSettings(values);
      message.success("同步设置已保存");
      setSettingsOpen(false);
      await fetchStatus();
    } catch (error) {
      if ((error as { errorFields?: unknown })?.errorFields) return;
      message.error(getErrorMessage(error, "同步设置保存失败"));
    } finally {
      setSaving(false);
    }
  };

  const runSync = async (forceDirection = "") => {
    setSyncing(true);
    try {
      const res = await syncApi.runNow(forceDirection);
      if (res.data.direction === "conflict") {
        setConflictData(res.data.conflict ?? null);
        setConflictOpen(true);
        return;
      }
      message.success(directionLabelMap[res.data.direction] ?? "同步完成");
      await fetchStatus();
    } catch (error) {
      message.error(getErrorMessage(error, "立即同步失败"));
    } finally {
      setSyncing(false);
    }
  };

  const handleBrowseDir = async () => {
    setBrowsingDir(true);
    try {
      const res = await syncApi.browseDir();
      if (!res.data.path) return;
      form.setFieldValue("sync_base_dir", buildSyncRoot(res.data.path));
    } catch (error) {
      message.error(getErrorMessage(error, "目录选择失败，请手动填写"));
    } finally {
      setBrowsingDir(false);
    }
  };

  const handleExportExcel = async () => {
    setExporting(true);
    try {
      const dirRes = await syncApi.browseDir();
      if (!dirRes.data.path) return;
      const res = await importExportApi.exportExcel(dirRes.data.path);
      message.success(`Excel 已导出：${res.data.path}`);
    } catch (error) {
      message.error(getErrorMessage(error, "Excel 导出失败"));
    } finally {
      setExporting(false);
    }
  };

  const handlePreviewExcel = async (file: File) => {
    setSelectedFile(file);
    setPreviewing(true);
    try {
      const res = await importExportApi.previewExcel(file);
      setPreviewSheets(res.data.sheets);
      setPreviewOpen(true);
    } catch (error) {
      message.error(getErrorMessage(error, "Excel 预览失败"));
    } finally {
      setPreviewing(false);
    }
  };

  const handleImportExcel = async () => {
    if (!selectedFile) return;
    setImporting(true);
    try {
      const res = await importExportApi.importExcel(selectedFile);
      const total = res.data.summary.reduce((sum, item) => sum + item.created + item.updated, 0);
      message.success(`导入完成，共处理 ${total} 条数据`);
      setPreviewOpen(false);
    } catch (error) {
      message.error(getErrorMessage(error, "Excel 导入失败"));
    } finally {
      setImporting(false);
    }
  };

  const hasImportableSheets = previewSheets.some((sheet) => sheet.matched_table && sheet.warnings.length === 0);
  const hasBlockingWarnings = previewSheets.some((sheet) => sheet.matched_table && sheet.warnings.length > 0);

  const openSyncSettings = (enabled?: boolean) => {
    if (enabled !== undefined) {
      form.setFieldValue("enabled", enabled);
    }
    setSettingsOpen(true);
  };

  return (
    <div>
      <Typography.Title level={4}>数据管理</Typography.Title>

      <Space direction="vertical" size={16} style={{ width: "100%" }}>
        <Card title="导入导出">
          <Space wrap>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={exporting}
              onClick={handleExportExcel}
            >
              导出 Excel
            </Button>
            <Upload
              accept=".xlsx"
              showUploadList={false}
              beforeUpload={(file) => {
                void handlePreviewExcel(file);
                return false;
              }}
            >
              <Button icon={<FileExcelOutlined />} loading={previewing}>
                导入 Excel
              </Button>
            </Upload>
          </Space>
        </Card>

        <Card
          title="同步状态"
          extra={
            <Button onClick={() => setSettingsOpen((open) => !open)}>
              {settingsOpen ? "收起同步设置" : "同步设置"}
            </Button>
          }
        >
          <Descriptions bordered size="small" column={2}>
            <Descriptions.Item label="同步目录" span={2}>
              {status?.sync_root || "-"}
            </Descriptions.Item>
            <Descriptions.Item label="检测到的 OneDrive 目录" span={2}>
              {status?.detected_dirs?.length
                ? status.detected_dirs.map((item) => item.path).join(" ; ")
                : "未检测到"}
            </Descriptions.Item>
            <Descriptions.Item label="定时同步">
              {status?.enabled ? <Tag color="success">已开启</Tag> : <Tag>未开启</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="同步间隔">
              {status?.interval_minutes ? `${status.interval_minutes} 分钟` : "-"}
            </Descriptions.Item>
            <Descriptions.Item label="上次同步时间">
              {status?.last_sync_at || "-"}
            </Descriptions.Item>
            <Descriptions.Item label="上次同步动作">
              {status?.last_sync_direction
                ? directionLabelMap[status.last_sync_direction] ?? status.last_sync_direction
                : "立即检查并同步时，会自动判断是推送本机最新数据还是拉取同步目录中的最新数据"}
            </Descriptions.Item>
            <Descriptions.Item label="最近错误">
              {status?.last_error ? <Typography.Text type="danger">{status.last_error}</Typography.Text> : "-"}
            </Descriptions.Item>
          </Descriptions>

          <Space wrap style={{ marginTop: 16 }}>
            <Button icon={<ReloadOutlined />} onClick={() => void fetchStatus()} loading={loading}>
              刷新状态
            </Button>
            <Button onClick={() => openSyncSettings(!status?.enabled)}>
              {status?.enabled ? "关闭同步" : "开启同步"}
            </Button>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={() => void runSync()}
              loading={syncing}
              disabled={!status?.configured}
            >
              立即检查并同步
            </Button>
          </Space>

          {settingsOpen ? (
            <>
              <Divider>同步设置</Divider>
              <List
                size="small"
                style={{ marginBottom: 16 }}
                dataSource={status?.detected_dirs ?? []}
                locale={{ emptyText: "未检测到 OneDrive 目录，可以手动输入路径" }}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        key="use"
                        size="small"
                        onClick={() => form.setFieldValue("sync_base_dir", buildSyncRoot(item.path))}
                      >
                        使用这个目录
                      </Button>,
                    ]}
                  >
                    <Space>
                      <Tag color="blue">{item.label}</Tag>
                      <Typography.Text>{item.path}</Typography.Text>
                    </Space>
                  </List.Item>
                )}
              />

              <Form form={form} layout="vertical">
                <Form.Item label="同步路径" required>
                  <Space.Compact style={{ width: "100%" }}>
                    <Form.Item
                      name="sync_base_dir"
                      noStyle
                      rules={[{ required: true, message: "请选择或输入同步路径" }]}
                    >
                      <Input placeholder="默认会带 sis-book-sync，手动输入时也可以自定义" />
                    </Form.Item>
                    <Button loading={browsingDir} onClick={() => void handleBrowseDir()}>
                      选择目录
                    </Button>
                  </Space.Compact>
                </Form.Item>

                <Space style={{ display: "flex" }} align="start" wrap>
                  <Form.Item name="enabled" label="启用定时同步" valuePropName="checked">
                    <Switch checkedChildren="开启" unCheckedChildren="关闭" />
                  </Form.Item>
                  <Form.Item
                    name="interval_minutes"
                    label="同步间隔（分钟）"
                    rules={[{ required: true, message: "请输入同步间隔" }]}
                  >
                    <InputNumber min={5} max={1440} style={{ width: 160 }} />
                  </Form.Item>
                  <Form.Item label=" ">
                    <Button
                      type="primary"
                      icon={<CloudSyncOutlined />}
                      onClick={handleSave}
                      loading={saving}
                    >
                      保存同步设置
                    </Button>
                  </Form.Item>
                </Space>
              </Form>
            </>
          ) : null}
        </Card>
      </Space>

      <Modal
        title="Excel 导入预览"
        open={previewOpen}
        width={980}
        onCancel={() => setPreviewOpen(false)}
        okText="确认导入"
        onOk={handleImportExcel}
        confirmLoading={importing}
        okButtonProps={{
          disabled: !hasImportableSheets || hasBlockingWarnings,
        }}
      >
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
          {previewSheets.map((sheet) => (
            <div key={sheet.name}>
              <Space wrap style={{ marginBottom: 8 }}>
                <Typography.Text strong>{sheet.name}</Typography.Text>
                {sheet.matched_label ? <Tag color="blue">{sheet.matched_label}</Tag> : <Tag>未匹配</Tag>}
                <Tag>{sheet.total_rows} 行</Tag>
              </Space>
              {sheet.warnings.map((warning) => (
                <Alert key={warning} type="warning" message={warning} showIcon style={{ marginBottom: 8 }} />
              ))}
              <Space wrap style={{ marginBottom: 8 }}>
                {sheet.mappings.map((mapping) => (
                  <Tag key={`${mapping.column}-${mapping.field}`}>
                    {mapping.column} → {mapping.label}
                  </Tag>
                ))}
              </Space>
              <Table
                size="small"
                rowKey="__index"
                columns={previewColumns(sheet)}
                dataSource={sheet.rows.map((row, index) => ({ ...row, __index: String(index) }))}
                pagination={false}
                scroll={{ x: "max-content" }}
              />
            </div>
          ))}
        </Space>
      </Modal>

      <Modal
        title="检测到同步冲突"
        open={conflictOpen}
        onCancel={() => setConflictOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setConflictOpen(false)}>
            取消
          </Button>,
          <Button
            key="pull"
            onClick={async () => {
              setConflictOpen(false);
              await runSync("pull");
            }}
          >
            以同步目录为准
          </Button>,
          <Button
            key="push"
            type="primary"
            onClick={async () => {
              setConflictOpen(false);
              await runSync("push");
            }}
          >
            以本机为准
          </Button>,
        ]}
      >
        <Typography.Paragraph>
          检测到本机和同步目录都发生了变更，当前不会自动覆盖。
        </Typography.Paragraph>
        <Descriptions bordered size="small" column={1}>
          <Descriptions.Item label="本机设备">
            {conflictData?.local_device_name || "当前设备"}
          </Descriptions.Item>
          <Descriptions.Item label="同步目录来源设备">
            {conflictData?.remote_device_name || "-"}
          </Descriptions.Item>
          <Descriptions.Item label="本机最近更新时间">
            {conflictData?.local_updated_at_ns
              ? new Date(conflictData.local_updated_at_ns / 1_000_000).toLocaleString()
              : "-"}
          </Descriptions.Item>
          <Descriptions.Item label="同步目录最近更新时间">
            {conflictData?.remote_updated_at_ns
              ? new Date(conflictData.remote_updated_at_ns / 1_000_000).toLocaleString()
              : "-"}
          </Descriptions.Item>
        </Descriptions>
      </Modal>
    </div>
  );
}
