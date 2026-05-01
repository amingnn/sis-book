import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Col,
  Collapse,
  Descriptions,
  Form,
  Input,
  InputNumber,
  List,
  Modal,
  Row,
  Space,
  Switch,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import {
  CloudSyncOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FilePdfOutlined,
  ImportOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { syncApi, type SyncStatus } from "../api/sync";
import { importExportApi } from "../api/importExport";

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

export default function DataManagement() {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [conflictOpen, setConflictOpen] = useState(false);
  const [conflictData, setConflictData] = useState<{
    local_updated_at_ns: number;
    remote_updated_at_ns: number;
    local_device_name: string;
    remote_device_name: string;
  } | null>(null);
  const [form] = Form.useForm();

  const fetchStatus = async () => {
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
  };

  useEffect(() => {
    void fetchStatus();
  }, []);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await syncApi.saveSettings(values);
      message.success("同步设置已保存");
      setSettingsOpen(false);
      await fetchStatus();
    } catch {
      /* ignore form validation */
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
    } catch {
      message.error("立即同步失败");
    } finally {
      setSyncing(false);
    }
  };

  const handleRunNow = async () => {
    await runSync();
  };

  const handleToggleSync = async (enabled: boolean) => {
    if (!status) return;
    const syncBaseDir = status.sync_root || status.sync_base_dir;
    if (enabled && !syncBaseDir) {
      message.warning("请先设置同步路径");
      setSettingsOpen(true);
      return;
    }
    setSaving(true);
    try {
      await syncApi.saveSettings({
        sync_base_dir: syncBaseDir,
        enabled,
        interval_minutes: status.interval_minutes || 30,
      });
      message.success(enabled ? "定时同步已开启" : "定时同步已关闭");
      await fetchStatus();
    } catch {
      message.error(enabled ? "开启同步失败" : "关闭同步失败");
    } finally {
      setSaving(false);
    }
  };

  const runImportExportPlaceholder = async (
    action: () => Promise<unknown>,
    successText: string,
  ) => {
    await action();
    message.info(successText);
  };

  return (
    <div>
      <Typography.Title level={4}>数据管理</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={15}>
          <Card title="同步状态">
            <Descriptions bordered size="small" column={1}>
              <Descriptions.Item label="同步目录">
                {status?.sync_root || "-"}
              </Descriptions.Item>
              <Descriptions.Item label="检测到的 OneDrive 目录">
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
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleRunNow}
                loading={syncing}
                disabled={!status?.configured}
              >
                立即检查并同步
              </Button>
              <Button
                danger={status?.enabled}
                onClick={() => void handleToggleSync(!status?.enabled)}
                loading={saving}
                disabled={!status || (!status.enabled && !status.configured)}
              >
                {status?.enabled ? "关闭定时同步" : "开启定时同步"}
              </Button>
            </Space>
          </Card>
        </Col>
        <Col xs={24} xl={9}>
          <Card title="导入导出">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Button
                block
                type="primary"
                icon={<DownloadOutlined />}
                onClick={() =>
                  runImportExportPlaceholder(importExportApi.exportCsv, "CSV 导出接口已预留")
                }
              >
                导出 CSV
              </Button>
              <Button
                block
                icon={<FilePdfOutlined />}
                onClick={() =>
                  runImportExportPlaceholder(importExportApi.exportPdf, "PDF 导出接口已预留")
                }
              >
                导出 PDF
              </Button>
              <Upload
                accept=".csv"
                showUploadList={false}
                beforeUpload={() => {
                  void runImportExportPlaceholder(importExportApi.importCsv, "CSV 导入接口已预留");
                  return false;
                }}
              >
                <Button block icon={<ImportOutlined />}>导入 CSV</Button>
              </Upload>
              <Upload
                accept=".xlsx,.xls"
                showUploadList={false}
                beforeUpload={() => {
                  void runImportExportPlaceholder(importExportApi.importExcel, "Excel 导入接口已预留");
                  return false;
                }}
              >
                <Button block icon={<FileExcelOutlined />}>导入 Excel</Button>
              </Upload>
            </Space>
          </Card>
        </Col>
      </Row>

      <Collapse
        style={{ marginTop: 16 }}
        activeKey={settingsOpen ? ["settings"] : []}
        onChange={(keys) => setSettingsOpen(keys.length > 0)}
        items={[
          {
            key: "settings",
            label: `同步设置${status?.detected_dirs?.length ? `（检测到 ${status.detected_dirs.length} 个 OneDrive 目录）` : ""}`,
            children: (
              <div>
                <Typography.Title level={5} style={{ marginTop: 0 }}>
                  检测到的 OneDrive 目录
                </Typography.Title>
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
                  <Form.Item
                    label="同步路径"
                    name="sync_base_dir"
                    rules={[{ required: true, message: "请选择或输入同步路径" }]}
                  >
                    <Input placeholder="默认会带 sis-book-sync，手动输入时也可以自定义" />
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
                  </Space>

                  <Button
                    type="primary"
                    icon={<CloudSyncOutlined />}
                    onClick={handleSave}
                    loading={saving}
                  >
                    保存同步设置
                  </Button>
                </Form>
              </div>
            ),
          },
        ]}
      />

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
