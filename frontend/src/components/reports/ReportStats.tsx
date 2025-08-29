import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Assessment as ReportIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CompletedIcon,
  Schedule as ScheduledIcon,
  Error as FailedIcon,
} from '@mui/icons-material'
import { Report } from '../../types'

interface ReportStatsProps {
  reports: Report[]
}

const ReportStats: React.FC<ReportStatsProps> = ({ reports }) => {
  const theme = useTheme()

  const stats = {
    total: reports.length,
    completed: reports.filter(r => r.status === 'completed').length,
    generating: reports.filter(r => r.status === 'generating').length,
    failed: reports.filter(r => r.status === 'failed').length,
    scheduled: reports.filter(r => r.status === 'scheduled').length,
  }

  const typeDistribution = reports.reduce((acc, report) => {
    acc[report.type] = (acc[report.type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const formatDistribution = reports.reduce((acc, report) => {
    acc[report.format] = (acc[report.format] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const StatCard = ({ icon, title, value, color, subtitle }: {
    icon: React.ReactNode
    title: string
    value: number
    color: string
    subtitle?: string
  }) => (
    <Card sx={{ 
      height: '100%',
      background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`
    }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Box sx={{ 
            p: 1, 
            borderRadius: 2, 
            bgcolor: alpha(color, 0.1),
            color: color,
            mr: 2
          }}>
            {icon}
          </Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, color }}>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
        </Box>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  )

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Report Statistics
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <StatCard
            icon={<ReportIcon />}
            title="Total Reports"
            value={stats.total}
            color={theme.palette.primary.main}
          />
        </Grid>
        
        <Grid item xs={6} md={3}>
          <StatCard
            icon={<CompletedIcon />}
            title="Completed"
            value={stats.completed}
            color={theme.palette.success.main}
            subtitle={`${stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}% success rate`}
          />
        </Grid>
        
        <Grid item xs={6} md={3}>
          <StatCard
            icon={<ScheduledIcon />}
            title="In Progress"
            value={stats.generating + stats.scheduled}
            color={theme.palette.warning.main}
          />
        </Grid>
        
        <Grid item xs={6} md={3}>
          <StatCard
            icon={<FailedIcon />}
            title="Failed"
            value={stats.failed}
            color={theme.palette.error.main}
          />
        </Grid>
      </Grid>

      {/* Distribution Charts */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Report Types
              </Typography>
              {Object.entries(typeDistribution).map(([type, count]) => (
                <Box key={type} sx={{ mb: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {type}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {count} ({stats.total > 0 ? Math.round((count / stats.total) * 100) : 0}%)
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={stats.total > 0 ? (count / stats.total) * 100 : 0}
                    sx={{ height: 6, borderRadius: 3 }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Output Formats
              </Typography>
              {Object.entries(formatDistribution).map(([format, count]) => (
                <Box key={format} sx={{ mb: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" sx={{ textTransform: 'uppercase' }}>
                      {format}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {count} ({stats.total > 0 ? Math.round((count / stats.total) * 100) : 0}%)
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={stats.total > 0 ? (count / stats.total) * 100 : 0}
                    sx={{ height: 6, borderRadius: 3 }}
                    color="secondary"
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default ReportFilters