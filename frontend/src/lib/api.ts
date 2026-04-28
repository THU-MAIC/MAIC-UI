import axios from 'axios'
import Cookies from 'js-cookie'
import { AuthResponse, LoginCredentials, RegisterData, User } from './types'

// Dynamic API base URL that works with both localhost and external IP access
const getApiBaseUrl = () => {
  // If NEXT_PUBLIC_API_URL is explicitly set, use it
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }

  // For server-side rendering or when window is not available, use relative path
  if (typeof window === 'undefined') {
    return '/api'
  }

  // For production, check if we're accessing via external IP
  if (process.env.NODE_ENV === 'production') {
    const hostname = window.location.hostname
    // If accessing via IP address, use full URL, otherwise use relative path
    if (/^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
      return `${window.location.protocol}//${hostname}:${window.location.port}/api`
    }
    return '/api'
  }

  // Development fallback
  return `${window.location.protocol}//${window.location.hostname}:8000/api`
}

const API_BASE_URL = getApiBaseUrl()

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear it and redirect to login
      Cookies.remove('access_token', {
        secure: process.env.NODE_ENV === 'production' && (typeof window !== 'undefined' && window.location.protocol === 'https:'),
        sameSite: process.env.NODE_ENV === 'production' ? 'lax' : 'none'
      })
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials)

    // Store token in cookies
    Cookies.set('access_token', response.data.access_token, {
      expires: 7, // 7 days
      secure: process.env.NODE_ENV === 'production' && (typeof window !== 'undefined' && window.location.protocol === 'https:'),
      sameSite: process.env.NODE_ENV === 'production' ? 'lax' : 'none'
    })

    return response.data
  },

  register: async (userData: RegisterData): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', userData)

    // Store token in cookies
    Cookies.set('access_token', response.data.access_token, {
      expires: 7, // 7 days
      secure: process.env.NODE_ENV === 'production' && (typeof window !== 'undefined' && window.location.protocol === 'https:'),
      sameSite: process.env.NODE_ENV === 'production' ? 'lax' : 'none'
    })

    return response.data
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout')
    } finally {
      // Always remove token even if API call fails
      Cookies.remove('access_token', {
        secure: process.env.NODE_ENV === 'production' && (typeof window !== 'undefined' && window.location.protocol === 'https:'),
        sameSite: process.env.NODE_ENV === 'production' ? 'lax' : 'none'
      })
    }
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  verifyToken: async (): Promise<{ valid: boolean; payload?: any }> => {
    try {
      const response = await api.post('/auth/verify-token')
      return response.data
    } catch (error) {
      return { valid: false }
    }
  },
}

export default api