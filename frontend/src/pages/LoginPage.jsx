import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "", role: "reception" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/auth/login", {
        username: form.username,
        password: form.password,
      });

      const { access_token, role, username } = res.data;

      // Validate role matches selection
      if (role !== form.role) {
        setError(`Invalid role. You are registered as ${role}.`);
        setLoading(false);
        return;
      }

      // Save to localStorage
      localStorage.setItem("token", access_token);
      localStorage.setItem("role", role);
      localStorage.setItem("username", username);

      // Redirect based on role
      if (role === "doctor") {
        navigate("/doctor/dashboard");
      } else {
        navigate("/reception/dashboard");
      }
    } catch (err) {
      setError("Invalid username or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>🦷 Dental Clinic</h2>
        <p style={styles.subtitle}>Please login to continue</p>

        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.roleRow}>
          <button
            style={form.role === "reception" ? styles.roleActive : styles.roleBtn}
            onClick={() => setForm({ ...form, role: "reception" })}
          >
            👩‍💼 Reception
          </button>
          <button
            style={form.role === "doctor" ? styles.roleActive : styles.roleBtn}
            onClick={() => setForm({ ...form, role: "doctor" })}
          >
            👨‍⚕️ Doctor
          </button>
        </div>

        <input
          style={styles.input}
          placeholder="Username"
          value={form.username}
          onChange={e => setForm({ ...form, username: e.target.value })}
        />
        <input
          style={styles.input}
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={e => setForm({ ...form, password: e.target.value })}
          onKeyDown={e => e.key === "Enter" && handleSubmit()}
        />

        <button style={styles.loginBtn} onClick={handleSubmit} disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f0f4f8" },
  card: { background: "white", padding: "40px", borderRadius: "12px", boxShadow: "0 4px 20px rgba(0,0,0,0.1)", width: "100%", maxWidth: "400px" },
  title: { textAlign: "center", fontSize: "24px", marginBottom: "4px" },
  subtitle: { textAlign: "center", color: "#666", marginBottom: "24px" },
  error: { background: "#fee", color: "#c00", padding: "10px", borderRadius: "6px", marginBottom: "16px", textAlign: "center" },
  roleRow: { display: "flex", gap: "12px", marginBottom: "20px" },
  roleBtn: { flex: 1, padding: "10px", border: "2px solid #ddd", borderRadius: "8px", background: "white", cursor: "pointer", fontSize: "14px" },
  roleActive: { flex: 1, padding: "10px", border: "2px solid #2563eb", borderRadius: "8px", background: "#eff6ff", cursor: "pointer", fontSize: "14px", fontWeight: "bold", color: "#2563eb" },
  input: { width: "100%", padding: "12px", marginBottom: "12px", border: "1px solid #ddd", borderRadius: "8px", fontSize: "14px", boxSizing: "border-box" },
  loginBtn: { width: "100%", padding: "12px", background: "#2563eb", color: "white", border: "none", borderRadius: "8px", fontSize: "16px", cursor: "pointer", fontWeight: "bold" },
};