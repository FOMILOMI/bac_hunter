// Base types
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// Project types
export interface Project extends BaseEntity {
  name: string
  description?: string
  status: 'active' | 'inactive' | 'archived'
  target_urls: string[]
  scan_config: ScanConfig
  findings_count?: number
  scans_count?: number
  last_scan_date?: string
  tags?: string[]
  metadata?: Record<string, any>
}

export interface ScanConfig {
  scan_type: 'full' | 'quick' | 'custom'
  target_scope: 'domain' | 'subdomain' | 'path' | 'custom'
  authentication?: AuthenticationConfig
  rate_limiting?: RateLimitingConfig
  custom_headers?: Record<string, string>
  proxy_settings?: ProxyConfig
  scan_depth: number
  max_threads: number
  timeout: number
  follow_redirects: boolean
  verify_ssl: boolean
}

export interface AuthenticationConfig {
  type: 'none' | 'basic' | 'bearer' | 'cookie' | 'form'
  username?: string
  password?: string
  token?: string
  cookie_data?: Record<string, string>
  form_data?: Record<string, string>
}

export interface RateLimitingConfig {
  requests_per_second: number
  delay_between_requests: number
  burst_limit: number
}

export interface ProxyConfig {
  enabled: boolean
  host: string
  port: number
  username?: string
  password?: string
  type: 'http' | 'https' | 'socks4' | 'socks5'
}

// Scan types
export interface Scan extends BaseEntity {
  project_id: string
  name: string
  description?: string
  status: 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  scan_type: string
  target_urls: string[]
  progress: number
  current_phase: string
  phases: ScanPhase[]
  findings_count: number
  duration: number
  requests_per_second: number
  total_requests: number
  completed_requests: number
  start_time: string
  end_time?: string
  error_message?: string
  scan_config: ScanConfig
  metadata?: Record<string, any>
}

export interface ScanPhase {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  start_time?: string
  end_time?: string
  description: string
  findings_count: number
}

// Finding types
export interface Finding extends BaseEntity {
  project_id: string
  scan_id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'open' | 'in_progress' | 'resolved' | 'false_positive' | 'duplicate'
  type: string
  cvss_score?: number
  cvss_vector?: string
  url: string
  parameter?: string
  evidence: string
  request_data?: RequestData
  response_data?: ResponseData
  remediation: string
  references?: string[]
  tags?: string[]
  metadata?: Record<string, any>
}

export interface RequestData {
  method: string
  url: string
  headers: Record<string, string>
  body?: string
  parameters?: Record<string, string>
}

export interface ResponseData {
  status_code: number
  headers: Record<string, string>
  body?: string
  response_time: number
}

// AI Insight types
export interface AIInsight extends BaseEntity {
  project_id?: string
  scan_id?: string
  title: string
  description: string
  category: 'security' | 'performance' | 'compliance' | 'best_practices' | 'optimization'
  confidence: number
  recommendation: string
  impact: 'high' | 'medium' | 'low'
  priority: 'urgent' | 'high' | 'medium' | 'low'
  feedback?: InsightFeedback
  related_findings?: string[]
  tags?: string[]
  metadata?: Record<string, any>
}

export interface InsightFeedback {
  rating: number
  comment?: string
  helpful: boolean
  submitted_at: string
  user_id?: string
}

// Report types
export interface Report extends BaseEntity {
  project_id?: string
  scan_id?: string
  title: string
  description?: string
  type: 'executive' | 'technical' | 'compliance' | 'detailed' | 'custom'
  status: 'draft' | 'generating' | 'completed' | 'failed' | 'scheduled'
  format: 'pdf' | 'html' | 'json' | 'csv'
  content: ReportContent
  template_id?: string
  scheduled_at?: string
  generated_at?: string
  file_size?: number
  download_url?: string
  metadata?: Record<string, any>
}

export interface ReportContent {
  summary: ReportSummary
  findings: Finding[]
  insights: AIInsight[]
  scans: Scan[]
  recommendations: string[]
  charts: ReportChart[]
  metadata: Record<string, any>
}

export interface ReportSummary {
  total_findings: number
  critical_findings: number
  high_findings: number
  medium_findings: number
  low_findings: number
  scan_duration: number
  target_urls: string[]
  scan_date: string
}

export interface ReportChart {
  type: 'pie' | 'bar' | 'line' | 'radar'
  title: string
  data: any
  options?: any
}

// Session types
export interface Session extends BaseEntity {
  project_id?: string
  scan_id?: string
  name: string
  description?: string
  type: 'http' | 'https' | 'websocket' | 'api' | 'custom'
  status: 'active' | 'inactive' | 'expired' | 'suspended'
  requests: SessionRequest[]
  metadata: SessionMetadata
  tags?: string[]
}

export interface SessionRequest {
  id: string
  timestamp: string
  method: string
  url: string
  headers: Record<string, string>
  body?: string
  response_status?: number
  response_headers?: Record<string, string>
  response_body?: string
  response_time?: number
  size?: number
}

export interface SessionMetadata {
  total_requests: number
  unique_urls: number
  methods_used: string[]
  status_codes: Record<number, number>
  average_response_time: number
  total_size: number
  start_time: string
  end_time?: string
}

// API Testing types
export interface APIRequest {
  id?: string
  name?: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS'
  url: string
  headers: Record<string, string>
  body?: string
  params?: Record<string, string>
  auth?: AuthenticationConfig
  timeout?: number
  follow_redirects?: boolean
  verify_ssl?: boolean
  metadata?: Record<string, any>
}

export interface APIResponse {
  id?: string
  request_id?: string
  status_code: number
  status_text: string
  headers: Record<string, string>
  body: string
  response_time: number
  size: number
  timestamp: string
  error?: string
  metadata?: Record<string, any>
}

// Dashboard types
export interface DashboardData {
  projects: Project[]
  scans: Scan[]
  findings: Finding[]
  insights: AIInsight[]
  reports: Report[]
  sessions: Session[]
  metrics: DashboardMetrics
  recentActivity: ActivityItem[]
}

export interface DashboardMetrics {
  total_projects: number
  active_scans: number
  total_findings: number
  critical_findings: number
  high_findings: number
  medium_findings: number
  low_findings: number
  ai_insights_count: number
  scan_success_rate: number
  average_scan_duration: number
  total_reports: number
  active_sessions: number
}

export interface ActivityItem {
  id: string
  type: 'project_created' | 'scan_started' | 'scan_completed' | 'finding_discovered' | 'insight_generated' | 'report_created'
  title: string
  description: string
  timestamp: string
  user_id?: string
  entity_id?: string
  entity_type?: string
  metadata?: Record<string, any>
}

// User types
export interface User extends BaseEntity {
  username: string
  email: string
  first_name?: string
  last_name?: string
  role: 'admin' | 'user' | 'viewer'
  status: 'active' | 'inactive' | 'suspended'
  preferences: UserPreferences
  last_login?: string
  permissions: string[]
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  timezone: string
  notifications: NotificationSettings
  dashboard_layout?: any
}

export interface NotificationSettings {
  email: boolean
  push: boolean
  critical_findings: boolean
  scan_completion: boolean
  system_alerts: boolean
}

// Template types
export interface Template extends BaseEntity {
  name: string
  description?: string
  type: 'scan' | 'report' | 'session' | 'api_request'
  content: any
  category: string
  tags?: string[]
  is_default: boolean
  metadata?: Record<string, any>
}

// Export types
export interface ExportOptions {
  format: 'json' | 'csv' | 'xml' | 'pdf' | 'html'
  include_metadata?: boolean
  include_attachments?: boolean
  filters?: Record<string, any>
  date_range?: {
    start: string
    end: string
  }
}

// Configuration types
export interface SystemConfig {
  scan_settings: ScanSystemConfig
  security_settings: SecurityConfig
  performance_settings: PerformanceConfig
  notification_settings: NotificationConfig
}

export interface ScanSystemConfig {
  default_timeout: number
  max_concurrent_scans: number
  default_rate_limit: number
  max_scan_duration: number
  allowed_scan_types: string[]
}

export interface SecurityConfig {
  require_authentication: boolean
  session_timeout: number
  max_login_attempts: number
  password_policy: PasswordPolicy
  ip_whitelist?: string[]
}

export interface PasswordPolicy {
  min_length: number
  require_uppercase: boolean
  require_lowercase: boolean
  require_numbers: boolean
  require_special_chars: boolean
  max_age_days: number
}

export interface PerformanceConfig {
  max_memory_usage: number
  max_cpu_usage: number
  database_connection_limit: number
  cache_enabled: boolean
  cache_ttl: number
}

export interface NotificationConfig {
  smtp_enabled: boolean
  smtp_host?: string
  smtp_port?: number
  smtp_username?: string
  smtp_password?: string
  webhook_urls?: string[]
}

// Learning types
export interface Tutorial extends BaseEntity {
  title: string
  description: string
  content: string
  category: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  duration_minutes: number
  prerequisites?: string[]
  tags?: string[]
  is_published: boolean
}

export interface LearningPath extends BaseEntity {
  user_id: string
  name: string
  description: string
  tutorials: string[]
  progress: LearningProgress
  estimated_completion: string
  is_active: boolean
}

export interface LearningProgress {
  completed_tutorials: string[]
  current_tutorial?: string
  total_progress: number
  last_activity: string
  achievements: string[]
}

// Error types
export interface APIError {
  message: string
  code: string
  details?: any
  timestamp: string
  request_id?: string
}

// Pagination types
export interface PaginationParams {
  page: number
  page_size: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

// Filter types
export interface FilterOptions {
  search?: string
  status?: string[]
  type?: string[]
  severity?: string[]
  category?: string[]
  date_range?: {
    start: string
    end: string
  }
  tags?: string[]
  user_id?: string
  project_id?: string
  scan_id?: string
}

// WebSocket types
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
  user_id?: string
}

export interface WebSocketEvent {
  event: string
  data: any
  timestamp: string
}

// File types
export interface FileUpload {
  id: string
  filename: string
  original_name: string
  size: number
  mime_type: string
  upload_date: string
  status: 'uploading' | 'completed' | 'failed'
  progress: number
  url?: string
  metadata?: Record<string, any>
}

// Audit types
export interface AuditLog extends BaseEntity {
  user_id?: string
  action: string
  resource_type: string
  resource_id: string
  details: any
  ip_address?: string
  user_agent?: string
  success: boolean
  error_message?: string
}

// Health check types
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  checks: HealthCheck[]
  overall_health: number
}

export interface HealthCheck {
  name: string
  status: 'pass' | 'fail' | 'warn'
  response_time: number
  details?: any
  error?: string
}

// Statistics types
export interface Statistics {
  overview: OverviewStats
  trends: TrendData[]
  distributions: DistributionData[]
  performance: PerformanceStats
}

export interface OverviewStats {
  total_projects: number
  total_scans: number
  total_findings: number
  total_insights: number
  total_reports: number
  total_sessions: number
  active_users: number
}

export interface TrendData {
  date: string
  value: number
  change: number
  change_percentage: number
}

export interface DistributionData {
  category: string
  count: number
  percentage: number
  color?: string
}

export interface PerformanceStats {
  average_scan_duration: number
  scan_success_rate: number
  average_response_time: number
  throughput: number
  error_rate: number
}
