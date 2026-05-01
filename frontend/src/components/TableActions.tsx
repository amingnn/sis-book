import { Button, Popconfirm, Space } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { ReactNode } from "react";

export interface TableAction<T> {
  key: string;
  label: string;
  icon?: ReactNode;
  danger?: boolean;
  disabled?: boolean;
  confirmTitle?: string;
  onClick: (record: T) => void;
}

export function renderTableActions<T>(record: T, actions: TableAction<T>[]) {
  return (
    <Space size="small" wrap={false}>
      {actions.map((action) => {
        const button = (
          <Button
            size="small"
            danger={action.danger}
            icon={action.icon}
            disabled={action.disabled}
            onClick={() => action.onClick(record)}
          >
            {action.label}
          </Button>
        );

        if (!action.confirmTitle) {
          return <span key={action.key}>{button}</span>;
        }

        return (
          <Popconfirm
            key={action.key}
            title={action.confirmTitle}
            onConfirm={() => action.onClick(record)}
          >
            <Button
              size="small"
              danger={action.danger}
              icon={action.icon}
              disabled={action.disabled}
            >
              {action.label}
            </Button>
          </Popconfirm>
        );
      })}
    </Space>
  );
}

export function createActionColumn<T>(
  actions: TableAction<T>[],
  width = 180,
): ColumnsType<T>[number] {
  return {
    title: "操作",
    key: "actions",
    width,
    render: (_, record) => renderTableActions(record, actions),
  };
}
