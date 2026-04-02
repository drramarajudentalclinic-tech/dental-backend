import axios from "axios";

// -----------------------
// CREATE AXIOS INSTANCE
// -----------------------
const api = axios.create({
  baseURL: "http://localhost:5000/api", // FIX: use localhost, not 127.0.0.1
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
  timeout: 10000,
});

// -----------------------
// REQUEST INTERCEPTOR
// -----------------------
api.interceptors.request.use(
  (config) => {
    console.log(
      `API REQUEST: [${config.method.toUpperCase()}] ${config.url}`,
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
    if (error.response) {
      console.error("API ERROR:", error.response.data);
    } else if (error.request) {
      console.error("API ERROR: No response from server");
    } else {
      console.error("API ERROR:", error.message);
    }
    return Promise.reject(error);
  }
);

export default api;