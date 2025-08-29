import React, { useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  useTheme,
  alpha,
  Tooltip,
  LinearProgress,
} from '@mui/material'
import {
  PlayArrow as RunningIcon,
  Pause as PausedIcon,
  CheckCircle as CompletedIcon,
  Error as FailedIcon,
  Schedule as QueuedIcon,
  BugReport as FindingIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendIcon,
  Timer as TimerIcon,
  Security as SecurityIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

import { Scan } from '../../types'

interface ScanStatsProps {
  scans: Scan[]
}

const ScanStats: React.FC<ScanStatsProps> = ({ scans }) => {
  const theme = useTheme()

  const stats = useMemo(() => {
    const totalScans = scans.length
    const runningScans = scans.filter(s => s.status === 'running').length
    const pausedScans = scans.filter(s => s.status === 'paused').length
    const completedScans = scans.filter(s => s.status === 'completed').length
    const failedScans = scans.filter(s => s.status === 'failed').length
    const queuedScans = scans.filter(s => s.status === 'queued').length
    
    const totalFindings = scans.reduce((sum, s) => sum + (s.findings_count || 0), 0)
    const totalDuration = scans.reduce((sum, s) => sum + (s.duration || 0), 0)
    const avgDuration = totalScans > 0 ? totalDuration / totalScans : 0
    
    const completionRate = totalScans > 0 ? ((completedScans / totalScans) * 100).toFixed(1) : 0
    const successRate = totalScans > 0 ? (((completedScans + runningScans) / totalScans) * 100).toFixed(1) : 0

    // Calculate scan type distribution
    const scanTypeStats = scans.reduce((acc, scan) => {
      const type = scan.scan_type || 'custom'
      acc[type] = (acc[type] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    // Calculate average RPS
    const totalRPS = scans.reduce((sum, s) => sum + (s.requests_per_second || 0), 0)
    const avgRPS = scans.length > 0 ? (totalRPS / scans.length).toFixed(1) : 0

    return {
      totalScans,
      runningScans,
      pausedScans,
      completedScans,
      failedScans,
      queuedScans,
      totalFindings,
      totalDuration,
      avgDuration,
      completionRate,
      successRate,
      scanTypeStats,
      avgRPS,
    }
  }, [scans])

  const statCards = [
    {
      title: 'Total Scans',
      value: stats.totalScans,
      icon: SecurityIcon,
      color: 'primary',
      description: 'All scans in the system',
      trend: null,
    },
    {
      title: 'Running',
      value: stats.runningScans,
      icon: RunningIcon,
      color: 'info',
      description: 'Currently active scans',
      trend: stats.runningScans > 0 ? 'up' : 'stable',
    },
    {
      title: 'Completed',
      value: stats.completedScans,
      icon: CompletedIcon,
      color: 'success',
      description: 'Successfully completed scans',
      trend: 'up',
    },
    {
      title: 'Failed',
      value: stats.failedScans,
      icon: FailedIcon,
      color: 'error',
      description: 'Failed or errored scans',
      trend: stats.failedScans > 0 ? 'down' : 'stable',
    },
    {
      title: 'Total Findings',
      value: stats.totalFindings,
      icon: FindingIcon,
      color: 'warning',
      description: 'Security vulnerabilities found',
      trend: stats.totalFindings > 0 ? 'up' : 'stable',
    },
    {
      title: 'Avg Duration',
      value: `${Math.floor(stats.avgDuration / 60)}m ${Math.floor(stats.avgDuration % 60)}s`,
      icon: TimerIcon,
      color: 'secondary',
      description: 'Average scan duration',
      trend: null,
    },
  ]

  const getTrendIcon = (trend: string | null) => {
    if (!trend) return null
    return (
      <TrendIcon
        sx={{
          fontSize: '1rem',
          color: trend === 'up' ? 'success.main' : trend === 'down' ? 'error.main' : 'text.secondary',
          transform: trend === 'down' ? 'rotate(180deg)' : 'none',
        }}
      />
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return theme.palette.info.main
      case 'completed':
        return theme.palette.success.main
      case 'failed':
        return theme.palette.error.main
      case 'paused':
        return theme.palette.warning.main
      case 'queued':
        return theme.palette.info.main
      default:
        return theme.palette.grey[500]
    }
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

  return (
    <Box sx={{ mb: 3 }}>
      {/* Main Stats Grid */}
      <Grid container spacing={3}>
        {statCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={stat.title}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card
                sx={{
                  height: '100%',
                  position: 'relative',
                  overflow: 'visible',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: theme.shadows[8],
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 2.5, textAlign: 'center' }}>
                  {/* Icon */}
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette[stat.color as any]?.main || theme.palette.primary.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 1rem',
                      color: theme.palette[stat.color as any]?.main || theme.palette.primary.main,
                    }}
                  >
                    <stat.icon sx={{ fontSize: '1.5rem' }} />
                  </Box>

                  {/* Value */}
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {stat.value}
                  </Typography>

                  {/* Title */}
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    {stat.title}
                  </Typography>

                  {/* Description */}
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    {stat.description}
                  </Typography>

                  {/* Trend Indicator */}
                  {stat.trend && (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      {getTrendIcon(stat.trend)}
                      <Typography variant="caption" color="text.secondary">
                        {stat.trend === 'up' ? 'Trending up' : stat.trend === 'down' ? 'Trending down' : 'Stable'}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* Progress Metrics */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CompletedIcon color="success" />
                Completion Rate
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h4" color="success.main" sx={{ fontWeight: 700 }}>
                  {stats.completionRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  of scans completed successfully
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={parseFloat(stats.completionRate)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: alpha(theme.palette.success.main, 0.2),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: theme.palette.success.main,
                    borderRadius: 4,
                  },
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendIcon color="primary" />
                Success Rate
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                  {stats.successRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  of scans running or completed
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={parseFloat(stats.successRate)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: theme.palette.primary.main,
                    borderRadius: 4,
                  },
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Status Distribution */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Scan Status Distribution
          </Typography>
          <Grid container spacing={2}>
            {[
              { status: 'running', label: 'Running', count: stats.runningScans, color: 'info' },
              { status: 'paused', label: 'Paused', count: stats.pausedScans, color: 'warning' },
              { status: 'completed', label: 'Completed', count: stats.completedScans, color: 'success' },
              { status: 'failed', label: 'Failed', count: stats.failedScans, color: 'error' },
              { status: 'queued', label: 'Queued', count: stats.queuedScans, color: 'info' },
            ].map((item) => (
              <Grid item xs={12} sm={6} md={2.4} key={item.status}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: getStatusColor(item.status),
                    }}
                  />
                  <Typography variant="body2" sx={{ flexGrow: 1 }}>
                    {item.label}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {item.count}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ({stats.totalScans > 0 ? ((item.count / stats.totalScans) * 100).toFixed(1) : 0}%)
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Performance Metrics
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Average Duration
                  </Typography>
                  <Typography variant="h5" color="secondary.main" sx={{ fontWeight: 600 }}>
                    {formatDuration(stats.avgDuration)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Average RPS
                  </Typography>
                  <Typography variant="h5" color="info.main" sx={{ fontWeight: 600 }}>
                    {stats.avgRPS}
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
                Scan Type Distribution
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {Object.entries(stats.scanTypeStats).map(([type, count]) => (
                  <Box key={type} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {type}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {count}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({stats.totalScans > 0 ? ((count / stats.totalScans) * 100).toFixed(1) : 0}%)
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default ScanStats
