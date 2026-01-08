import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { authClient } from './auth';

// Create the base axios instance
const apiClient: AxiosInstance = axios.create({
  // Backend port 8001 confirm karein
  // baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || 'https://iqoonaz4321-taskneon-app.hf.space',
     baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://iqoonaz4321-phase-3.hf.space',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor: Token attach karne ke liye
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const session = await authClient.getSession();
      // Better Auth session token extraction
      if (session?.data?.session?.token) {
        config.headers.Authorization = `Bearer ${session.data.session.token}`;
      }
    } catch (e) {
      console.error("Auth session error:", e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Errors ko handle karne ke liye
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMessage = 'An unexpected error occurred';
    let errorCode = 'UNKNOWN_ERROR';

    if (error.response) {
      // Server responded with a status code outside the 2xx range
      const data = error.response.data;
      
      // FastAPI typically sends error in 'detail' field
      if (data && typeof data === 'object') {
        errorMessage = data.detail || data.error?.message || JSON.stringify(data);
        errorCode = data.error?.code || error.response.status.toString();
      } else if (typeof data === 'string') {
        errorMessage = data;
      }
    } else if (error.request) {
      // Request was made but no response was received
      errorMessage = 'No response from server. Is the backend running on port 8001?';
      errorCode = 'NETWORK_ERROR';
    } else {
      errorMessage = error.message;
    }

    // Creating a custom error object that won't break the UI
    const apiError = new Error(errorMessage);
    (apiError as any).code = errorCode;
    (apiError as any).status = error.response?.status;

    return Promise.reject(apiError);
  }
);

export { apiClient };