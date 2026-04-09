import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  HomeOutlined,
  AccountBookOutlined,
  ShoppingCartOutlined,
  FileTextOutlined,
} from "@ant-design/icons";

const { Sider, Content } = Layout;

const menuItems = [
  { key: "/", icon: <HomeOutlined />, label: "首页" },
  { key: "/sales", icon: <AccountBookOutlined />, label: "销售记录" },
  { key: "/purchases", icon: <ShoppingCartOutlined />, label: "采购单" },
  { key: "/orders", icon: <FileTextOutlined />, label: "开单" },
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
            height: 48,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            fontSize: collapsed ? 14 : 16,
            color: "#1677ff",
            borderBottom: "1px solid #f0f0f0",
          }}
        >
          {collapsed ? "暮橙" : "暮橙体育记账本"}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Content style={{ padding: 24, background: "#f5f5f5", overflow: "auto" }}>
        <Outlet />
      </Content>
    </Layout>
  );
}
