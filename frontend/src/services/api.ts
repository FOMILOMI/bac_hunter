import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { toast } from 'react-hot-toast'

// Types for API responses
interface APIResponse<T> {
  data: T
  message?: string
  success: boolean
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api/v2',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Generic API functions
const apiService = {
  get: <T>(url: string, params?: any): Promise<T> =>
    api.get(url, { params }).then((res) => res.data),
  
  post: <T>(url: string, data?: any): Promise<T> =>
    api.post(url, data).then((res) => res.data),
  
  put: <T>(url: string, data?: any): Promise<T> =>
    api.put(url, data).then((res) => res.data),
  
  delete: <T>(url: string): Promise<T> =>
    api.delete(url).then((res) => res.data),
  
  patch: <T>(url: string, data?: any): Promise<T> =>
    api.patch(url, data).then((res) => res.data),
}

// Projects API
export const projectsAPI = {
  getAll: () => apiService.get<{ projects: any[] }>('/projects'),
  getById: (id: string) => apiService.get<any>(`/projects/${id}`),
  create: (data: any) => apiService.post<any>('/projects', data),
  update: (id: string, data: any) => apiService.put<any>(`/projects/${id}`, data),
  delete: (id: string) => apiService.delete<any>(`/projects/${id}`),
  export: (id: string, format: string) => apiService.get<any>(`/projects/${id}/export`, { format }),
  import: (data: any) => apiService.post<any>('/projects/import', data),
}

// Scans API
export const scansAPI = {
  getAll: () => apiService.get<{ scans: any[] }>('/scans'),
  getById: (id: string) => apiService.get<any>(`/scans/${id}`),
  create: (data: any) => apiService.post<any>('/scans', data),
  update: (id: string, data: any) => apiService.put<any>(`/scans/${id}`, data),
  delete: (id: string) => apiService.delete<any>(`/scans/${id}`),
  start: (id: string) => apiService.post<any>(`/scans/${id}/start`),
  stop: (id: string) => apiService.post<any>(`/scans/${id}/stop`),
  pause: (id: string) => apiService.post<any>(`/scans/${id}/pause`),
  resume: (id: string) => apiService.post<any>(`/scans/${id}/resume`),
  getProgress: (id: string) => apiService.get<any>(`/scans/${id}/progress`),
  getLogs: (id: string) => apiService.get<any>(`/scans/${id}/logs`),
  getMetrics: (id: string) => apiService.get<any>(`/scans/${id}/metrics`),
}

// Findings API
export const findingsAPI = {
  getAll: () => apiService.get<{ findings: any[] }>('/findings'),
  getById: (id: string) => apiService.get<any>(`/findings/${id}`),
  create: (data: any) => apiService.post<any>('/findings', data),
  update: (id: string, data: any) => apiService.put<any>(`/findings/${id}`, data),
  delete: (id: string) => apiService.delete<any>(`/findings/${id}`),
  updateStatus: (findingId: string, status: string) => 
    apiService.patch<any>(`/findings/${findingId}/status`, { status }),
  getByProject: (projectId: string) => apiService.get<any>(`/projects/${projectId}/findings`),
  getByScan: (scanId: string) => apiService.get<any>(`/scans/${scanId}/findings`),
  export: (filters?: any) => apiService.get<any>('/findings/export', filters),
}

// AI Insights API
export const aiInsightsAPI = {
  getAll: () => apiService.get<{ insights: any[] }>('/ai-insights'),
  getById: (id: string) => apiService.get<any>(`/ai-insights/${id}`),
  create: (data: any) => apiService.post<any>('/ai-insights', data),
  update: (id: string, data: any) => apiService.put<any>(`/ai-insights/${id}`, data),
  delete: (id: string) => apiService.delete<any>(`/ai-insights/${id}`),
  updateFeedback: (insightId: string, feedback: any) => 
    apiService.patch<any>(`/ai-insights/${insightId}/feedback`, feedback),
  getByProject: (projectId: string) => apiService.get<any>(`/projects/${projectId}/ai-insights`),
  getByScan: (scanId: string) => apiService.get<any>(`/scans/${scanId}/ai-insights`),
  generate: (data: any) => apiService.post<any>('/ai-insights/generate', data),
}

// Reports API
export const reportsAPI = {
  getAll: () => apiService.get<{ reports: any[] }>('/reports'),
  getById: (id: string) => apiService.get<any>(`/reports/${id}`),
  generate: (data: any) => apiService.post<any>('/reports/generate', data),
  update: (id: string, data: any) => apiService.put<any>(`/reports/${id}`, data),
  delete: (id: string) => apiService.delete<any>(`/reports/${id}`),
  download: (id: string, format: string) => apiService.get<any>(`/reports/${id}/download`, { format }),
  getTemplates: () => apiService.get<any>('/reports/templates'),
  saveTemplate: (data: any) => apiService.post<any>('/reports/templates', data),
}

// Sessions API
export const sessionsAPI = {
  getAll: () => apiService.get<{ sessions: any[] }>('/sessions'),
  getById: (id: string) => apiService.get<any>(`/sessions/${id}`),
  create: (data: any) => apiService.post<any>('/sessions', data),
  update: (id: string, data: any) => apiService.put<any>(`/sessions/${id}`, data),
  delete: (id: string) => apiService.delete<any>(`/sessions/${id}`),
  replay: (id: string) => apiService.post<any>(`/sessions/${id}/replay`),
  export: (id: string, format: string) => apiService.get<any>(`/sessions/${id}/export`, { format }),
  import: (data: any) => apiService.post<any>('/sessions/import', data),
  getVisualization: (id: string) => apiService.get<any>(`/sessions/${id}/visualization`),
}

// API Testing API
export const apiTestingAPI = {
  execute: (request: any) => apiService.post<any>('/api-testing/execute', request),
  getHistory: () => apiService.get<{ history: any[] }>('/api-testing/history'),
  saveTemplate: (template: any) => apiService.post<any>('/api-testing/templates', template),
  getTemplates: () => apiService.get<any>('/api-testing/templates'),
  deleteTemplate: (id: string) => apiService.delete<any>(`/api-testing/templates/${id}`),
  getConfiguration: () => apiService.get<any>('/api-testing/configuration'),
  updateConfiguration: (config: any) => apiService.put<any>('/api-testing/configuration', config),
}

// Dashboard API
export const dashboardAPI = {
  getOverview: () => apiService.get<any>('/dashboard/overview'),
  getStats: () => apiService.get<any>('/dashboard/stats'),
  getActivity: () => apiService.get<any>('/dashboard/activity'),
  getMetrics: () => apiService.get<any>('/dashboard/metrics'),
  getRecentActivity: () => apiService.get<any>('/dashboard/recent-activity'),
}

// Statistics API
export const statsAPI = {
  getProjectStats: () => apiService.get<any>('/stats/projects'),
  getScanStats: () => apiService.get<any>('/stats/scans'),
  getFindingStats: () => apiService.get<any>('/stats/findings'),
  getInsightStats: () => apiService.get<any>('/stats/insights'),
  getReportStats: () => apiService.get<any>('/stats/reports'),
  getSessionStats: () => apiService.get<any>('/stats/sessions'),
  getOverallStats: () => apiService.get<any>('/stats/overall'),
}

// Export API
export const exportAPI = {
  exportProjects: (filters?: any) => apiService.get<any>('/export/projects', filters),
  exportScans: (filters?: any) => apiService.get<any>('/export/scans', filters),
  exportFindings: (filters?: any) => apiService.get<any>('/export/findings', filters),
  exportInsights: (filters?: any) => apiService.get<any>('/export/insights', filters),
  exportReports: (filters?: any) => apiService.get<any>('/export/reports', filters),
  exportSessions: (filters?: any) => apiService.get<any>('/export/sessions', filters),
  exportAll: (filters?: any) => apiService.get<any>('/export/all', filters),
}

// Configuration API
export const configAPI = {
  getSystemConfig: () => apiService.get<any>('/config/system'),
  updateSystemConfig: (config: any) => apiService.put<any>('/config/system', config),
  getUserConfig: () => apiService.get<any>('/config/user'),
  updateUserConfig: (config: any) => apiService.put<any>('/config/user', config),
  getScanConfig: () => apiService.get<any>('/config/scan'),
  updateScanConfig: (config: any) => apiService.put<any>('/config/scan', config),
  getSecurityConfig: () => apiService.get<any>('/config/security'),
  updateSecurityConfig: (config: any) => apiService.put<any>('/config/security', config),
}

// Learning & AI API
export const learningAPI = {
  getRecommendations: (context: any) => apiService.post<any>('/learning/recommendations', context),
  getBestPractices: () => apiService.get<any>('/learning/best-practices'),
  getTutorials: () => apiService.get<any>('/learning/tutorials'),
  getTutorial: (id: string) => apiService.get<any>(`/learning/tutorials/${id}`),
  submitFeedback: (data: any) => apiService.post<any>('/learning/feedback', data),
  getLearningPath: (userId: string) => apiService.get<any>(`/learning/paths/${userId}`),
  updateProgress: (userId: string, progress: any) => 
    apiService.patch<any>(`/learning/paths/${userId}/progress`, progress),
}

// Authentication API
export const authAPI = {
  login: (credentials: any) => apiService.post<any>('/auth/login', credentials),
  logout: () => apiService.post<any>('/auth/logout'),
  refresh: () => apiService.post<any>('/auth/refresh'),
  register: (userData: any) => apiService.post<any>('/auth/register', userData),
  forgotPassword: (email: string) => apiService.post<any>('/auth/forgot-password', { email }),
  resetPassword: (token: string, password: string) => 
    apiService.post<any>('/auth/reset-password', { token, password }),
  changePassword: (currentPassword: string, newPassword: string) => 
    apiService.post<any>('/auth/change-password', { currentPassword, newPassword }),
  getProfile: () => apiService.get<any>('/auth/profile'),
  updateProfile: (profile: any) => apiService.put<any>('/auth/profile', profile),
}

// File Upload API
export const uploadAPI = {
  uploadFile: (file: File, type: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    return apiService.post<any>('/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  uploadMultiple: (files: File[], type: string) => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    formData.append('type', type)
    return apiService.post<any>('/upload/multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  getUploadProgress: (uploadId: string) => apiService.get<any>(`/upload/progress/${uploadId}`),
  cancelUpload: (uploadId: string) => apiService.delete<any>(`/upload/${uploadId}`),
}

// WebSocket API (for real-time updates)
export const websocketAPI = {
  connect: (token?: string) => {
    // WebSocket connection logic would go here
    // This is a placeholder for the actual implementation
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws${token ? `?token=${token}` : ''}`
    return new WebSocket(url)
  },
  subscribe: (channel: string) => {
    // Subscription logic would go here
  },
  unsubscribe: (channel: string) => {
    // Unsubscription logic would go here
  },
}

// WebSocket connection helper function
export const createWebSocketConnection = (token?: string) => {
  return websocketAPI.connect(token)
}

// Utility functions
export const apiUtils = {
  handleError: (error: any) => {
    const message = error.response?.data?.message || error.message || 'An error occurred'
    toast.error(message)
    return Promise.reject(error)
  },
  
  downloadFile: (url: string, filename: string) => {
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  },
  
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },
  
  formatDuration: (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  },
}

export default api
