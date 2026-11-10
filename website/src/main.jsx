import React, { lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./styles.css";
import Home from "./pages/Home";
/* portal and not-found pages load only when opened, so the home page opens faster */
const PortalLogin = lazy(() => import("./pages/PortalLogin"));
const PortalRecord = lazy(() => import("./pages/PortalRecord"));
const NotFound = lazy(() => import("./pages/NotFound"));

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Suspense fallback={<p style={{ padding: 40, textAlign: "center" }}>Loading…</p>}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/portal" element={<PortalLogin />} />
        <Route path="/portal/record/:pid" element={<PortalRecord />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
    </BrowserRouter>
  </React.StrictMode>,
);
