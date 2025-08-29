import React, { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Tooltip,
  useTheme,
  alpha,
  Avatar,
  Grid,
  Divider,
} from '@mui/material'
import {
  MoreVert as MoreIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  Download as ExportIcon,
  Settings as SettingsIcon,
  BugReport as FindingIcon,
  Assessment as ReportIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  TrendingUp as TrendIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  History as HistoryIcon,
  Schedule as ScheduleIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { Scan } from '../../types'

interface ScanCardProps {
  scan: Scan
  onPause: (id: string) => void
  onResume: (id: string) => void
  onStop: (id: string) => void
  onDelete: (id: string) => void
  onViewLogs: (scan: Scan) => void
  onViewMetrics: (scan: Scan) => void
}

const ScanCard: React.FC<ScanCardProps> = ({
  scan,
  onPause,
  onResume,
  onStop,
  onDelete,
  onViewLogs,
  onViewMetrics,
}) => {
  const theme = useTheme()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [elapsedTime, setElapsedTime] = useState(0)

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

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation()
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleAction = (action: () => void) => {
    handleMenuClose()
    action()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'primary'
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'paused':
        return 'warning'
      case 'queued':
        return 'info'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <TrendIcon fontSize="small" />
      case 'completed':
        return <SuccessIcon fontSize="small" />
      case 'failed':
        return <ErrorIcon fontSize="small" />
      case 'paused':
        return <PauseIcon fontSize="small" />
      case 'queued':
        return <ScheduleIcon fontSize="small" />
      default:
        return <InfoIcon fontSize="small" />
    }
  }

  const getProgressValue = () => {
    if (scan.status === 'completed') return 100
    if (scan.status === 'failed') return 0
    if (scan.progress && scan.progress.percentage) return scan.progress.percentage
    return 0
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

  const getScanTypeIcon = (scanType: string) => {
    switch (scanType) {
      case 'quick':
        return <SpeedIcon />
      case 'comprehensive':
        return <SecurityIcon />
      case 'stealth':
        return <TimelineIcon />
      case 'aggressive':
        return <WarningIcon />
      default:
        return <SecurityIcon />
    }
  }

  const getScanTypeColor = (scanType: string) => {
    switch (scanType) {
      case 'quick':
        return 'success'
      case 'comprehensive':
        return 'primary'
      case 'stealth':
        return 'info'
      case 'aggressive':
        return 'warning'
      default:
        return 'default'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className="hover-lift"
        sx={{
          height: '100%',
          cursor: 'pointer',
          position: 'relative',
          overflow: 'visible',
          '&:hover': {
            borderColor: theme.palette.primary.main,
          },
        }}
        onClick={() => navigate(`/scans/${scan.id}`)}
      >
        {/* Status indicator bar */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            backgroundColor: alpha(theme.palette[getStatusColor(scan.status) as any]?.main || theme.palette.grey[500], 0.3),
            borderTopLeftRadius: theme.shape.borderRadius,
            borderTopRightRadius: theme.shape.borderRadius,
          }}
        />

        <CardContent sx={{ pt: 3 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  mb: 0.5,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {scan.name || `Scan ${scan.id}`}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  mb: 1,
                }}
              >
                {scan.description || 'Security testing scan'}
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  display: 'block',
                  fontFamily: 'monospace',
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {scan.target_url}
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={handleMenuOpen}
              sx={{ ml: 1, flexShrink: 0 }}
            >
              <MoreIcon />
            </IconButton>
          </Box>

          {/* Status and Progress */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Chip
                icon={getStatusIcon(scan.status)}
                label={scan.status}
                size="small"
                color={getStatusColor(scan.status) as any}
                variant="outlined"
                sx={{ fontSize: '0.75rem', height: 24 }}
              />
              <Typography variant="caption" color="text.secondary">
                {scan.started_at ? new Date(scan.started_at).toLocaleDateString() : 'Not started'}
              </Typography>
            </Box>
            
            {/* Progress Bar */}
            <Box sx={{ mt: 1 }}>
              <LinearProgress
                variant="determinate"
                value={getProgressValue()}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: theme.palette.primary.main,
                    borderRadius: 3,
                  },
                }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {getProgressValue()}% Complete
                </Typography>
                {scan.status === 'running' && (
                  <Typography variant="caption" color="text.secondary">
                    {formatDuration(elapsedTime)}
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>

          {/* Scan Information */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    backgroundColor: alpha(theme.palette[getScanTypeColor(scan.scan_type || 'default') as any]?.main || theme.palette.grey[500], 0.1),
                    color: theme.palette[getScanTypeColor(scan.scan_type || 'default') as any]?.main || theme.palette.grey[500],
                    mx: 'auto',
                    mb: 0.5,
                  }}
                >
                  {getScanTypeIcon(scan.scan_type || 'default')}
                </Avatar>
                <Typography variant="caption" color="text.secondary">
                  {scan.scan_type || 'Custom'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="warning.main" sx={{ fontWeight: 600 }}>
                  {scan.findings_count || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Findings
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Scan Details */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Scan Details
            </Typography>
            <Grid container spacing={1}>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">
                  Started:
                </Typography>
                <Typography variant="caption" sx={{ ml: 0.5 }}>
                  {scan.started_at ? new Date(scan.started_at).toLocaleTimeString() : 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">
                  Duration:
                </Typography>
                <Typography variant="caption" sx={{ ml: 0.5 }}>
                  {scan.duration ? formatDuration(scan.duration) : 'N/A'}
                </Typography>
              </Grid>
              {scan.completed_at && (
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Completed:
                  </Typography>
                  <Typography variant="caption" sx={{ ml: 0.5 }}>
                    {new Date(scan.completed_at).toLocaleTimeString()}
                  </Typography>
                </Grid>
              )}
              {scan.requests_per_second && (
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    RPS:
                  </Typography>
                  <Typography variant="caption" sx={{ ml: 0.5 }}>
                    {scan.requests_per_second}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Box>

          {/* Tags */}
          {scan.tags && scan.tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {scan.tags.slice(0, 3).map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              ))}
              {scan.tags.length > 3 && (
                <Chip
                  label={`+${scan.tags.length - 3}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              )}
            </Box>
          )}
        </CardContent>

        {/* Actions */}
        <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
            <Tooltip title="View Details">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/scans/${scan.id}`)
                }}
                sx={{ flexGrow: 1 }}
              >
                <ViewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            {scan.status === 'running' && (
              <Tooltip title="Pause Scan">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    onPause(scan.id)
                  }}
                  sx={{ flexGrow: 1 }}
                  color="warning"
                >
                  <PauseIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            
            {scan.status === 'paused' && (
              <Tooltip title="Resume Scan">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    onResume(scan.id)
                  }}
                  sx={{ flexGrow: 1 }}
                  color="primary"
                >
                  <StartIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            
            {(scan.status === 'running' || scan.status === 'paused') && (
              <Tooltip title="Stop Scan">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    onStop(scan.id)
                  }}
                  sx={{ flexGrow: 1 }}
                  color="error"
                >
                  <StopIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </CardActions>

        {/* Action Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          onClick={(e) => e.stopPropagation()}
        >
          <MenuItem onClick={() => handleAction(() => navigate(`/scans/${scan.id}`))}>
            <ListItemIcon>
              <ViewIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => onViewLogs(scan))}>
            <ListItemIcon>
              <TimelineIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Logs</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => onViewMetrics(scan))}>
            <ListItemIcon>
              <TrendIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Metrics</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/scans/${scan.id}/findings`))}>
            <ListItemIcon>
              <FindingIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Findings</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/scans/${scan.id}/report`))}>
            <ListItemIcon>
              <ReportIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Generate Report</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={() => handleAction(() => navigate(`/scans/${scan.id}/settings`))}>
            <ListItemIcon>
              <SettingsIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Scan Settings</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/scans/${scan.id}/export`))}>
            <ListItemIcon>
              <ExportIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Export Results</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={() => handleAction(() => onDelete(scan.id))}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText sx={{ color: 'error.main' }}>Delete Scan</ListItemText>
          </MenuItem>
        </Menu>
      </Card>
    </motion.div>
  )
}

export default ScanCard
