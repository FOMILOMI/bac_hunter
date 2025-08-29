import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  useTheme,
  Grid,
  Tooltip
} from '@mui/material'
import {
  Memory,
  Storage,
  Speed,
  NetworkCheck,
  CheckCircle,
  Warning,
  Error
} from '@mui/icons-material'
import { motion } from 'framer-motion'

interface SystemStatus {
  status: string
  uptime: string
  database_size: string
  active_scans: number
  memory_usage: string
  cpu_usage: string
  disk_usage: string
}

interface SystemHealthCardProps {
  status?: SystemStatus
  className?: string
}

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ status, className }) => {
  const theme = useTheme()
  
  // Default values if status is not provided
  const defaultStatus: SystemStatus = {
    status: 'operational',
    uptime: '24h 15m 30s',
    database_size: '45.2 MB',
    active_scans: 2,
    memory_usage: '128 MB',
    cpu_usage: '15%',
    disk_usage: '2.1 GB'
  }
  
  const systemStatus = status || defaultStatus
  
  // Get health status configuration
  const getHealthStatus = () => {
    switch (systemStatus.status.toLowerCase()) {
      case 'operational':
      case 'healthy':
        return {
          color: theme.palette.success.main,
          icon: CheckCircle,
          label: 'Operational'
        }
      case 'degraded':
      case 'warning':
        return {
          color: theme.palette.warning.main,
          icon: Warning,
          label: 'Degraded'
        }
      case 'critical':
      case 'error':
        return {
          color: theme.palette.error.main,
          icon: Error,
          label: 'Critical'
        }
      default:
        return {
          color: theme.palette.grey[500],
          icon: Warning,
          label: 'Unknown'
        }
    }
  }
  
  // Parse usage values for progress bars
  const parseUsage = (usage: string) => {
    if (usage.includes('%')) {
      return parseInt(usage.replace('%', ''))
    }
    if (usage.includes('MB')) {
      const value = parseInt(usage.replace(' MB', ''))
      return Math.min((value / 1024) * 100, 100) // Assume 1GB max
    }
    if (usage.includes('GB')) {
      const value = parseFloat(usage.replace(' GB', ''))
      return Math.min((value / 10) * 100, 100) // Assume 10GB max
    }
    return 0
  }
  
  // Get usage color based on percentage
  const getUsageColor = (percentage: number) => {
    if (percentage < 50) return theme.palette.success.main
    if (percentage < 80) return theme.palette.warning.main
    return theme.palette.error.main
  }
  
  const healthStatus = getHealthStatus()
  const StatusIcon = healthStatus.icon
  
  // Metrics to display
  const metrics = [
    {
      label: 'Memory Usage',
      value: systemStatus.memory_usage,
      icon: Memory,
      color: getUsageColor(parseUsage(systemStatus.memory_usage))
    },
    {
      label: 'CPU Usage',
      value: systemStatus.cpu_usage,
      icon: Speed,
      color: getUsageColor(parseUsage(systemStatus.cpu_usage))
    },
    {
      label: 'Disk Usage',
      value: systemStatus.disk_usage,
      icon: Storage,
      color: getUsageColor(parseUsage(systemStatus.disk_usage))
    },
    {
      label: 'Active Scans',
      value: `${systemStatus.active_scans}`,
      icon: NetworkCheck,
      color: systemStatus.active_scans > 0 ? theme.palette.info.main : theme.palette.grey[500]
    }
  ]
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className={className} sx={{ height: '100%' }}>
        <CardContent>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              System Health
            </Typography>
            
            <Chip
              icon={<StatusIcon />}
              label={healthStatus.label}
              size="small"
              sx={{
                backgroundColor: healthStatus.color,
                color: 'white',
                fontWeight: 'bold'
              }}
            />
          </Box>
          
          {/* Overall Status */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Overall Status:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold', color: healthStatus.color }}>
                {healthStatus.label}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Uptime:
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                {systemStatus.uptime}
              </Typography>
            </Box>
          </Box>
          
          {/* Metrics Grid */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {metrics.map((metric, index) => {
              const MetricIcon = metric.icon
              const usagePercentage = parseUsage(metric.value)
              
              return (
                <Grid item xs={6} key={metric.label}>
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <Box sx={{ textAlign: 'center' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
                        <MetricIcon sx={{ fontSize: 20, color: metric.color, mr: 1 }} />
                        <Typography variant="caption" color="text.secondary">
                          {metric.label}
                        </Typography>
                      </Box>
                      
                      <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {metric.value}
                      </Typography>
                      
                      {metric.label !== 'Active Scans' && (
                        <LinearProgress
                          variant="determinate"
                          value={usagePercentage}
                          sx={{
                            height: 6,
                            borderRadius: 3,
                            backgroundColor: theme.palette.grey[200],
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: metric.color,
                              borderRadius: 3
                            }
                          }}
                        />
                      )}
                    </Box>
                  </motion.div>
                </Grid>
              )
            })}
          </Grid>
          
          {/* Database Info */}
          <Box sx={{ 
            p: 2, 
            backgroundColor: theme.palette.grey[50], 
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`
          }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
              Database Information
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Storage sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Size: {systemStatus.database_size}
              </Typography>
            </Box>
          </Box>
          
          {/* Health Indicators */}
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Health Indicators:
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Tooltip title="Memory Usage" arrow>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: getUsageColor(parseUsage(systemStatus.memory_usage))
                  }}
                />
              </Tooltip>
              
              <Tooltip title="CPU Usage" arrow>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: getUsageColor(parseUsage(systemStatus.cpu_usage))
                  }}
                />
              </Tooltip>
              
              <Tooltip title="Disk Usage" arrow>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: getUsageColor(parseUsage(systemStatus.disk_usage))
                  }}
                />
              </Tooltip>
              
              <Tooltip title="Network Status" arrow>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: theme.palette.success.main
                  }}
                />
              </Tooltip>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default SystemHealthCard