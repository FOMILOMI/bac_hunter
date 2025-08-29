import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  useTheme,
  alpha,
  Tabs,
  Tab,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Button,
  Alert,
} from '@mui/material'
import {
  TrendingUp as TrendIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  BugReport as FindingIcon,
  Timeline as TimelineIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

import { Scan } from '../../types'
import { scansAPI } from '../../services/api'

interface ScanMetricsProps {
  scan: Scan
}

interface MetricsData {
  performance: {
    requests_per_second: number
    average_response_time: number
    total_requests: number
    successful_requests: number
    failed_requests: number
    timeout_requests: number
  }
  findings: {
    total: number
    by_severity: Record<string, number>
    by_type: Record<string, number>
    by_phase: Record<string, number>
    timeline: Array<{ timestamp: string; count: number }>
  }
  coverage: {
    endpoints_tested: number
    total_endpoints: number
    parameters_tested: number
    total_parameters: number
    coverage_percentage: number
  }
  phases: {
    recon: PhaseMetrics
    access: PhaseMetrics
    audit: PhaseMetrics
    exploit: PhaseMetrics
    report: PhaseMetrics
  }
}

interface PhaseMetrics {
  duration: number
  requests_sent: number
  findings_count: number
  success_rate: number
  errors: number
}

const ScanMetrics: React.FC<ScanMetricsProps> = ({ scan }) => {
  const theme = useTheme()
  const [tabValue, setTabValue] = useState(0)

  // Fetch scan metrics
  const {
    data: metricsData,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['scan-metrics', scan.id],
    () => scansAPI.getMetrics(scan.id),
    {
      refetchInterval: scan.status === 'running' ? 5000 : false, // Refresh every 5 seconds for running scans
    }
  )

  const metrics = metricsData?.metrics || {}

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(event, newValue)
  }

  const formatDuration = (seconds: number) => {
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
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      case 'low':
        return 'success'
      default:
        return 'default'
    }
  }

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'recon':
        return <SecurityIcon />
      case 'access':
        return <SpeedIcon />
      case 'audit':
        return <FindingIcon />
      case 'exploit':
        return <TrendIcon />
      case 'report':
        return <SuccessIcon />
      default:
        return <SecurityIcon />
    }
  }

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'recon':
        return 'info'
      case 'access':
        return 'primary'
      case 'audit':
        return 'warning'
      case 'exploit':
        return 'error'
      case 'report':
        return 'success'
      default:
        return 'default'
    }
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load scan metrics: {(error as any).message}
        </Alert>
        <Button onClick={() => refetch()} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TrendIcon />
          Scan Metrics & Analytics
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Export Metrics">
            <IconButton onClick={() => {}} size="small">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Refresh">
            <IconButton onClick={() => refetch()} size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="metrics tabs">
          <Tab label="Overview" icon={<TrendIcon />} iconPosition="start" />
          <Tab label="Performance" icon={<SpeedIcon />} iconPosition="start" />
          <Tab label="Findings" icon={<FindingIcon />} iconPosition="start" />
          <Tab label="Coverage" icon={<SecurityIcon />} iconPosition="start" />
          <Tab label="Phases" icon={<TimelineIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      {tabValue === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Overview Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 1rem',
                      color: theme.palette.primary.main,
                    }}
                  >
                    <SpeedIcon />
                  </Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {metrics.performance?.requests_per_second || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Requests/sec
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette.warning.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 1rem',
                      color: theme.palette.warning.main,
                    }}
                  >
                    <FindingIcon />
                  </Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {metrics.findings?.total || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Findings
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette.success.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 1rem',
                      color: theme.palette.success.main,
                    }}
                  >
                    <SecurityIcon />
                  </Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {metrics.coverage?.coverage_percentage || 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Coverage
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette.info.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 1rem',
                      color: theme.palette.info.main,
                    }}
                  >
                    <TimelineIcon />
                  </Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {scan.duration ? formatDuration(scan.duration) : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Duration
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Quick Stats */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Request Statistics
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Total Requests:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {metrics.performance?.total_requests || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Successful:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                        {metrics.performance?.successful_requests || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Failed:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                        {metrics.performance?.failed_requests || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Timeouts:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'warning.main' }}>
                        {metrics.performance?.timeout_requests || 0}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Coverage Summary
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Endpoints Tested:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {metrics.coverage?.endpoints_tested || 0}/{metrics.coverage?.total_endpoints || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Parameters Tested:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {metrics.coverage?.parameters_tested || 0}/{metrics.coverage?.total_parameters || 0}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Coverage:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                        {metrics.coverage?.coverage_percentage || 0}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </motion.div>
      )}

      {tabValue === 1 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Performance Metrics
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Requests Per Second
                    </Typography>
                    <Typography variant="h3" color="primary.main" sx={{ fontWeight: 700 }}>
                      {metrics.performance?.requests_per_second || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Current rate of requests being sent
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Average Response Time
                    </Typography>
                    <Typography variant="h3" color="info.main" sx={{ fontWeight: 700 }}>
                      {metrics.performance?.average_response_time || 0}ms
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Average time to receive responses
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12}>
                  <Typography variant="subtitle2" sx={{ mb: 2 }}>
                    Request Success Rate
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={metrics.performance?.total_requests ? 
                        ((metrics.performance.successful_requests / metrics.performance.total_requests) * 100) : 0
                      }
                      sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {metrics.performance?.total_requests ? 
                        Math.round((metrics.performance.successful_requests / metrics.performance.total_requests) * 100) : 0
                      }%
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {metrics.performance?.successful_requests || 0} successful out of {metrics.performance?.total_requests || 0} total requests
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {tabValue === 2 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Findings by Severity
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {Object.entries(metrics.findings?.by_severity || {}).map(([severity, count]) => (
                      <Box key={severity} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Chip
                          label={severity}
                          size="small"
                          color={getSeverityColor(severity) as any}
                          variant="outlined"
                        />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {count}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Findings by Type
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {Object.entries(metrics.findings?.by_type || {}).map(([type, count]) => (
                      <Box key={type} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {type}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {count}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Findings Timeline
                  </Typography>
                  <Box sx={{ height: 200, display: 'flex', alignItems: 'end', gap: 1 }}>
                    {metrics.findings?.timeline?.map((point, index) => (
                      <Box
                        key={index}
                        sx={{
                          flexGrow: 1,
                          height: `${(point.count / Math.max(...(metrics.findings?.timeline?.map(p => p.count) || [1]))) * 100}%`,
                          backgroundColor: theme.palette.primary.main,
                          borderRadius: '4px 4px 0 0',
                          minHeight: 4,
                        }}
                      />
                    ))}
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Findings discovered over time
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </motion.div>
      )}

      {tabValue === 3 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Test Coverage Analysis
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Endpoint Coverage
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={metrics.coverage?.total_endpoints ? 
                          ((metrics.coverage.endpoints_tested / metrics.coverage.total_endpoints) * 100) : 0
                        }
                        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {metrics.coverage?.total_endpoints ? 
                          Math.round((metrics.coverage.endpoints_tested / metrics.coverage.total_endpoints) * 100) : 0
                        }%
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {metrics.coverage?.endpoints_tested || 0} of {metrics.coverage?.total_endpoints || 0} endpoints tested
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                      Parameter Coverage
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={metrics.coverage?.total_parameters ? 
                          ((metrics.coverage.parameters_tested / metrics.coverage.total_parameters) * 100) : 0
                        }
                        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {metrics.coverage?.total_parameters ? 
                          Math.round((metrics.coverage.parameters_tested / metrics.coverage.total_parameters) * 100) : 0
                        }%
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {metrics.coverage?.parameters_tested || 0} of {metrics.coverage?.total_parameters || 0} parameters tested
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {tabValue === 4 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Grid container spacing={3}>
            {['recon', 'access', 'audit', 'exploit', 'report'].map((phase) => {
              const phaseData = metrics.phases?.[phase as keyof typeof metrics.phases] as PhaseMetrics
              if (!phaseData) return null
              
              return (
                <Grid item xs={12} md={6} lg={4} key={phase}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                        <Box
                          sx={{
                            color: theme.palette[getPhaseColor(phase) as any]?.main || theme.palette.grey[500],
                          }}
                        >
                          {getPhaseIcon(phase)}
                        </Box>
                        <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                          {phase}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Duration:</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {formatDuration(phaseData.duration || 0)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Requests:</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {phaseData.requests_sent || 0}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Findings:</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600, color: 'warning.main' }}>
                            {phaseData.findings_count || 0}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Success Rate:</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                            {phaseData.success_rate || 0}%
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2">Errors:</Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                            {phaseData.errors || 0}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )
            })}
          </Grid>
        </motion.div>
      )}
    </Box>
  )
}

export default ScanMetrics
