import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Spin } from "antd";

import AppLayout from "./components/AppLayout";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const DataOverview = lazy(() => import("./pages/DataOverview"));
const SalesRecords = lazy(() => import("./pages/SalesRecords"));
const Purchases = lazy(() => import("./pages/Purchases"));
const Orders = lazy(() => import("./pages/Orders"));
const Customers = lazy(() => import("./pages/Customers"));
const Suppliers = lazy(() => import("./pages/Suppliers"));
const Products = lazy(() => import("./pages/Products"));
const Tasks = lazy(() => import("./pages/Tasks"));
const DataManagement = lazy(() => import("./pages/DataManagement"));

function PageFallback() {
  return (
    <div style={{ textAlign: "center", padding: 80 }}>
      <Spin size="large" />
    </div>
  );
}

function withFallback(page: ReactNode) {
  return <Suspense fallback={<PageFallback />}>{page}</Suspense>;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={withFallback(<Dashboard />)} />
          <Route path="/data-overview" element={withFallback(<DataOverview />)} />
          <Route path="/sales" element={withFallback(<SalesRecords />)} />
          <Route path="/purchases" element={withFallback(<Purchases />)} />
          <Route path="/orders" element={withFallback(<Orders />)} />
          <Route path="/customers" element={withFallback(<Customers />)} />
          <Route path="/suppliers" element={withFallback(<Suppliers />)} />
          <Route path="/products" element={withFallback(<Products />)} />
          <Route path="/tasks" element={withFallback(<Tasks />)} />
          <Route path="/data-management" element={withFallback(<DataManagement />)} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
