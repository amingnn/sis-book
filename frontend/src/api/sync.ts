import client from "./client";

export interface SyncStatus {
  sync_base_dir: string;
  enabled: boolean;
  interval_minutes: number;
  last_sync_at: string;
  last_sync_direction: string;
  last_error: string;
  detected_dirs: Array<{
    path: string;
    label: string;
  }>;
  sync_root: string;
  configured: boolean;
}

export interface SyncRunResult {
  ok: boolean;
  direction: string;
  trigger: string;
  sync_root: string;
  last_sync_at: string;
  conflict?: {
    local_updated_at_ns: number;
    remote_updated_at_ns: number;
    local_device_name: string;
    remote_device_name: string;
  } | null;
}

export const syncApi = {
  getStatus: () => client.get<SyncStatus>("/sync/status"),
  saveSettings: (payload: {
    sync_base_dir: string;
    enabled: boolean;
    interval_minutes: number;
  }) => client.put("/sync/settings", payload),
  browseDir: () => client.post<{ path: string }>("/sync/browse"),
  runNow: (forceDirection = "") =>
    client.post<SyncRunResult>("/sync/run", { force_direction: forceDirection }),
};
