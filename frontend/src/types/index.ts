// Core types for BAC Hunter application

export interface Project {
  id: string
  name: string
  description: string
  target_url: string
  status: 'created' | 'scanning' | 'completed' | 'failed' | 'paused'
  scan_config: ScanConfig
  created_at: string
  updated_at?: string
  scan_count: number
  finding_count: number
  ai_insights_count?: number
  last_scan_at?: string
  tags?: string[]
}

export interface ScanConfig {
  scan_type: 'quick' | 'comprehensive' | 'stealth' | 'aggressive' | 'custom'
  ai_enabled: boolean
  rl_optimization: boolean
  max_rps: number
  timeout: number
  phases: ScanPhase[]
  authentication?: AuthConfig
  custom_headers?: Record<string, string>
  proxy?: ProxyConfig
}

export interface AuthConfig {
  type: 'none' | 'basic' | 'bearer' | 'cookie' | 'custom'
  credentials?: {
    username?: string
    password?: string
    token?: string
    cookie?: string
    headers?: Record<string, string>
  }
}

export interface ProxyConfig {
  enabled: boolean
  host: string
  port: number
  username?: string
  password?: string
}

export type ScanPhase = 'recon' | 'access' | 'audit' | 'exploit' | 'report'

export interface Scan {
  id: string
  project_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  current_phase?: ScanPhase
  started_at: string
  completed_at?: string
  duration?: number
  findings_count: number
  errors_count: number
  config: ScanConfig
  metrics: ScanMetrics
}

export interface ScanMetrics {
  total_requests: number
  successful_requests: number
  failed_requests: number
  average_response_time: number
  endpoints_discovered: number
  parameters_tested: number
  payloads_executed: number
}

export interface Finding {
  id: string
  project_id: string
  scan_id: string
  type: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  confidence: number
  url: string
  method: string
  parameter?: string
  payload?: string
  request: HTTPRequest
  response: HTTPResponse
  evidence: Evidence[]
  remediation: string
  references: string[]
  status: 'new' | 'confirmed' | 'false_positive' | 'resolved' | 'ignored'
  created_at: string
  updated_at?: string
  tags?: string[]
}

export interface HTTPRequest {
  method: string
  url: string
  headers: Record<string, string>
  body?: string
  timestamp: string
}

export interface HTTPResponse {
  status_code: number
  headers: Record<string, string>
  body: string
  size: number
  response_time: number
  timestamp: string
}

export interface Evidence {
  type: 'request' | 'response' | 'screenshot' | 'log' | 'diff'
  title: string
  content: string
  metadata?: Record<string, any>
}

export interface AIInsight {
  id: string
  project_id?: string
  scan_id?: string
  finding_id?: string
  type: 'recommendation' | 'anomaly' | 'pattern' | 'prediction' | 'optimization'
  title: string
  description: string
  confidence: number
  priority: 'low' | 'medium' | 'high' | 'critical'
  category: string
  data: Record<string, any>
  action_items: string[]
  created_at: string
  status: 'new' | 'reviewed' | 'implemented' | 'dismissed'
}

export interface Recommendation {
  id: string
  title: string
  description: string
  type: 'security' | 'performance' | 'configuration' | 'methodology'
  priority: 'low' | 'medium' | 'high' | 'critical'
  confidence: number
  action_items: string[]
  estimated_effort: string
  risk_level: string
  references?: string[]
}

export interface Target {
  id: string
  base_url: string
  finding_count: number
  last_scan_at?: string
  status: 'active' | 'inactive'
  metadata?: Record<string, any>
}

export interface Session {
  id: string
  name: string
  target_url: string
  requests: SessionRequest[]
  created_at: string
  updated_at?: string
  status: 'active' | 'archived'
  metadata?: Record<string, any>
}

export interface SessionRequest {
  id: string
  method: string
  url: string
  headers: Record<string, string>
  body?: string
  response?: HTTPResponse
  timestamp: string
  tags?: string[]
}

export interface Endpoint {
  url: string
  method: string
  parameters: Parameter[]
  status_codes: number[]
  response_types: string[]
  authentication_required: boolean
  rate_limited: boolean
  discovered_at: string
  last_tested_at?: string
}

export interface Parameter {
  name: string
  type: 'query' | 'body' | 'header' | 'path' | 'cookie'
  data_type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  required: boolean
  default_value?: string
  examples?: string[]
  vulnerable: boolean
  tested_payloads: string[]
}

export interface Vulnerability {
  cve_id?: string
  cwe_id?: string
  name: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  impact: string
  remediation: string
  references: string[]
}

export interface Report {
  id: string
  project_id: string
  name: string
  type: 'executive' | 'technical' | 'compliance' | 'custom'
  format: 'html' | 'pdf' | 'json' | 'csv' | 'xml'
  template: string
  config: ReportConfig
  generated_at: string
  file_path?: string
  size?: number
  status: 'generating' | 'completed' | 'failed'
}

export interface ReportConfig {
  include_executive_summary: boolean
  include_methodology: boolean
  include_findings: boolean
  include_recommendations: boolean
  include_appendices: boolean
  finding_filters: FindingFilter[]
  custom_sections: CustomSection[]
}

export interface FindingFilter {
  field: keyof Finding
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'in'
  value: any
}

export interface CustomSection {
  title: string
  content: string
  position: number
}

export interface DashboardStats {
  total_projects: number
  active_scans: number
  total_findings: number
  critical_findings: number
  high_findings: number
  medium_findings: number
  low_findings: number
  ai_insights_count: number
  recent_activity: ActivityItem[]
  scan_success_rate: number
  average_scan_duration: number
}

export interface ActivityItem {
  id: string
  type: 'scan_started' | 'scan_completed' | 'finding_discovered' | 'project_created' | 'ai_insight_generated'
  title: string
  description: string
  timestamp: string
  project_id?: string
  scan_id?: string
  finding_id?: string
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface APIError {
  message: string
  code?: string
  details?: Record<string, any>
}

export interface PaginationParams {
  page: number
  limit: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

export interface FilterParams {
  search?: string
  status?: string[]
  severity?: string[]
  type?: string[]
  date_from?: string
  date_to?: string
  project_id?: string
  scan_id?: string
}

// Chart and visualization types
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
  fill?: boolean
}

export interface NetworkGraphNode {
  id: string
  label: string
  group: string
  size: number
  color?: string
  x?: number
  y?: number
}

export interface NetworkGraphEdge {
  from: string
  to: string
  label?: string
  width?: number
  color?: string
}

export interface HeatmapData {
  x: string[]
  y: string[]
  z: number[][]
}

// Configuration types
export interface AppConfig {
  api_base_url: string
  websocket_url: string
  max_file_size: number
  supported_formats: string[]
  default_scan_config: ScanConfig
  ui_preferences: UIPreferences
}

export interface UIPreferences {
  theme: 'dark' | 'light' | 'auto'
  sidebar_collapsed: boolean
  default_page_size: number
  auto_refresh_interval: number
  show_tooltips: boolean
  compact_mode: boolean
}
