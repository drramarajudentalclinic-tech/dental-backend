import axios from "axios";

// -----------------------
// BASE URL (AUTO SWITCH)
// -----------------------
const BASE_URL =
  window.location.hostname === "localhost"
    ? "http://localhost:5000/api"   // Local
    : "https://dental-backend-xojn.onrender.com/api"; // Live

// -----------------------
// CREATE AXIOS INSTANCE
// -----------------------
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// -----------------------
// REQUEST INTERCEPTOR
// -----------------------
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");

    // ✅ Attach JWT token automatically
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    console.log(
      `API REQUEST: [${config.method?.toUpperCase()}] ${config.baseURL}${config.url}`,
      config.data || config.params
    );

    return config;
  },
  (error) => Promise.reject(error)
);

// -----------------------
// RESPONSE INTERCEPTOR
// -----------------------
api.interceptors.response.use(
  (response) => {
    console.log("API RESPONSE:", response.data);
    return response;
  },
  (error) => {
    // 🔴 Server responded with error
    if (error.response) {
      console.error("API ERROR:", error.response.data);

      // 🔐 Handle Unauthorized (JWT expired / invalid)
      if (error.response.status === 401) {
        alert("Session expired. Please login again.");

        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    }
    // 🔴 No response (server down / network issue)
    else if (error.request) {
      console.error("API ERROR: No response from server");
    alert("Server is starting... please wait a few seconds and retry.");
    }
    // 🔴 Other error
    else {
      console.error("API ERROR:", error.message);
    }

    return Promise.reject(error);
  }
);

export default api;