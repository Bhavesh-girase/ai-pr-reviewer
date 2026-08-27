import axios from 'axios'

// Resolve backend URL with development server fallback
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  timeout: 180000, // 3 minutes timeout to accommodate cloning, hybrid retrieval, and AI generation pipelines
  headers: {
    'Content-Type': 'application/json',
  },
})

// Global response interceptor for parsing backend errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // FastAPI HTTPExceptions put error details in response.data.detail
    const detail = error.response?.data?.detail
    let message = 'An unexpected error occurred while communicating with the API.'

    if (typeof detail === 'string') {
      message = detail
    } else if (Array.isArray(detail)) {
      // Handle standard FastAPI validation errors list
      message = detail.map((err) => `${err.loc?.join('.') || 'input'}: ${err.msg}`).join('; ')
    } else if (error.response?.data?.message) {
      message = error.response.data.message
    } else if (error.message) {
      message = error.message
    }

    return Promise.reject(new Error(message))
  }
)
