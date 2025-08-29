import React, { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Paper,
  Divider,
  Alert,
  Skeleton,
  LinearProgress,
  Button,
  Grid,
  FormControlLabel,
  Checkbox,
  Switch,
  OutlinedInput,
} from '@mui/material'
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Clear as ClearIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  BugReport as FindingIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'

import { Scan } from '../../types'
import { scansAPI } from '../../services/api'

interface ScanLogsProps {
  scan: Scan
}

interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warning' | 'error' | 'success' | 'finding'
  message: string
  details?: any
  phase?: string
  target?: string
  payload?: string
  response?: string
}

const ScanLogs: React.FC<ScanLogsProps> = ({ scan }) => {
  const theme = useTheme()
  const logsEndRef = useRef<HTMLDivElement>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<string[]>([])
  const [phaseFilter, setPhaseFilter] = useState<string[]>([])
  const [autoScroll, setAutoScroll] = useState(true)
  const [showRawLogs, setShowRawLogs] = useState(false)

  // Fetch scan logs
  const {
    data: logsData,
    isLoading,
    error,
    refetch,
  } = useQuery(
    ['scan-logs', scan.id],
    () => scansAPI.getLogs(scan.id),
    {
      refetchInterval: scan.status === 'running' ? 2000 : false, // Refresh every 2 seconds for running scans
    }
  )

  const logs = logsData?.logs || []

  // Auto-scroll to bottom for new logs
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  // Filter logs based on search and filters
  const filteredLogs = logs.filter((log: LogEntry) => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (log.target && log.target.toLowerCase().includes(searchTerm.toLowerCase())) ||
                         (log.payload && log.payload.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesLevel = levelFilter.length === 0 || levelFilter.includes(log.level)
    const matchesPhase = phaseFilter.length === 0 || (log.phase && phaseFilter.includes(log.phase))
    
    return matchesSearch && matchesLevel && matchesPhase
  })

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <InfoIcon fontSize="small" />
      case 'warning':
        return <WarningIcon fontSize="small" />
      case 'error':
        return <ErrorIcon fontSize="small" />
      case 'success':
        return <SuccessIcon fontSize="small" />
      case 'finding':
        return <FindingIcon fontSize="small" />
      default:
        return <InfoIcon fontSize="small" />
    }
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'info':
        return 'info'
      case 'warning':
        return 'warning'
      case 'error':
        return 'error'
      case 'success':
        return 'success'
      case 'finding':
        return 'error'
      default:
        return 'default'
    }
  }

  const getLevelBackground = (level: string) => {
    switch (level) {
      case 'info':
        return alpha(theme.palette.info.main, 0.1)
      case 'warning':
        return alpha(theme.palette.warning.main, 0.1)
      case 'error':
        return alpha(theme.palette.error.main, 0.1)
      case 'success':
        return alpha(theme.palette.success.main, 0.1)
      case 'finding':
        return alpha(theme.palette.error.main, 0.15)
      default:
        return alpha(theme.palette.grey[500], 0.1)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const exportLogs = () => {
    const logText = filteredLogs.map(log => 
      `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.message}`
    ).join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `scan-logs-${scan.id}-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const clearFilters = () => {
    setSearchTerm('')
    setLevelFilter([])
    setPhaseFilter([])
  }

  const hasActiveFilters = searchTerm || levelFilter.length > 0 || phaseFilter.length > 0

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load scan logs: {(error as any).message}
        </Alert>
        <Button onClick={() => refetch()} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, pb: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SecurityIcon />
          Scan Logs
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                size="small"
              />
            }
            label="Auto-scroll"
            sx={{ mr: 1 }}
          />
          
          <Tooltip title="Export Logs">
            <IconButton onClick={exportLogs} size="small">
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

      {/* Filters */}
      <Box sx={{ mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      onClick={() => setSearchTerm('')}
                    >
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Level</InputLabel>
              <Select
                multiple
                value={levelFilter}
                onChange={(e) => setLevelFilter(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                input={<OutlinedInput label="Level" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {['info', 'warning', 'error', 'success', 'finding'].map((level) => (
                  <MenuItem key={level} value={level}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={levelFilter.indexOf(level) > -1}
                          size="small"
                        />
                      }
                      label={level}
                      sx={{ margin: 0 }}
                    />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Phase</InputLabel>
              <Select
                multiple
                value={phaseFilter}
                onChange={(e) => setPhaseFilter(typeof e.target.value === 'string' ? e.target.value.split(',') : e.target.value)}
                input={<OutlinedInput label="Phase" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {['recon', 'access', 'audit', 'exploit', 'report'].map((phase) => (
                  <MenuItem key={phase} value={phase}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={phaseFilter.indexOf(phase) > -1}
                          size="small"
                        />
                      }
                      label={phase}
                      sx={{ margin: 0 }}
                    />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        
        {hasActiveFilters && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              {filteredLogs.length} of {logs.length} logs shown
            </Typography>
            <Button
              onClick={clearFilters}
              size="small"
              startIcon={<ClearIcon />}
              sx={{ ml: 'auto' }}
            >
              Clear Filters
            </Button>
          </Box>
        )}
      </Box>

      {/* Logs Display */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', position: 'relative' }}>
        {isLoading ? (
          <Box sx={{ p: 2 }}>
            <Skeleton variant="rectangular" height={400} />
          </Box>
        ) : filteredLogs.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary">
              {hasActiveFilters ? 'No logs match your filters' : 'No logs available yet'}
            </Typography>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <AnimatePresence>
              {filteredLogs.map((log, index) => (
                <motion.div
                  key={log.id || index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  <Paper
                    sx={{
                      p: 2,
                      backgroundColor: getLevelBackground(log.level),
                      border: 1,
                      borderColor: alpha(theme.palette[getLevelColor(log.level) as any]?.main || theme.palette.grey[500], 0.3),
                      '&:hover': {
                        backgroundColor: alpha(theme.palette[getLevelColor(log.level) as any]?.main || theme.palette.grey[500], 0.15),
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                      <Box
                        sx={{
                          color: theme.palette[getLevelColor(log.level) as any]?.main || theme.palette.grey[500],
                          mt: 0.5,
                        }}
                      >
                        {getLevelIcon(log.level)}
                      </Box>
                      
                      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                            {formatTimestamp(log.timestamp)}
                          </Typography>
                          
                          <Chip
                            label={log.level}
                            size="small"
                            color={getLevelColor(log.level) as any}
                            variant="outlined"
                            sx={{ fontSize: '0.65rem', height: 20 }}
                          />
                          
                          {log.phase && (
                            <Chip
                              label={log.phase}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.65rem', height: 20 }}
                            />
                          )}
                        </Box>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {log.message}
                        </Typography>
                        
                        {log.target && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                            Target: {log.target}
                          </Typography>
                        )}
                        
                        {log.payload && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Payload:
                            </Typography>
                            <Paper
                              sx={{
                                p: 1,
                                backgroundColor: alpha(theme.palette.grey[900], 0.1),
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                overflow: 'auto',
                              }}
                            >
                              {log.payload}
                            </Paper>
                          </Box>
                        )}
                        
                        {log.response && (
                          <Box>
                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                              Response:
                            </Typography>
                            <Paper
                              sx={{
                                p: 1,
                                backgroundColor: alpha(theme.palette.grey[900], 0.1),
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                overflow: 'auto',
                              }}
                            >
                              {log.response}
                            </Paper>
                          </Box>
                        )}
                      </Box>
                    </Box>
                  </Paper>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {/* Auto-scroll anchor */}
            <div ref={logsEndRef} />
          </Box>
        )}
      </Box>

      {/* Status Bar */}
      <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="caption" color="text.secondary">
            {filteredLogs.length} logs • {scan.status} • {scan.findings_count || 0} findings
          </Typography>
          
          {scan.status === 'running' && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Live updates enabled
              </Typography>
              <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'success.main' }} />
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  )
}

export default ScanLogs
