import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import ReceptionDashboard from "./pages/ReceptionDashboard";
import DoctorDashboard from "./pages/DoctorDashboard";
import VisitPage from "./pages/VisitPage";
import BillingPage from "./pages/BillingPage";
import EditPatient from "./pages/EditPatient";
import DoctorPatientView from "./pages/DoctorPatientView";
import ReceptionPatientForm from "./pages/ReceptionPatientForm";
import AppointmentsDiary from "./pages/AppointmentsDiary.jsx";

// ── TEMP: Navigation tracer — remove after finding the bug ──
function NavTracer() {
  const location = useLocation();
  useEffect(() => {
    console.trace("🔴 NAVIGATED TO:", location.pathname + location.search);
  }, [location]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <NavTracer />
      <Routes>

        <Route path="/" element={<Navigate to="/reception/dashboard" replace />} />
        <Route path="/reception" element={<Navigate to="/reception/dashboard" replace />} />
        <Route path="/doctor" element={<Navigate to="/doctor/dashboard" replace />} />

        {/* Reception */}
        <Route path="/reception/dashboard"    element={<ReceptionDashboard />} />
        <Route path="/reception/patient/new"  element={<ReceptionPatientForm />} />
        <Route path="/reception/patient/:id"  element={<ReceptionPatientForm />} />
        <Route path="/reception/appointments" element={<AppointmentsDiary />} />

        {/* Doctor */}
        <Route path="/doctor/dashboard"       element={<DoctorDashboard />} />
        <Route path="/doctor/patient/:id"     element={<DoctorPatientView />} />
        <Route path="/doctor/visit/:visitId"  element={<VisitPage />} />

        {/* Common */}
        <Route path="/visit/:visitId"         element={<VisitPage />} />
        <Route path="/billing/:visitId"       element={<BillingPage />} />
        <Route path="/patients/edit/:id"      element={<EditPatient />} />

        {/* Fallback */}
        <Route path="*" element={<h1>404 - Page Not Found</h1>} />

      </Routes>
    </BrowserRouter>
  );
}