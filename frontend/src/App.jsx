import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import HomePage from "./pages/HomePage";
import FormPage from "./pages/FormPage";
import ReportPage from "./pages/ReportPage";
import LeadDetailPage from "./pages/LeadDetailPage";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/form" element={<FormPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/lead/:id" element={<LeadDetailPage />} />
      </Routes>
    </Router>
  );
}