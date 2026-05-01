import { Button, Input, Space, Typography } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import type { ReactNode } from "react";

interface PageToolbarProps {
  title: string;
  leading?: ReactNode;
  searchValue?: string;
  searchPlaceholder?: string;
  onSearchChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  primaryText?: string;
  primaryIcon?: ReactNode;
  onPrimaryClick?: () => void;
  extra?: ReactNode;
}

export default function PageToolbar({
  title,
  leading,
  searchValue,
  searchPlaceholder,
  onSearchChange,
  onSearch,
  primaryText,
  primaryIcon,
  onPrimaryClick,
  extra,
}: PageToolbarProps) {
  const showSearch = searchValue !== undefined && onSearchChange && onSearch;

  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 16, marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {leading}
        <Typography.Title level={4} style={{ margin: 0 }}>
          {title}
        </Typography.Title>
      </div>
      <Space wrap>
        {extra}
        {showSearch ? (
          <Input.Search
            placeholder={searchPlaceholder}
            allowClear
            prefix={<SearchOutlined />}
            value={searchValue}
            onChange={(event) => onSearchChange(event.target.value)}
            onSearch={onSearch}
            style={{ width: 260 }}
          />
        ) : null}
        {primaryText && onPrimaryClick ? (
          <Button type="primary" icon={primaryIcon} onClick={onPrimaryClick}>
            {primaryText}
          </Button>
        ) : null}
      </Space>
    </div>
  );
}
