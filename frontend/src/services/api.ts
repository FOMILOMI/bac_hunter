import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { toast } from 'react-hot-toast'

// API Types
export interface ScanRequest {
  target: string
  mode: string
  max_rps: number
  phases: string[]
  identities_config?: Record<string, any>
  custom_plugins?: string[]
  timeout_seconds?: number
  max_concurrency?: number
  obey_robots?: boolean
  enable_ai?: boolean
}

export interface Target {
  id: number
  base_url: string
  name?: string
  description?: string
  status: string
  tags?: string[]
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface Scan {
  id: number
  target_id: number
  name: string
  mode: string
  status: string
  progress: number
  started_at?: string
  completed_at?: string
  configuration: Record<string, any>
  results_summary?: Record<string, any>
  error_message?: string
  created_at: string
  updated_at: string
  user_id?: string
}

export interface Finding {
  id: number
  target_id: number
  scan_id?: number
  type: string
  url: string
  evidence: string
  score: number
  severity: string
  status: string
  created_at: string
  updated_at: string
  metadata?: Record<string, any>
  false_positive: boolean
  notes?: string
}

export interface Identity {
  id: number
  name: string
  base_headers?: Record<string, string>
  cookies?: string
  auth_bearer?: string
  role?: string
  user_id?: string
  tenant_id?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Project {
  id: number
  name: string
  description?: string
  targets?: number[]
  configuration?: Record<string, any>
  created_at: string
  updated_at: string
  status: string
}

export interface Report {
  id: number
  name: string
  type: string
  content: string
  generated_at: string
  scan_id?: number
  target_id?: number
  user_id?: string
  metadata?: Record<string, any>
}

export interface AIModel {
  name: string
  status: string
  version: string
}

export interface AIAnalysisRequest {
  target_id: number
  analysis_type: string
  scan_id?: number
  custom_prompt?: string
}

export interface ScanLog {
  id: number
  scan_id: number
  level: string
  message: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  limit: number
  offset: number
}

export interface APIResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('api_token')
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
      localStorage.removeItem('api_token')
      window.location.href = '/login'
    }
    
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    toast.error(message)
    
    return Promise.reject(error)
  }
)

// API Service Class
export class APIService {
  // Health Check
  static async healthCheck(): Promise<any> {
    const response = await api.get('/health')
    return response.data
  }

  // Target Management
  static async listTargets(params?: {
    limit?: number
    offset?: number
    status?: string
    search?: string
  }): Promise<PaginatedResponse<Target>> {
    const response = await api.get('/api/targets', { params })
    return response.data
  }

  static async createTarget(target: Omit<Target, 'id' | 'created_at' | 'updated_at'>): Promise<{ id: number; message: string }> {
    const response = await api.post('/api/targets', target)
    return response.data
  }

  static async getTarget(targetId: number): Promise<Target> {
    const response = await api.get(`/api/targets/${targetId}`)
    return response.data
  }

  static async updateTarget(targetId: number, target: Partial<Target>): Promise<{ message: string }> {
    const response = await api.put(`/api/targets/${targetId}`, target)
    return response.data
  }

  static async deleteTarget(targetId: number): Promise<{ message: string }> {
    const response = await api.delete(`/api/targets/${targetId}`)
    return response.data
  }

  // Scan Management
  static async listScans(params?: {
    limit?: number
    offset?: number
    status?: string
    target_id?: number
  }): Promise<PaginatedResponse<Scan>> {
    const response = await api.get('/api/scans', { params })
    return response.data
  }

  static async createScan(scan: ScanRequest): Promise<{ scan_id: number; message: string; status: string }> {
    const response = await api.post('/api/scans', scan)
    return response.data
  }

  static async getScan(scanId: number): Promise<Scan> {
    const response = await api.get(`/api/scans/${scanId}`)
    return response.data
  }

  static async startScan(scanId: number): Promise<{ message: string }> {
    const response = await api.post(`/api/scans/${scanId}/start`)
    return response.data
  }

  static async stopScan(scanId: number): Promise<{ message: string }> {
    const response = await api.post(`/api/scans/${scanId}/stop`)
    return response.data
  }

  static async getScanProgress(scanId: number): Promise<{ scan_id: number; progress: number; status: string }> {
    const response = await api.get(`/api/scans/${scanId}/progress`)
    return response.data
  }

  static async getScanLogs(scanId: number, params?: {
    level?: string
    limit?: number
  }): Promise<{ logs: ScanLog[] }> {
    const response = await api.get(`/api/scans/${scanId}/logs`, { params })
    return response.data
  }

  // Findings Management
  static async listFindings(params?: {
    limit?: number
    offset?: number
    severity?: string
    status?: string
    target_id?: number
    scan_id?: number
  }): Promise<PaginatedResponse<Finding>> {
    const response = await api.get('/api/findings', { params })
    return response.data
  }

  static async getFinding(findingId: number): Promise<Finding> {
    const response = await api.get(`/api/findings/${findingId}`)
    return response.data
  }

  static async updateFinding(findingId: number, finding: Partial<Finding>): Promise<{ message: string }> {
    const response = await api.put(`/api/findings/${findingId}`, finding)
    return response.data
  }

  // Identity Management
  static async listIdentities(): Promise<Identity[]> {
    const response = await api.get('/api/identities')
    return response.data
  }

  static async createIdentity(identity: Omit<Identity, 'id' | 'created_at' | 'updated_at'>): Promise<{ id: number; message: string }> {
    const response = await api.post('/api/identities', identity)
    return response.data
  }

  static async updateIdentity(identityId: number, identity: Partial<Identity>): Promise<{ message: string }> {
    const response = await api.put(`/api/identities/${identityId}`, identity)
    return response.data
  }

  static async deleteIdentity(identityId: number): Promise<{ message: string }> {
    const response = await api.delete(`/api/identities/${identityId}`)
    return response.data
  }

  // Project Management
  static async listProjects(): Promise<Project[]> {
    const response = await api.get('/api/projects')
    return response.data
  }

  static async createProject(project: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<{ id: number; message: string }> {
    const response = await api.post('/api/projects', project)
    return response.data
  }

  static async getProject(projectId: number): Promise<Project> {
    const response = await api.get(`/api/projects/${projectId}`)
    return response.data
  }

  static async updateProject(projectId: number, project: Partial<Project>): Promise<{ message: string }> {
    const response = await api.put(`/api/projects/${projectId}`, project)
    return response.data
  }

  static async deleteProject(projectId: number): Promise<{ message: string }> {
    const response = await api.delete(`/api/projects/${projectId}`)
    return response.data
  }

  // Report Management
  static async listReports(params?: {
    limit?: number
    offset?: number
    type?: string
  }): Promise<PaginatedResponse<Report>> {
    const response = await api.get('/api/reports', { params })
    return response.data
  }

  static async generateReport(report: Omit<Report, 'id' | 'generated_at'>): Promise<{ report_id: string; message: string; status: string }> {
    const response = await api.post('/api/reports/generate', report)
    return response.data
  }

  static async downloadReport(reportId: string): Promise<Blob> {
    const response = await api.get(`/api/reports/${reportId}`, {
      responseType: 'blob'
    })
    return response.data
  }

  // AI and Intelligence
  static async listAIModels(): Promise<{ models: AIModel[] }> {
    const response = await api.get('/api/ai/models')
    return response.data
  }

  static async triggerAIAnalysis(request: AIAnalysisRequest): Promise<{ analysis_id: string; message: string; status: string }> {
    const response = await api.post('/api/ai/analyze', request)
    return response.data
  }

  static async getAIPredictions(params?: {
    target_id?: number
    model_name?: string
    limit?: number
  }): Promise<{ predictions: any[]; total: number }> {
    const response = await api.get('/api/ai/predictions', { params })
    return response.data
  }

  // CLI Integration
  static async cliScan(scanRequest: ScanRequest): Promise<{ message: string; scan_id: string; status: string }> {
    const response = await api.post('/api/cli/scan', scanRequest)
    return response.data
  }

  static async cliAudit(target: string, mode: string = 'standard'): Promise<{ message: string; audit_id: string; status: string }> {
    const response = await api.post('/api/cli/audit', { target, mode })
    return response.data
  }

  static async cliExploit(target: string, vulnerabilities: string[]): Promise<{ message: string; exploit_id: string; status: string }> {
    const response = await api.post('/api/cli/exploit', { target, vulnerabilities })
    return response.data
  }

  // Statistics
  static async getOverviewStats(): Promise<any> {
    const response = await api.get('/api/stats/overview')
    return response.data
  }

  static async getTargetStats(): Promise<{ targets: any[]; total: number }> {
    const response = await api.get('/api/stats/targets')
    return response.data
  }

  static async getFindingStats(): Promise<{ findings: any[]; total: number }> {
    const response = await api.get('/api/stats/findings')
    return response.data
  }

  // Session Management
  static async listSessions(): Promise<any[]> {
    const response = await api.get('/api/sessions')
    return response.data
  }

  static async createSession(session: any): Promise<{ id: number; message: string }> {
    const response = await api.post('/api/sessions', session)
    return response.data
  }

  static async getSession(sessionId: number): Promise<any> {
    const response = await api.get(`/api/sessions/${sessionId}`)
    return response.data
  }

  static async deleteSession(sessionId: number): Promise<{ message: string }> {
    const response = await api.delete(`/api/sessions/${sessionId}`)
    return response.data
  }

  // File Upload
  static async uploadFile(file: File, type: string): Promise<{ message: string; file_id: string }> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('type', type)
    
    const response = await api.post('/api/upload/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  static async uploadMultipleFiles(files: File[], type: string): Promise<{ message: string; file_ids: string[] }> {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`files`, file)
    })
    formData.append('type', type)
    
    const response = await api.post('/api/upload/multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // Export
  static async exportData(format: string, filters?: Record<string, any>): Promise<Blob> {
    const response = await api.get(`/api/export`, {
      params: { format, ...filters },
      responseType: 'blob'
    })
    return response.data
  }
}

// WebSocket Service
export class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(private url: string, private onMessage?: (data: any) => void) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)
        
        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (this.onMessage) {
              this.onMessage(data)
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
        
        this.ws.onclose = () => {
          console.log('WebSocket disconnected')
          this.attemptReconnect()
        }
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect().catch(console.error)
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('Max reconnection attempts reached')
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

// Create WebSocket instances
export const scanWebSocket = (scanId: number) => 
  new WebSocketService(`${WS_BASE_URL}/ws/scans/${scanId}`)

export const systemWebSocket = () => 
  new WebSocketService(`${WS_BASE_URL}/ws/system`)

export default APIService
