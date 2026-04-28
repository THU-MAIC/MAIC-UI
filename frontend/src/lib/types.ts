export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  grade_level?: number
  interests: string[]
  learning_preferences: Record<string, any>
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
  grade_level?: number
  interests?: string[]
  learning_preferences?: Record<string, any>
}