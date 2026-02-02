import axios from "axios"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// Interceptor Request
api.interceptors.request.use(config => {
  const token = localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor Response
api.interceptors.response.use(
  response => response,
  error => {
    console.error("API error:", error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const getMachines = () => api.get("/machines")
export const getKPI = (id, date) => api.get(`/kpis/${machineId}/${date}`)
export const getAlerts = () => api.get("/alerts")

export default api
