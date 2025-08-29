import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { Project, Scan, Finding, AIInsight, DashboardStats, UIPreferences } from '../types'

// Dashboard store
interface DashboardState {
  stats: DashboardStats | null
  loading: boolean
  error: string | null
  lastUpdated: Date | null
  setStats: (stats: DashboardStats) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useDashboardStore = create<DashboardState>()(
  subscribeWithSelector((set) => ({
    stats: null,
    loading: false,
    error: null,
    lastUpdated: null,
    setStats: (stats) => set({ stats, lastUpdated: new Date(), error: null }),
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error, loading: false }),
  }))
)

// Projects store
interface ProjectsState {
  projects: Project[]
  currentProject: Project | null
  loading: boolean
  error: string | null
  filters: {
    search: string
    status: string[]
    tags: string[]
  }
  setProjects: (projects: Project[]) => void
  setCurrentProject: (project: Project | null) => void
  addProject: (project: Project) => void
  updateProject: (id: string, updates: Partial<Project>) => void
  removeProject: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setFilters: (filters: Partial<ProjectsState['filters']>) => void
}

export const useProjectsStore = create<ProjectsState>()(
  subscribeWithSelector((set, get) => ({
    projects: [],
    currentProject: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      status: [],
      tags: [],
    },
    setProjects: (projects) => set({ projects, error: null }),
    setCurrentProject: (currentProject) => set({ currentProject }),
    addProject: (project) => set({ projects: [...get().projects, project] }),
    updateProject: (id, updates) => set({
      projects: get().projects.map(p => p.id === id ? { ...p, ...updates } : p),
      currentProject: get().currentProject?.id === id 
        ? { ...get().currentProject!, ...updates } 
        : get().currentProject
    }),
    removeProject: (id) => set({
      projects: get().projects.filter(p => p.id !== id),
      currentProject: get().currentProject?.id === id ? null : get().currentProject
    }),
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error, loading: false }),
    setFilters: (filters) => set({ filters: { ...get().filters, ...filters } }),
  }))
)

// Scans store
interface ScansState {
  scans: Scan[]
  currentScan: Scan | null
  loading: boolean
  error: string | null
  activeScans: Set<string>
  setScans: (scans: Scan[]) => void
  setCurrentScan: (scan: Scan | null) => void
  addScan: (scan: Scan) => void
  updateScan: (id: string, updates: Partial<Scan>) => void
  removeScan: (id: string) => void
  setActiveScan: (id: string, active: boolean) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useScansStore = create<ScansState>()(
  subscribeWithSelector((set, get) => ({
    scans: [],
    currentScan: null,
    loading: false,
    error: null,
    activeScans: new Set(),
    setScans: (scans) => set({ scans, error: null }),
    setCurrentScan: (currentScan) => set({ currentScan }),
    addScan: (scan) => set({ scans: [...get().scans, scan] }),
    updateScan: (id, updates) => set({
      scans: get().scans.map(s => s.id === id ? { ...s, ...updates } : s),
      currentScan: get().currentScan?.id === id 
        ? { ...get().currentScan!, ...updates } 
        : get().currentScan
    }),
    removeScan: (id) => set({
      scans: get().scans.filter(s => s.id !== id),
      currentScan: get().currentScan?.id === id ? null : get().currentScan
    }),
    setActiveScan: (id, active) => {
      const activeScans = new Set(get().activeScans)
      if (active) {
        activeScans.add(id)
      } else {
        activeScans.delete(id)
      }
      set({ activeScans })
    },
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error, loading: false }),
  }))
)

// Findings store
interface FindingsState {
  findings: Finding[]
  currentFinding: Finding | null
  loading: boolean
  error: string | null
  totalCount: number
  filters: {
    search: string
    severity: string[]
    status: string[]
    type: string[]
    project_id: string
    scan_id: string
  }
  pagination: {
    page: number
    limit: number
    sort: string
    order: 'asc' | 'desc'
  }
  setFindings: (findings: Finding[], totalCount: number) => void
  setCurrentFinding: (finding: Finding | null) => void
  addFinding: (finding: Finding) => void
  updateFinding: (id: string, updates: Partial<Finding>) => void
  removeFinding: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setFilters: (filters: Partial<FindingsState['filters']>) => void
  setPagination: (pagination: Partial<FindingsState['pagination']>) => void
}

export const useFindingsStore = create<FindingsState>()(
  subscribeWithSelector((set, get) => ({
    findings: [],
    currentFinding: null,
    loading: false,
    error: null,
    totalCount: 0,
    filters: {
      search: '',
      severity: [],
      status: [],
      type: [],
      project_id: '',
      scan_id: '',
    },
    pagination: {
      page: 1,
      limit: 25,
      sort: 'created_at',
      order: 'desc',
    },
    setFindings: (findings, totalCount) => set({ findings, totalCount, error: null }),
    setCurrentFinding: (currentFinding) => set({ currentFinding }),
    addFinding: (finding) => set({ 
      findings: [...get().findings, finding],
      totalCount: get().totalCount + 1
    }),
    updateFinding: (id, updates) => set({
      findings: get().findings.map(f => f.id === id ? { ...f, ...updates } : f),
      currentFinding: get().currentFinding?.id === id 
        ? { ...get().currentFinding!, ...updates } 
        : get().currentFinding
    }),
    removeFinding: (id) => set({
      findings: get().findings.filter(f => f.id !== id),
      currentFinding: get().currentFinding?.id === id ? null : get().currentFinding,
      totalCount: Math.max(0, get().totalCount - 1)
    }),
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error, loading: false }),
    setFilters: (filters) => set({ filters: { ...get().filters, ...filters } }),
    setPagination: (pagination) => set({ pagination: { ...get().pagination, ...pagination } }),
  }))
)

// AI Insights store
interface AIInsightsState {
  insights: AIInsight[]
  loading: boolean
  error: string | null
  setInsights: (insights: AIInsight[]) => void
  addInsight: (insight: AIInsight) => void
  updateInsight: (id: string, updates: Partial<AIInsight>) => void
  removeInsight: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useAIInsightsStore = create<AIInsightsState>()(
  subscribeWithSelector((set, get) => ({
    insights: [],
    loading: false,
    error: null,
    setInsights: (insights) => set({ insights, error: null }),
    addInsight: (insight) => set({ insights: [...get().insights, insight] }),
    updateInsight: (id, updates) => set({
      insights: get().insights.map(i => i.id === id ? { ...i, ...updates } : i)
    }),
    removeInsight: (id) => set({
      insights: get().insights.filter(i => i.id !== id)
    }),
    setLoading: (loading) => set({ loading }),
    setError: (error) => set({ error, loading: false }),
  }))
)

// WebSocket store
interface WebSocketState {
  connected: boolean
  reconnecting: boolean
  error: string | null
  lastMessage: any
  messageHistory: any[]
  setConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setError: (error: string | null) => void
  addMessage: (message: any) => void
  clearHistory: () => void
}

export const useWebSocketStore = create<WebSocketState>()(
  subscribeWithSelector((set, get) => ({
    connected: false,
    reconnecting: false,
    error: null,
    lastMessage: null,
    messageHistory: [],
    setConnected: (connected) => set({ connected, error: connected ? null : get().error }),
    setReconnecting: (reconnecting) => set({ reconnecting }),
    setError: (error) => set({ error, connected: false }),
    addMessage: (message) => set({
      lastMessage: message,
      messageHistory: [...get().messageHistory.slice(-99), message] // Keep last 100 messages
    }),
    clearHistory: () => set({ messageHistory: [], lastMessage: null }),
  }))
)

// UI Preferences store
interface UIState {
  preferences: UIPreferences
  sidebarOpen: boolean
  currentTheme: 'dark' | 'light'
  notifications: Array<{
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    message: string
    timestamp: Date
    read: boolean
  }>
  setPreferences: (preferences: Partial<UIPreferences>) => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: 'dark' | 'light') => void
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void
  markNotificationRead: (id: string) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

export const useUIStore = create<UIState>()(
  subscribeWithSelector((set, get) => ({
    preferences: {
      theme: 'dark',
      sidebar_collapsed: false,
      default_page_size: 25,
      auto_refresh_interval: 30000,
      show_tooltips: true,
      compact_mode: false,
    },
    sidebarOpen: true,
    currentTheme: 'dark',
    notifications: [],
    setPreferences: (preferences) => set({
      preferences: { ...get().preferences, ...preferences }
    }),
    setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
    setTheme: (currentTheme) => set({ currentTheme }),
    addNotification: (notification) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      set({
        notifications: [...get().notifications, {
          ...notification,
          id,
          timestamp: new Date(),
          read: false,
        }]
      })
    },
    markNotificationRead: (id) => set({
      notifications: get().notifications.map(n => 
        n.id === id ? { ...n, read: true } : n
      )
    }),
    removeNotification: (id) => set({
      notifications: get().notifications.filter(n => n.id !== id)
    }),
    clearNotifications: () => set({ notifications: [] }),
  }))
)

// Global loading state
interface LoadingState {
  globalLoading: boolean
  loadingStates: Record<string, boolean>
  setGlobalLoading: (loading: boolean) => void
  setLoading: (key: string, loading: boolean) => void
  isLoading: (key: string) => boolean
}

export const useLoadingStore = create<LoadingState>()(
  (set, get) => ({
    globalLoading: false,
    loadingStates: {},
    setGlobalLoading: (globalLoading) => set({ globalLoading }),
    setLoading: (key, loading) => set({
      loadingStates: { ...get().loadingStates, [key]: loading }
    }),
    isLoading: (key) => get().loadingStates[key] || false,
  })
)
