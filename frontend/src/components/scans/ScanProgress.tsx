import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  useTheme,
  alpha,
  CircularProgress,
  Tooltip,
  IconButton,
  Button,
  Alert,
} from '@mui/material'
import {
  PlayArrow as RunningIcon,
  Pause as PausedIcon,
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  Speed as SpeedIcon,
  Timer as TimerIcon,
  TrendingUp as TrendIcon,
  Security as SecurityIcon,
  BugReport as FindingIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

import { Scan } from '../../types'
import { scansAPI } from '../../services/api'

interface ScanProgressProps {
  scan: Scan
}

interface ProgressData {
  phase: string
  progress: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  start_time?: string
  end_time?: string
  duration?: number
  findings_count: number
  requests_sent: number
  requests_total: number
  current_target?: string
  current_payload?: string
}

const ScanProgress: React.FC<ScanProgressProps> = ({ scan }) => {
  const theme = useTheme()
  const [elapsedTime, setElapsedTime] = useState(0)

  // Fetch real-time progress data
  const {
    data: progressData,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['scan-progress', scan.id],
    () => scansAPI.getProgress(scan.id),
    {
      refetchInterval: scan.status === 'running' ? 1000 : false, // Refresh every second for running scans
    }
  )

  const progress = progressData?.progress || {}

  // Calculate elapsed time for running scans
  useEffect(() => {
    let interval: NodeJS.Timeout
    if (scan.status === 'running' && scan.started_at) {
      const startTime = new Date(scan.started_at).getTime()
      const updateElapsed = () => {
        const now = Date.now()
        setElapsedTime(Math.floor((now - startTime) / 1000))
      }
      updateElapsed()
      interval = setInterval(updateElapsed, 1000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [scan.status, scan.started_at])

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

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'recon':
        return <SecurityIcon />
      case 'access':
        return <SpeedIcon />
      case 'audit':
        return <BugReportIcon />
      case 'exploit':
        return <TrendIcon />
      case 'report':
        return <CompletedIcon />
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'default'
      case 'running':
        return 'primary'
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      default:
        return 'default'
    }
  }

  const getOverallProgress = () => {
    if (scan.status === 'completed') return 100
    if (scan.status === 'failed') return 0
    
    const phases = ['recon', 'access', 'audit', 'exploit', 'report']
    const totalWeight = phases.length
    let completedWeight = 0
    
    phases.forEach(phase => {
      if (progress[phase]?.status === 'completed') {
        completedWeight += 1
      } else if (progress[phase]?.status === 'running') {
        completedWeight += (progress[phase]?.progress || 0) / 100
      }
    })
    
    return Math.round((completedWeight / totalWeight) * 100)
  }

  const getCurrentPhase = () => {
    const phases = ['recon', 'access', 'audit', 'exploit', 'report']
    for (const phase of phases) {
      if (progress[phase]?.status === 'running') {
        return phase
      }
    }
    return null
  }

  const getCurrentPhaseProgress = () => {
    const currentPhase = getCurrentPhase()
    if (currentPhase && progress[currentPhase]) {
      return progress[currentPhase].progress || 0
    }
    return 0
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load scan progress: {(error as any).message}
        </Alert>
        <Button onClick={() => refetch()} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      {/* Overall Progress */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <RunningIcon color="primary" />
              Overall Progress
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                {getOverallProgress()}%
              </Typography>
              {scan.status === 'running' && (
                <CircularProgress size={24} color="primary" />
              )}
            </Box>
          </Box>
          
          <LinearProgress
            variant="determinate"
            value={getOverallProgress()}
            sx={{
              height: 12,
              borderRadius: 6,
              backgroundColor: alpha(theme.palette.primary.main, 0.2),
              '& .MuiLinearProgress-bar': {
                backgroundColor: theme.palette.primary.main,
                borderRadius: 6,
              },
            }}
          />
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {scan.status === 'running' ? 'Scan in progress...' : `Scan ${scan.status}`}
            </Typography>
            {scan.status === 'running' && (
              <Typography variant="caption" color="text.secondary">
                Elapsed: {formatDuration(elapsedTime)}
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Current Phase */}
      {getCurrentPhase() && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendIcon color="info" />
              Current Phase: {getCurrentPhase()?.charAt(0).toUpperCase() + getCurrentPhase()?.slice(1)}
            </Typography>
            
            <LinearProgress
              variant="determinate"
              value={getCurrentPhaseProgress()}
              sx={{
                height: 10,
                borderRadius: 5,
                backgroundColor: alpha(theme.palette.info.main, 0.2),
                '& .MuiLinearProgress-bar': {
                  backgroundColor: theme.palette.info.main,
                  borderRadius: 5,
                },
              }}
            />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {getCurrentPhaseProgress()}% complete
              </Typography>
              {progress[getCurrentPhase()!]?.current_target && (
                <Typography variant="caption" color="text.secondary">
                  Target: {progress[getCurrentPhase()!].current_target}
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Phase Details */}
      <Grid container spacing={2}>
        {['recon', 'access', 'audit', 'exploit', 'report'].map((phase) => {
          const phaseData = progress[phase] as ProgressData
          if (!phaseData) return null
          
          return (
            <Grid item xs={12} md={6} lg={4} key={phase}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card
                  sx={{
                    height: '100%',
                    border: 2,
                    borderColor: phaseData.status === 'running' 
                      ? theme.palette.primary.main 
                      : 'transparent',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            color: theme.palette[getPhaseColor(phase) as any]?.main || theme.palette.grey[500],
                          }}
                        >
                          {getPhaseIcon(phase)}
                        </Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                          {phase}
                        </Typography>
                      </Box>
                      
                      <Chip
                        label={phaseData.status}
                        size="small"
                        color={getStatusColor(phaseData.status) as any}
                        variant="outlined"
                      />
                    </Box>
                    
                    {/* Phase Progress */}
                    <Box sx={{ mb: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={phaseData.progress || 0}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: alpha(theme.palette[getPhaseColor(phase) as any]?.main || theme.palette.grey[500], 0.2),
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: theme.palette[getPhaseColor(phase) as any]?.main || theme.palette.grey[500],
                            borderRadius: 3,
                          },
                        }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {phaseData.progress || 0}% complete
                      </Typography>
                    </Box>
                    
                    {/* Phase Stats */}
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Findings:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: 'warning.main' }}>
                          {phaseData.findings_count || 0}
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Requests:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {phaseData.requests_sent || 0}/{phaseData.requests_total || 0}
                        </Typography>
                      </Grid>
                      
                      {phaseData.duration && (
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Duration:
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {formatDuration(phaseData.duration)}
                          </Typography>
                        </Grid>
                      )}
                      
                      {phaseData.current_target && (
                        <Grid item xs={12}>
                          <Typography variant="caption" color="text.secondary">
                            Current Target:
                          </Typography>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                            {phaseData.current_target}
                          </Typography>
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          )
        })}
      </Grid>

      {/* Real-time Stats */}
      {scan.status === 'running' && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Real-time Statistics
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main" sx={{ fontWeight: 700 }}>
                    {scan.findings_count || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Findings
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main" sx={{ fontWeight: 700 }}>
                    {formatDuration(elapsedTime)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Elapsed Time
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                    {scan.requests_per_second || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Requests/sec
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main" sx={{ fontWeight: 700 }}>
                    {getCurrentPhase()?.charAt(0).toUpperCase() + getCurrentPhase()?.slice(1) || 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Current Phase
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default ScanProgress
