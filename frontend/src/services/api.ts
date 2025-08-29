import axios, { AxiosResponse } from 'axios'
import toast from 'react-hot-toast'
import {
  Project,
  Scan,
  Finding,
  AIInsight,
  Target,
  Session,
  Report,
  DashboardStats,
  PaginatedResponse,
  FilterParams,
  PaginationParams,
  Recommendation,
  ScanConfig,
  APIError,
} from '../types'

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for loading states
api.interceptors.request.use((config) => {
  // Add loading indicator if needed
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || 'An error occurred'
    
    // Don't show toast for certain endpoints
    const silentEndpoints = ['/health', '/ws']
    const isSilent = silentEndpoints.some(endpoint => 
      error.config?.url?.includes(endpoint)
    )
    
    if (!isSilent) {
      toast.error(message)
    }
    
    return Promise.reject(error)
  }
)

// Helper function to handle API responses
const handleResponse = <T>(response: AxiosResponse<T>): T => response.data

// Dashboard API
export const dashboardAPI = {
  getStats: (): Promise<DashboardStats> =>
    api.get('/v2/stats').then(handleResponse),
  
  getActivity: (): Promise<any[]> =>
    api.get('/v2/activity').then(handleResponse),
}

// Projects API
export const projectsAPI = {
  getAll: (): Promise<{ projects: Project[] }> =>
    api.get('/projects').then(handleResponse),
  
  getById: (id: string): Promise<{ project: Project }> =>
    api.get(`/projects/${id}`).then(handleResponse),
  
  create: (data: Partial<Project>): Promise<{ project_id: string }> =>
    api.post('/projects', data).then(handleResponse),
  
  update: (id: string, data: Partial<Project>): Promise<{ project: Project }> =>
    api.put(`/projects/${id}`, data).then(handleResponse),
  
  delete: (id: string): Promise<void> =>
    api.delete(`/projects/${id}`).then(handleResponse),
  
  getVisualizations: (id: string, type: string): Promise<any> =>
    api.get(`/projects/${id}/visualizations?visualization_type=${type}`).then(handleResponse),
  
  getRecommendations: (id: string): Promise<{ recommendations: Recommendation[] }> =>
    api.get(`/projects/${id}/recommendations`).then(handleResponse),
}

// Scans API
export const scansAPI = {
  getAll: (params?: FilterParams & PaginationParams): Promise<PaginatedResponse<Scan>> =>
    api.get('/scans', { params }).then(handleResponse),
  
  getById: (id: string): Promise<{ scan: Scan }> =>
    api.get(`/scans/${id}`).then(handleResponse),
  
  create: (projectId: string, config: ScanConfig): Promise<{ scan_id: string }> =>
    api.post(`/projects/${projectId}/scans`, config).then(handleResponse),
  
  start: (id: string): Promise<void> =>
    api.post(`/scans/${id}/start`).then(handleResponse),
  
  pause: (id: string): Promise<void> =>
    api.post(`/scans/${id}/pause`).then(handleResponse),
  
  resume: (id: string): Promise<void> =>
    api.post(`/scans/${id}/resume`).then(handleResponse),
  
  cancel: (id: string): Promise<void> =>
    api.post(`/scans/${id}/cancel`).then(handleResponse),
  
  delete: (id: string): Promise<void> =>
    api.delete(`/scans/${id}`).then(handleResponse),
  
  getLogs: (id: string): Promise<{ logs: string[] }> =>
    api.get(`/scans/${id}/logs`).then(handleResponse),
  
  getMetrics: (id: string): Promise<any> =>
    api.get(`/scans/${id}/metrics`).then(handleResponse),
}

// Findings API
export const findingsAPI = {
  getAll: (params?: FilterParams & PaginationParams): Promise<PaginatedResponse<Finding>> =>
    api.get('/v2/findings', { params }).then(handleResponse),
  
  getById: (id: string): Promise<{ finding: Finding }> =>
    api.get(`/findings/${id}`).then(handleResponse),
  
  updateStatus: (id: string, status: Finding['status']): Promise<{ finding: Finding }> =>
    api.patch(`/findings/${id}`, { status }).then(handleResponse),
  
  addComment: (id: string, comment: string): Promise<void> =>
    api.post(`/findings/${id}/comments`, { comment }).then(handleResponse),
  
  export: (format: string, ids?: string[]): Promise<Blob> =>
    api.post(`/findings/export`, { format, ids }, { responseType: 'blob' }).then(handleResponse),
  
  bulkUpdate: (ids: string[], updates: Partial<Finding>): Promise<void> =>
    api.patch('/findings/bulk', { ids, updates }).then(handleResponse),
}

// AI Insights API
export const aiAPI = {
  getInsights: (params?: FilterParams & PaginationParams): Promise<PaginatedResponse<AIInsight>> =>
    api.get('/ai/insights', { params }).then(handleResponse),
  
  getRecommendations: (targetUrl: string): Promise<{ recommendations: Recommendation[] }> =>
    api.get(`/v2/recommendations/${encodeURIComponent(targetUrl)}`).then(handleResponse),
  
  analyzeRequest: (data: any): Promise<any> =>
    api.post('/ai/analyze/request', data).then(handleResponse),
  
  analyzeResponse: (data: any): Promise<any> =>
    api.post('/ai/analyze/response', data).then(handleResponse),
  
  generateExplanation: (findingId: string): Promise<{ explanation: string }> =>
    api.post(`/ai/explain/${findingId}`).then(handleResponse),
  
  getConcepts: (): Promise<{ concepts: any[] }> =>
    api.get('/v2/learning/concepts').then(handleResponse),
  
  explainConcept: (concept: string, level: string = 'basic'): Promise<any> =>
    api.get(`/v2/learning/explain/${concept}?level=${level}`).then(handleResponse),
}

// Targets API
export const targetsAPI = {
  getAll: (): Promise<{ targets: Target[] }> =>
    api.get('/targets').then(handleResponse),
  
  getById: (id: string): Promise<{ target: Target }> =>
    api.get(`/targets/${id}`).then(handleResponse),
  
  create: (url: string): Promise<{ target_id: string }> =>
    api.post('/targets', { url }).then(handleResponse),
  
  delete: (id: string): Promise<void> =>
    api.delete(`/targets/${id}`).then(handleResponse),
}

// Sessions API
export const sessionsAPI = {
  getAll: (): Promise<{ sessions: Session[] }> =>
    api.get('/sessions').then(handleResponse),
  
  getById: (id: string): Promise<{ session: Session }> =>
    api.get(`/sessions/${id}`).then(handleResponse),
  
  create: (data: Partial<Session>): Promise<{ session_id: string }> =>
    api.post('/sessions', data).then(handleResponse),
  
  update: (id: string, data: Partial<Session>): Promise<{ session: Session }> =>
    api.put(`/sessions/${id}`, data).then(handleResponse),
  
  delete: (id: string): Promise<void> =>
    api.delete(`/sessions/${id}`).then(handleResponse),
  
  importHAR: (file: File): Promise<{ session_id: string }> => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/sessions/import/har', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(handleResponse)
  },
  
  export: (id: string, format: string): Promise<Blob> =>
    api.get(`/sessions/${id}/export?format=${format}`, { responseType: 'blob' }).then(handleResponse),
}

// Reports API
export const reportsAPI = {
  getAll: (): Promise<{ reports: Report[] }> =>
    api.get('/reports').then(handleResponse),
  
  getById: (id: string): Promise<{ report: Report }> =>
    api.get(`/reports/${id}`).then(handleResponse),
  
  create: (data: Partial<Report>): Promise<{ report_id: string }> =>
    api.post('/reports', data).then(handleResponse),
  
  generate: (id: string): Promise<void> =>
    api.post(`/reports/${id}/generate`).then(handleResponse),
  
  download: (id: string): Promise<Blob> =>
    api.get(`/reports/${id}/download`, { responseType: 'blob' }).then(handleResponse),
  
  delete: (id: string): Promise<void> =>
    api.delete(`/reports/${id}`).then(handleResponse),
  
  getTemplates: (): Promise<{ templates: any[] }> =>
    api.get('/reports/templates').then(handleResponse),
}

// Export API
export const exportAPI = {
  exportData: (format: string, options?: any): Promise<Blob> =>
    api.post(`/v2/export/${format}`, options, { responseType: 'blob' }).then(handleResponse),
  
  exportFindings: (format: string, filters?: FilterParams): Promise<Blob> =>
    api.post(`/export/findings/${format}`, filters, { responseType: 'blob' }).then(handleResponse),
  
  exportProject: (projectId: string, format: string): Promise<Blob> =>
    api.get(`/projects/${projectId}/export?format=${format}`, { responseType: 'blob' }).then(handleResponse),
}

// Configuration API
export const configAPI = {
  generateConfiguration: (data: any): Promise<any> =>
    api.post('/v2/configuration/generate', data).then(handleResponse),
  
  getProfiles: (): Promise<{ profiles: any[] }> =>
    api.get('/configuration/profiles').then(handleResponse),
  
  saveProfile: (profile: any): Promise<{ profile_id: string }> =>
    api.post('/configuration/profiles', profile).then(handleResponse),
}

// Health check
export const healthAPI = {
  check: (): Promise<{ status: string; timestamp: string }> =>
    api.get('/health').then(handleResponse),
}

// WebSocket connection helper
export const createWebSocketConnection = (url: string = '/ws') => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}${url}`
  return new WebSocket(wsUrl)
}

export default api
