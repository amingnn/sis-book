import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import SalesRecords from "./pages/SalesRecords";
import Purchases from "./pages/Purchases";
import Orders from "./pages/Orders";
import Tasks from "./pages/Tasks";
import DataManagement from "./pages/DataManagement";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sales" element={<SalesRecords />} />
          <Route path="/purchases" element={<Purchases />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/data-management" element={<DataManagement />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
