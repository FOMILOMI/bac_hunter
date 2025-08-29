import React from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Grid,
  useTheme,
  alpha,
} from '@mui/material'
import {
  CheckCircle as SuccessIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
} from '@mui/icons-material'

interface SystemHealthProps {
  successRate: number
  avgDuration: number
}

const SystemHealth: React.FC<SystemHealthProps> = ({ successRate, avgDuration }) => {
  const theme = useTheme()

  const getHealthColor = (value: number) => {
    if (value >= 90) return theme.palette.success.main
    if (value >= 70) return theme.palette.warning.main
    return theme.palette.error.main
  }

  const getHealthStatus = (value: number) => {
    if (value >= 90) return 'Excellent'
    if (value >= 70) return 'Good'
    return 'Needs Attention'
  }

  const healthMetrics = [
    {
      label: 'Scan Success Rate',
      value: successRate,
      unit: '%',
      icon: <SuccessIcon />,
    },
    {
      label: 'Avg Response Time',
      value: 1.2,
      unit: 's',
      icon: <SpeedIcon />,
    },
    {
      label: 'Memory Usage',
      value: 68,
      unit: '%',
      icon: <MemoryIcon />,
    },
    {
      label: 'Storage Usage',
      value: 45,
      unit: '%',
      icon: <StorageIcon />,
    },
  ]

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="System Health"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        action={
          <Chip
            label={getHealthStatus(successRate)}
            size="small"
            sx={{
              backgroundColor: alpha(getHealthColor(successRate), 0.1),
              color: getHealthColor(successRate),
              fontWeight: 600,
            }}
          />
        }
      />
      <CardContent>
        <Grid container spacing={3}>
          {healthMetrics.map((metric, index) => (
            <Grid item xs={12} sm={6} key={index}>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box
                    sx={{
                      p: 0.5,
                      borderRadius: 1,
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      mr: 1,
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    {React.cloneElement(metric.icon, { fontSize: 'small' })}
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                    {metric.label}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {metric.value}{metric.unit}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={metric.value}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.grey[500], 0.2),
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getHealthColor(metric.value),
                      borderRadius: 3,
                    },
                  }}
                />
              </Box>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ mt: 3, p: 2, backgroundColor: alpha(theme.palette.primary.main, 0.05), borderRadius: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Average Scan Duration
          </Typography>
          <Typography variant="h6" color="primary.main" sx={{ fontWeight: 600 }}>
            {avgDuration} minutes
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Based on last 50 scans
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

export default SystemHealth
