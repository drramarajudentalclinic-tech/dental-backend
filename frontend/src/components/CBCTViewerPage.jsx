 /**
 * CBCTViewerPage.jsx
 *
 * Standalone page rendered in a new tab when the user clicks "View CBCT".
 *
 * Add this route in your App.jsx / router:
 *   <Route path="/cbct-viewer" element={<CBCTViewerPage />} />
 *
 * It reads volumeId from the URL query string (?volumeId=42)
 * and apiBase from localStorage (set by CBCTSection before opening the tab).
 */

import React from "react";
import CBCTViewer from "./CBCTViewer";

export default function CBCTViewerPage() {
  const params   = new URLSearchParams(window.location.search);
  const volumeId = Number(params.get("volumeId"));

  // apiBase written by CBCTSection before opening the tab
  let apiBase = "/api";
  try {
    const stored = localStorage.getItem("cbct_viewer_params");
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.apiBase) apiBase = parsed.apiBase;
    }
  } catch (_) {}

  if (!volumeId) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "#020617", color: "#ef4444", fontFamily: "monospace", fontSize: 18 }}>
        ⚠️ No volume ID provided. Please open this page from the CBCT section.
      </div>
    );
  }

  return (
    <CBCTViewer
      volumeId={volumeId}
      apiBase={apiBase}
      onClose={() => window.close()}   // closes the tab
    />
  );
}