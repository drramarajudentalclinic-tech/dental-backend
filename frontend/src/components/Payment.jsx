// Payment.jsx — billing is handled in Reception Dashboard → Billing tab
import { useNavigate } from "react-router-dom";

export default function Payment({ visitId }) {
  const navigate = useNavigate();

  return (
    <div style={{
      textAlign: "center",
      padding: "48px 24px",
      background: "#f8faff",
      borderRadius: 14,
      border: "1.5px dashed #c7d9fc",
    }}>
      <div style={{ fontSize: 40, marginBottom: 14 }}>💳</div>
      <div style={{ fontSize: 16, fontWeight: 800, color: "#0f2a50", marginBottom: 8 }}>
        Billing &amp; Payments
      </div>
      <div style={{ fontSize: 13.5, color: "#64748b", marginBottom: 24, lineHeight: 1.6 }}>
        Billing for this visit is managed from the Reception Dashboard.
      </div>
      <button
        onClick={() => navigate("/reception/dashboard?section=billing")}
        style={{
          display: "inline-flex", alignItems: "center", gap: 8,
          padding: "10px 24px", borderRadius: 10,
          background: "linear-gradient(135deg,#1d4d7a,#1d6fa4)",
          color: "#fff", border: "none",
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          fontSize: 13, fontWeight: 700, cursor: "pointer",
          boxShadow: "0 4px 12px rgba(29,77,122,0.25)",
        }}
      >
        Go to Billing →
      </button>
    </div>
  );
}