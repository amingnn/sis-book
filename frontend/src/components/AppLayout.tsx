import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  HomeOutlined,
  AccountBookOutlined,
  ShoppingCartOutlined,
  FileTextOutlined,
  CheckSquareOutlined,
  SettingOutlined,
  UserOutlined,
  ShopOutlined,
  AppstoreOutlined,
  BarChartOutlined,
  ImportOutlined,
} from "@ant-design/icons";

const { Sider, Content } = Layout;

const menuItems = [
  { key: "/", icon: <HomeOutlined />, label: "首页" },
  { key: "/sales", icon: <AccountBookOutlined />, label: "销售记录" },
  { key: "/purchases", icon: <ShoppingCartOutlined />, label: "采购单" },
  { key: "/orders", icon: <FileTextOutlined />, label: "开单" },
  { key: "/customers", icon: <UserOutlined />, label: "客户" },
  { key: "/suppliers", icon: <ShopOutlined />, label: "厂家" },
  { key: "/products", icon: <AppstoreOutlined />, label: "产品" },
  { key: "/data-overview", icon: <BarChartOutlined />, label: "数据总览" },
  { key: "/import-export", icon: <ImportOutlined />, label: "导入导出" },
  { key: "/tasks", icon: <CheckSquareOutlined />, label: "任务待办" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        style={{ borderRight: "1px solid #f0f0f0" }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: collapsed ? 0 : 10,
            fontWeight: 700,
            fontSize: collapsed ? 12 : 16,
            color: "#d95f0e",
            borderBottom: "1px solid #f0f0f0",
            padding: collapsed ? 8 : "0 12px",
          }}
        >
          <img
            src="/branding/app-icon-192.png"
            alt="暮橙体育记账本图标"
            style={{
              width: collapsed ? 26 : 30,
              height: collapsed ? 26 : 30,
              borderRadius: 8,
              flexShrink: 0,
            }}
          />
          {!collapsed ? <span>暮橙体育记账本</span> : null}
        </div>
        <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)" }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ borderInlineEnd: "none", flex: 1 }}
          />
          <div style={{ paddingBottom: 48 }}>
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              items={[{ key: "/data-management", icon: <SettingOutlined />, label: "数据管理" }]}
              onClick={({ key }) => navigate(key)}
              style={{ borderInlineEnd: "none", borderTop: "1px solid #f0f0f0" }}
            />
          </div>
        </div>
      </Sider>
      <Content style={{ padding: 24, background: "#f5f5f5", overflow: "auto" }}>
        <Outlet />
      </Content>
    </Layout>
  );
}
