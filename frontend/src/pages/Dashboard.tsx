import React, { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material'
import {
  Security,
  BugReport,
  Target,
  Timeline,
  Refresh,
  Add,
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'

import { api } from '../services/api'
import { useWebSocket } from '../hooks/useWebSocket'
import { StatusIndicator } from '../components/StatusIndicator'
import { ScanProgressCard } from '../components/scans/ScanProgressCard'
import { RecentFindingsTable } from '../components/findings/RecentFindingsTable'
import { QuickActionsPanel } from '../components/dashboard/QuickActionsPanel'
import { SystemHealthCard } from '../components/dashboard/SystemHealthCard'
import { AIInsightsCard } from '../components/dashboard/AIInsightsCard'

// Types
interface DashboardStats {
  total_targets: number
  total_findings: number
  total_scans: number
  severity_distribution: {
    critical: number
    high: number
    medium: number
    low: number
  }
  last_scan: string
  system_health: string
}

interface ActiveScan {
  id: string
  target: string
  progress: number
  status: string
  mode: string
  started_at: string
}

interface RecentFinding {
  id: number
  type: string
  severity: string
  url: string
  target: string
  created_at: string
}

const Dashboard: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const queryClient = useQueryClient()
  
  // State
  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d'>('7d')
  const [autoRefresh, setAutoRefresh] = useState(true)
  
  // WebSocket connection for real-time updates
  const { messages, sendMessage } = useWebSocket('/ws/dashboard')
  
  // API Queries
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => api.get('/api/stats/overview'),
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds if auto-refresh is enabled
    staleTime: 10000, // Consider data stale after 10 seconds
  })
  
  const { data: activeScans, isLoading: scansLoading } = useQuery({
    queryKey: ['dashboard', 'active-scans'],
    queryFn: () => api.get('/api/scans?status=running'),
    refetchInterval: autoRefresh ? 10000 : false, // Refresh every 10 seconds for active scans
  })
  
  const { data: recentFindings, isLoading: findingsLoading } = useQuery({
    queryKey: ['dashboard', 'recent-findings'],
    queryFn: () => api.get('/api/findings?limit=10'),
    refetchInterval: autoRefresh ? 60000 : false, // Refresh every minute for findings
  })
  
  const { data: systemStatus, isLoading: systemLoading } = useQuery({
    queryKey: ['dashboard', 'system-status'],
    queryFn: () => api.get('/api/system/status'),
    refetchInterval: autoRefresh ? 15000 : false, // Refresh every 15 seconds for system status
  })
  
  // Mutations
  const refreshMutation = useMutation({
    mutationFn: () => api.post('/api/system/refresh'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Dashboard refreshed successfully')
    },
    onError: (error) => {
      toast.error('Failed to refresh dashboard')
      console.error('Refresh error:', error)
    }
  })
  
  // Handle real-time updates from WebSocket
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      
      if (lastMessage.type === 'scan_update') {
        // Invalidate scans query to refresh data
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'active-scans'] })
        
        // Show toast notification for scan updates
        if (lastMessage.status === 'completed') {
          toast.success(`Scan completed for ${lastMessage.target}`)
        } else if (lastMessage.status === 'failed') {
          toast.error(`Scan failed for ${lastMessage.target}`)
        }
      } else if (lastMessage.type === 'finding_discovered') {
        // Invalidate findings query
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'recent-findings'] })
        
        // Show toast for new findings
        toast.success(`New ${lastMessage.severity} finding discovered!`)
      }
    }
  }, [messages, queryClient])
  
  // Handle refresh
  const handleRefresh = useCallback(() => {
    refreshMutation.mutate()
  }, [refreshMutation])
  
  // Toggle auto-refresh
  const toggleAutoRefresh = useCallback(() => {
    setAutoRefresh(prev => !prev)
    toast.success(autoRefresh ? 'Auto-refresh disabled' : 'Auto-refresh enabled')
  }, [autoRefresh])
  
  // Chart data preparation
  const severityChartData = stats?.severity_distribution ? [
    { name: 'Critical', value: stats.severity_distribution.critical, color: theme.palette.error.main },
    { name: 'High', value: stats.severity_distribution.high, color: theme.palette.warning.main },
    { name: 'Medium', value: stats.severity_distribution.medium, color: theme.palette.info.main },
    { name: 'Low', value: stats.severity_distribution.low, color: theme.palette.success.main }
  ] : []
  
  const timeSeriesData = [
    { time: '00:00', findings: 12, scans: 3 },
    { time: '04:00', findings: 8, scans: 2 },
    { time: '08:00', findings: 25, scans: 5 },
    { time: '12:00', findings: 18, scans: 4 },
    { time: '16:00', findings: 32, scans: 6 },
    { time: '20:00', findings: 15, scans: 3 },
    { time: '24:00', findings: 22, scans: 4 }
  ]
  
  // Loading states
  if (statsLoading && scansLoading && findingsLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {[...Array(8)].map((_, index) => (
            <Grid item xs={12} md={6} lg={3} key={index}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" height={24} />
                  <Skeleton variant="text" width="40%" height={20} />
                  <Skeleton variant="rectangular" width="100%" height={60} sx={{ mt: 1 }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    )
  }
  
  // Error state
  if (statsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load dashboard data. Please check your connection and try again.
        </Alert>
        <Button variant="contained" onClick={handleRefresh} startIcon={<Refresh />}>
          Retry
        </Button>
      </Box>
    )
  }
  
  return (
    <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: theme.palette.background.default }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}>
            Security Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time security testing overview and insights
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Tooltip title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}>
            <IconButton 
              onClick={toggleAutoRefresh}
              color={autoRefresh ? 'primary' : 'default'}
            >
              <Refresh />
            </IconButton>
          </Tooltip>
          
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={refreshMutation.isPending}
          >
            {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Now'}
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<Add />}
            color="primary"
          >
            New Scan
          </Button>
        </Box>
      </Box>
      
      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Key Metrics Cards */}
        <Grid item xs={12} md={6} lg={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${theme.palette.primary.main}15, ${theme.palette.primary.main}05)` }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Security sx={{ fontSize: 40, color: theme.palette.primary.main, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {stats?.total_targets || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Targets
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingUp sx={{ fontSize: 16, color: theme.palette.success.main, mr: 1 }} />
                  <Typography variant="caption" color="success.main">
                    +12% from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid item xs={12} md={6} lg={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${theme.palette.error.main}15, ${theme.palette.error.main}05)` }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <BugReport sx={{ fontSize: 40, color: theme.palette.error.main, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {stats?.total_findings || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Findings
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingDown sx={{ fontSize: 16, color: theme.palette.error.main, mr: 1 }} />
                  <Typography variant="caption" color="error.main">
                    -5% from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid item xs={12} md={6} lg={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${theme.palette.warning.main}15, ${theme.palette.warning.main}05)` }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Target sx={{ fontSize: 40, color: theme.palette.warning.main, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {stats?.total_scans || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Scans
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TrendingUp sx={{ fontSize: 16, color: theme.palette.success.main, mr: 1 }} />
                  <Typography variant="caption" color="success.main">
                    +8% from last week
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid item xs={12} md={6} lg={3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${theme.palette.info.main}15, ${theme.palette.info.main}05)` }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Timeline sx={{ fontSize: 40, color: theme.palette.info.main, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {activeScans?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Scans
                    </Typography>
                  </Box>
                </Box>
                <StatusIndicator 
                  status={systemStatus?.status || 'unknown'} 
                  size="small"
                />
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        {/* Charts Row */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
          >
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                  Security Activity Timeline
                </Typography>
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="findings" 
                      stroke={theme.palette.error.main} 
                      strokeWidth={2}
                      dot={{ fill: theme.palette.error.main }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="scans" 
                      stroke={theme.palette.primary.main} 
                      strokeWidth={2}
                      dot={{ fill: theme.palette.primary.main }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
          >
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                  Findings by Severity
                </Typography>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={severityChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {severityChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        {/* Active Scans */}
        {activeScans && activeScans.length > 0 && (
          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.6 }}
            >
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                    Active Scans
                  </Typography>
                  <Grid container spacing={2}>
                    {activeScans.map((scan: ActiveScan) => (
                      <Grid item xs={12} md={6} lg={4} key={scan.id}>
                        <ScanProgressCard scan={scan} />
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        )}
        
        {/* Recent Findings and Quick Actions */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.7 }}
          >
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                  Recent Findings
                </Typography>
                <RecentFindingsTable findings={recentFindings || []} />
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.8 }}
          >
            <QuickActionsPanel />
          </motion.div>
        </Grid>
        
        {/* System Health and AI Insights */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.9 }}
          >
            <SystemHealthCard status={systemStatus} />
          </motion.div>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 1.0 }}
          >
            <AIInsightsCard />
          </motion.div>
        </Grid>
      </Grid>
      
      {/* Footer */}
      <Box sx={{ mt: 4, pt: 3, borderTop: `1px solid ${theme.palette.divider}` }}>
        <Typography variant="body2" color="text.secondary" align="center">
          Last updated: {new Date().toLocaleString()} | 
          Auto-refresh: {autoRefresh ? 'Enabled' : 'Disabled'} | 
          System Status: {systemStatus?.status || 'Unknown'}
        </Typography>
      </Box>
    </Box>
  )
}

export default Dashboard
