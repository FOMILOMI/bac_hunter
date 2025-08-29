import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { toast } from 'react-hot-toast'

// Types
export interface ScanRequest {
  target: string
  mode?: string
  max_rps?: number
  phases?: string[]
  identities_config?: Record<string, any>
  custom_plugins?: string[]
  timeout_minutes?: number
  obey_robots?: boolean
  enable_ai?: boolean
}

export interface TargetRequest {
  base_url: string
  name?: string
  description?: string
  tags?: string[]
  metadata?: Record<string, any>
}

export interface IdentityRequest {
  name: string
  base_headers?: Record<string, string>
  cookie?: string
  auth_bearer?: string
  role?: string
  user_id?: string
  tenant_id?: string
}

export interface FindingUpdateRequest {
  status?: string
  false_positive?: boolean
  notes?: string
  severity?: string
}

export interface AIAnalysisRequest {
  target_url: string
  context?: Record<string, any>
  analysis_type?: string
}

// API Response types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: string
}

export interface PaginatedResponse<T = any> {
  data: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// Error types
export interface ApiError {
  message: string
  status: number
  details?: any
}

// Configuration
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
}

// Create axios instance
const axiosInstance: AxiosInstance = axios.create(API_CONFIG)

// Request interceptor for authentication
axiosInstance.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add request ID for tracking
    config.headers['X-Request-ID'] = generateRequestId()
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - redirect to login
          handleUnauthorized()
          break
        case 403:
          // Forbidden
          toast.error('Access denied. You do not have permission to perform this action.')
          break
        case 404:
          // Not found
          toast.error('The requested resource was not found.')
          break
        case 429:
          // Rate limited
          toast.error('Too many requests. Please wait before trying again.')
          break
        case 500:
          // Internal server error
          toast.error('An internal server error occurred. Please try again later.')
          break
        default:
          // Other errors
          const errorMessage = data?.detail || data?.message || 'An error occurred'
          toast.error(errorMessage)
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection and try again.')
    } else {
      // Other error
      toast.error('An unexpected error occurred.')
    }
    
    return Promise.reject(error)
  }
)

// Utility functions
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

function handleUnauthorized(): void {
  // Clear stored authentication
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_info')
  
  // Redirect to login page
  window.location.href = '/login'
}

// API class
class APIService {
  private client: AxiosInstance

  constructor() {
    this.client = axiosInstance
  }

  // Generic request methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config)
    return response.data
  }

  // Authentication
  async login(credentials: { username: string; password: string }): Promise<{ token: string; user: any }> {
    const response = await this.post<{ token: string; user: any }>('/api/auth/login', credentials)
    
    // Store authentication data
    localStorage.setItem('auth_token', response.token)
    localStorage.setItem('user_info', JSON.stringify(response.user))
    
    return response
  }

  async logout(): Promise<void> {
    try {
      await this.post('/api/auth/logout')
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error)
    } finally {
      // Clear stored authentication
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
    }
  }

  async refreshToken(): Promise<{ token: string }> {
    const response = await this.post<{ token: string }>('/api/auth/refresh')
    
    // Update stored token
    localStorage.setItem('auth_token', response.token)
    
    return response
  }

  // Dashboard & Statistics
  async getOverviewStats(): Promise<any> {
    return this.get('/api/stats/overview')
  }

  async getSystemStatus(): Promise<any> {
    return this.get('/api/system/status')
  }

  // Target Management
  async getTargets(params?: {
    status?: string
    tags?: string[]
    risk_score_min?: number
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const queryParams = new URLSearchParams()
    
    if (params?.status) queryParams.append('status', params.status)
    if (params?.tags) params.tags.forEach(tag => queryParams.append('tags', tag))
    if (params?.risk_score_min !== undefined) queryParams.append('risk_score_min', params.risk_score_min.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    
    const url = `/api/targets${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.get(url)
  }

  async createTarget(target: TargetRequest): Promise<any> {
    return this.post('/api/targets', target)
  }

  async updateTarget(targetId: number, target: Partial<TargetRequest>): Promise<any> {
    return this.put(`/api/targets/${targetId}`, target)
  }

  async deleteTarget(targetId: number): Promise<any> {
    return this.delete(`/api/targets/${targetId}`)
  }

  // Scan Management
  async getScans(params?: {
    status?: string
    target_id?: number
    created_by?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const queryParams = new URLSearchParams()
    
    if (params?.status) queryParams.append('status', params.status)
    if (params?.target_id) queryParams.append('target_id', params.target_id.toString())
    if (params?.created_by) queryParams.append('created_by', params.created_by)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    
    const url = `/api/scans${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.get(url)
  }

  async getScan(scanId: string): Promise<any> {
    return this.get(`/api/scans/${scanId}`)
  }

  async createScan(scan: ScanRequest): Promise<any> {
    return this.post('/api/scans', scan)
  }

  async pauseScan(scanId: string): Promise<any> {
    return this.post(`/api/scans/${scanId}/pause`)
  }

  async resumeScan(scanId: string): Promise<any> {
    return this.post(`/api/scans/${scanId}/resume`)
  }

  async deleteScan(scanId: string): Promise<any> {
    return this.delete(`/api/scans/${scanId}`)
  }

  async getScanProgress(scanId: string): Promise<any> {
    return this.get(`/api/scans/${scanId}/progress`)
  }

  async getScanLogs(scanId: string): Promise<any[]> {
    return this.get(`/api/scans/${scanId}/logs`)
  }

  // Findings Management
  async getFindings(params?: {
    target_id?: number
    severity?: string
    status?: string
    scan_id?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const queryParams = new URLSearchParams()
    
    if (params?.target_id) queryParams.append('target_id', params.target_id.toString())
    if (params?.severity) queryParams.append('severity', params.severity)
    if (params?.status) queryParams.append('status', params.status)
    if (params?.scan_id) queryParams.append('scan_id', params.scan_id)
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.offset) queryParams.append('offset', params.offset.toString())
    
    const url = `/api/findings${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.get(url)
  }

  async getFinding(findingId: number): Promise<any> {
    return this.get(`/api/findings/${findingId}`)
  }

  async updateFinding(findingId: number, update: FindingUpdateRequest): Promise<any> {
    return this.put(`/api/findings/${findingId}`, update)
  }

  async exportFindings(format: string, targetId?: number): Promise<any> {
    const params = new URLSearchParams({ format })
    if (targetId) params.append('target_id', targetId.toString())
    
    return this.post(`/api/findings/export?${params.toString()}`)
  }

  // Identity & Session Management
  async getIdentities(): Promise<any[]> {
    return this.get('/api/identities')
  }

  async createIdentity(identity: IdentityRequest): Promise<any> {
    return this.post('/api/identities', identity)
  }

  async getSessions(targetId?: number): Promise<any[]> {
    const url = targetId ? `/api/sessions?target_id=${targetId}` : '/api/sessions'
    return this.get(url)
  }

  async refreshSessions(targetId?: number): Promise<any> {
    const data = targetId ? { target_id: targetId } : {}
    return this.post('/api/sessions/refresh', data)
  }

  // AI & Intelligence
  async getAIModels(): Promise<any> {
    return this.get('/api/ai/models')
  }

  async triggerAIAnalysis(request: AIAnalysisRequest): Promise<any> {
    return this.post('/api/ai/analyze', request)
  }

  async getAIPredictions(targetUrl?: string, limit?: number): Promise<any[]> {
    const params = new URLSearchParams()
    if (targetUrl) params.append('target_url', targetUrl)
    if (limit) params.append('limit', limit.toString())
    
    const url = `/api/ai/predictions${params.toString() ? `?${params.toString()}` : ''}`
    return this.get(url)
  }

  // Plugin Management
  async getPlugins(): Promise<any[]> {
    return this.get('/api/plugins')
  }

  async configurePlugin(pluginName: string, config: Record<string, any>): Promise<any> {
    return this.post(`/api/plugins/${pluginName}/config`, config)
  }

  // Reporting
  async getReports(): Promise<any[]> {
    return this.get('/api/reports')
  }

  async generateReport(scanId: string, format?: string, template?: string): Promise<any> {
    const data: any = { scan_id: scanId }
    if (format) data.format = format
    if (template) data.template = template
    
    return this.post('/api/reports/generate', data)
  }

  async downloadReport(reportId: string): Promise<any> {
    return this.get(`/api/reports/${reportId}`)
  }

  // File Upload
  async uploadFile(file: File, type: string): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    
    return this.post('/api/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  async uploadMultipleFiles(files: File[], type: string): Promise<any> {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`files[${index}]`, file)
    })
    formData.append('type', type)
    
    return this.post('/api/upload/multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  }

  // System Operations
  async refreshSystem(): Promise<any> {
    return this.post('/api/system/refresh')
  }

  async getHealthCheck(): Promise<any> {
    return this.get('/health')
  }

  // CLI Integration (for backward compatibility)
  async executeCLICommand(command: string, args: string[]): Promise<any> {
    return this.post('/api/cli/execute', { command, args })
  }

  // WebSocket connection helper
  getWebSocketUrl(endpoint: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}${endpoint}`
  }

  // Utility methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token')
  }

  getAuthToken(): string | null {
    return localStorage.getItem('auth_token')
  }

  getUserInfo(): any | null {
    const userInfo = localStorage.getItem('user_info')
    return userInfo ? JSON.parse(userInfo) : null
  }

  // Error handling utilities
  handleError(error: any): ApiError {
    if (axios.isAxiosError(error)) {
      return {
        message: error.response?.data?.detail || error.response?.data?.message || error.message,
        status: error.response?.status || 0,
        details: error.response?.data
      }
    }
    
    return {
      message: error.message || 'An unknown error occurred',
      status: 0,
      details: error
    }
  }
}

// Create and export singleton instance
export const api = new APIService()

// Export types for use in components
export type {
  ScanRequest,
  TargetRequest,
  IdentityRequest,
  FindingUpdateRequest,
  AIAnalysisRequest,
  ApiResponse,
  PaginatedResponse,
  ApiError
}
