import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatResponse {
  response: string
  history: Message[]
  hackathon_data?: any
}

interface HistoryResponse {
  history: Message[]
}

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const sendMessage = async (message: string, userId: string = 'default_user'): Promise<ChatResponse> => {
  try {
    const response = await api.post<ChatResponse>('/api/spotbot/query', {
      message,
      user_id: userId,
    })
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

export const getHistory = async (userId: string = 'default_user'): Promise<HistoryResponse> => {
  try {
    const response = await api.get<HistoryResponse>(`/api/spotbot/history/${userId}`)
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

export const clearHistory = async (userId: string = 'default_user'): Promise<{ message: string; user_id: string }> => {
  try {
    const response = await api.post<{ message: string; user_id: string }>(`/api/spotbot/clear/${userId}`)
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

export const createHackathon = async (hackathonData: any, userId: string = 'default_user'): Promise<{ success: boolean; hackathon: any; message?: string }> => {
  try {
    const response = await api.post<{ success: boolean; hackathon: any; message?: string }>('/api/spotbot/create', {
      hackathon_data: hackathonData,
      user_id: userId,
    })
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

export type { Message, ChatResponse, HistoryResponse }
