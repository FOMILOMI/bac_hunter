import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material'
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Security,
  Speed,
  Timer
} from '@mui/icons-material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'

import { api } from '../../services/api'
import { StatusIndicator } from '../StatusIndicator'

interface ScanProgressCardProps {
  scan: {
    id: string
    target: string
    progress: number
    status: string
    mode: string
    started_at: string
  }
  className?: string
}

const ScanProgressCard: React.FC<ScanProgressCardProps> = ({ scan, className }) => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  
  // Mutations
  const pauseScanMutation = useMutation({
    mutationFn: () => api.pauseScan(scan.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'active-scans'] })
    }
  })
  
  const resumeScanMutation = useMutation({
    mutationFn: () => api.resumeScan(scan.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'active-scans'] })
    }
  })
  
  const stopScanMutation = useMutation({
    mutationFn: () => api.deleteScan(scan.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'active-scans'] })
    }
  })
  
  // Calculate time elapsed
  const getTimeElapsed = () => {
    if (!scan.started_at) return '0m'
    
    const startTime = new Date(scan.started_at)
    const now = new Date()
    const diffMs = now.getTime() - startTime.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 60) {
      return `${diffMins}m`
    } else {
      const hours = Math.floor(diffMins / 60)
      const mins = diffMins % 60
      return `${hours}h ${mins}m`
    }
  }
  
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return theme.palette.success.main
      case 'paused':
        return theme.palette.warning.main
      case 'stopped':
        return theme.palette.error.main
      default:
        return theme.palette.grey[500]
    }
  }
  
  // Get mode color
  const getModeColor = (mode: string) => {
    switch (mode.toLowerCase()) {
      case 'stealth':
        return theme.palette.info.main
      case 'standard':
        return theme.palette.primary.main
      case 'aggressive':
        return theme.palette.warning.main
      case 'maximum':
        return theme.palette.error.main
      default:
        return theme.palette.grey[500]
    }
  }
  
  // Handle scan control actions
  const handlePause = () => {
    pauseScanMutation.mutate()
  }
  
  const handleResume = () => {
    resumeScanMutation.mutate()
  }
  
  const handleStop = () => {
    stopScanMutation.mutate()
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card 
        className={className}
        sx={{
          height: '100%',
          border: `1px solid ${theme.palette.divider}`,
          '&:hover': {
            borderColor: getStatusColor(scan.status),
            boxShadow: `0 4px 12px ${getStatusColor(scan.status)}20`
          }
        }}
      >
        <CardContent>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Security sx={{ color: getStatusColor(scan.status) }} />
              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                {scan.target}
              </Typography>
            </Box>
            
            <StatusIndicator 
              status={scan.status} 
              size="small" 
              variant="icon"
            />
          </Box>
          
          {/* Progress Bar */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Progress
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                {Math.round(scan.progress)}%
              </Typography>
            </Box>
            
            <LinearProgress
              variant="determinate"
              value={scan.progress}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: theme.palette.grey[200],
                '& .MuiLinearProgress-bar': {
                  backgroundColor: getStatusColor(scan.status),
                  borderRadius: 4
                }
              }}
            />
          </Box>
          
          {/* Scan Details */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Speed sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                Mode: 
              </Typography>
              <Chip
                label={scan.mode}
                size="small"
                sx={{
                  backgroundColor: getModeColor(scan.mode),
                  color: 'white',
                  fontSize: '0.7rem',
                  height: 20
                }}
              />
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Timer sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                Time: {getTimeElapsed()}
              </Typography>
            </Box>
          </Box>
          
          {/* Control Buttons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            {scan.status === 'running' ? (
              <Tooltip title="Pause Scan">
                <IconButton
                  size="small"
                  onClick={handlePause}
                  disabled={pauseScanMutation.isPending}
                  sx={{
                    color: theme.palette.warning.main,
                    '&:hover': {
                      backgroundColor: `${theme.palette.warning.main}10`
                    }
                  }}
                >
                  <Pause />
                </IconButton>
              </Tooltip>
            ) : (
              <Tooltip title="Resume Scan">
                <IconButton
                  size="small"
                  onClick={handleResume}
                  disabled={resumeScanMutation.isPending}
                  sx={{
                    color: theme.palette.success.main,
                    '&:hover': {
                      backgroundColor: `${theme.palette.success.main}10`
                    }
                  }}
                >
                  <PlayArrow />
                </IconButton>
              </Tooltip>
            )}
            
            <Tooltip title="Stop Scan">
              <IconButton
                size="small"
                onClick={handleStop}
                disabled={stopScanMutation.isPending}
                sx={{
                  color: theme.palette.error.main,
                  '&:hover': {
                    backgroundColor: `${theme.palette.error.main}10`
                  }
                }}
              >
                <Stop />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Refresh">
              <IconButton
                size="small"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['dashboard', 'active-scans'] })}
                sx={{
                  color: theme.palette.info.main,
                  '&:hover': {
                    backgroundColor: `${theme.palette.info.main}10`
                  }
                }}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default ScanProgressCard