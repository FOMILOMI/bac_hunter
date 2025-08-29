import React, { useState, useEffect } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
  Button,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  BugReport as BugIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Psychology as AIIcon,
} from '@mui/icons-material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

import APIService, { ScanRequest } from '../services/api'
import { useDashboardStore } from '../store/dashboardStore'
import { useWebSocketStore } from '../store/webSocketStore'
import StatusIndicator from '../components/StatusIndicator'

const Dashboard: React.FC = () => {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d'>('24h')
  const { stats, setStats } = useDashboardStore()
  const { connected } = useWebSocketStore()
  const queryClient = useQueryClient()

  // Fetch dashboard data
  const { data: overviewStats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['dashboard-stats', selectedTimeRange],
    queryFn: () => APIService.getOverviewStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: targetStats, isLoading: targetStatsLoading } = useQuery({
    queryKey: ['target-stats'],
    queryFn: () => APIService.getTargetStats(),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: findingStats, isLoading: findingStatsLoading } = useQuery({
    queryKey: ['finding-stats'],
    queryFn: () => APIService.getFindingStats(),
    refetchInterval: 60000,
  })

  const { data: aiModels, isLoading: aiModelsLoading } = useQuery({
    queryKey: ['ai-models'],
    queryFn: () => APIService.listAIModels(),
    refetchInterval: 120000, // Refresh every 2 minutes
  })

  // Recent scans
  const { data: recentScans, isLoading: scansLoading } = useQuery({
    queryKey: ['recent-scans'],
    queryFn: () => APIService.listScans({ limit: 5 }),
    refetchInterval: 15000, // Refresh every 15 seconds
  })

  // Quick scan mutation
  const quickScanMutation = useMutation({
    mutationFn: (target: string) => APIService.createScan({
      target,
      mode: 'standard',
      max_rps: 2.0,
      phases: ['recon', 'access'],
      enable_ai: true,
    }),
    onSuccess: (data) => {
      toast.success(`Quick scan started: ${data.scan_id}`)
      queryClient.invalidateQueries({ queryKey: ['recent-scans'] })
    },
    onError: (error) => {
      toast.error('Failed to start quick scan')
    },
  })

  // Update stats when WebSocket data arrives
  useEffect(() => {
    if (overviewStats) {
      setStats(overviewStats)
    }
  }, [overviewStats, setStats])

  // Mock data for charts (replace with real data)
  const scanTrendData = [
    { time: '00:00', scans: 12, findings: 45 },
    { time: '04:00', scans: 8, findings: 32 },
    { time: '08:00', scans: 25, findings: 89 },
    { time: '12:00', scans: 18, findings: 67 },
    { time: '16:00', scans: 22, findings: 78 },
    { time: '20:00', scans: 15, findings: 54 },
  ]

  const severityDistribution = [
    { name: 'Critical', value: 15, color: '#f44336' },
    { name: 'High', value: 28, color: '#ff9800' },
    { name: 'Medium', value: 45, color: '#ffc107' },
    { name: 'Low', value: 32, color: '#4caf50' },
    { name: 'Info', value: 20, color: '#2196f3' },
  ]

  const handleQuickScan = (target: string) => {
    if (!target.trim()) {
      toast.error('Please enter a target URL')
      return
    }
    quickScanMutation.mutate(target)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success'
      case 'completed': return 'primary'
      case 'failed': return 'error'
      case 'pending': return 'warning'
      default: return 'default'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error'
      case 'high': return 'error'
      case 'medium': return 'warning'
      case 'low': return 'info'
      default: return 'default'
    }
  }

  if (statsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load dashboard data. Please check your connection and try again.
        </Alert>
        <Button variant="contained" onClick={() => queryClient.invalidateQueries()}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <StatusIndicator connected={connected} />
          <Typography variant="body2" color="text.secondary">
            {connected ? 'Connected to BAC Hunter' : 'Disconnected'}
          </Typography>
        </Box>
      </Box>

      {/* Quick Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <input
                  type="text"
                  placeholder="Enter target URL (e.g., https://example.com)"
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const target = (e.target as HTMLInputElement).value
                      handleQuickScan(target)
                    }
                  }}
                />
                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  onClick={() => {
                    const input = document.querySelector('input[type="text"]') as HTMLInputElement
                    if (input) handleQuickScan(input.value)
                  }}
                  disabled={quickScanMutation.isPending}
                >
                  Quick Scan
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={() => queryClient.invalidateQueries()}
                >
                  Refresh Data
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<AIIcon />}
                  onClick={() => {/* Navigate to AI insights */}}
                >
                  AI Analysis
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Scans
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <Skeleton width={60} /> : (overviewStats?.scans_last_24h || 0)}
                  </Typography>
                </Box>
                <SpeedIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Total Findings
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <Skeleton width={60} /> : (overviewStats?.findings_last_24h || 0)}
                  </Typography>
                </Box>
                <BugIcon color="error" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Active Scans
                  </Typography>
                  <Typography variant="h4">
                    {statsLoading ? <Skeleton width={60} /> : (overviewStats?.scans_by_status?.running || 0)}
                  </Typography>
                </Box>
                <PlayIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    AI Models
                  </Typography>
                  <Typography variant="h4">
                    {aiModelsLoading ? <Skeleton width={60} /> : (aiModels?.models?.length || 0)}
                  </Typography>
                </Box>
                <AIIcon color="secondary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Scan Trends */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scan Activity (Last 24 Hours)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={scanTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="scans" stroke="#2196f3" strokeWidth={2} />
                  <Line type="monotone" dataKey="findings" stroke="#f44336" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Severity Distribution */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Findings by Severity
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={severityDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {severityDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        {/* Recent Scans */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Scans
              </Typography>
              {scansLoading ? (
                <Box>
                  {[1, 2, 3].map((i) => (
                    <Box key={i} sx={{ mb: 2 }}>
                      <Skeleton height={20} />
                      <Skeleton height={16} width="60%" />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Box>
                  {recentScans?.scans?.slice(0, 5).map((scan: any) => (
                    <Box key={scan.id} sx={{ mb: 2, p: 2, border: '1px solid #eee', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2" noWrap>
                          {scan.name}
                        </Typography>
                        <Chip
                          label={scan.status}
                          color={getStatusColor(scan.status) as any}
                          size="small"
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {scan.target_id} • {scan.mode} mode
                      </Typography>
                      {scan.status === 'running' && (
                        <LinearProgress
                          variant="determinate"
                          value={scan.progress * 100}
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* AI Insights */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                AI Insights
              </Typography>
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Pattern Detected:</strong> Multiple endpoints with similar response patterns detected.
                  </Typography>
                </Alert>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Anomaly:</strong> Unusual response times detected in authentication endpoints.
                  </Typography>
                </Alert>
                <Alert severity="success">
                  <Typography variant="body2">
                    <strong>Recommendation:</strong> Consider enabling advanced evasion techniques for stealth scanning.
                  </Typography>
                </Alert>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard
