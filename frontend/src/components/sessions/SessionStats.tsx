import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Timeline as TimelineIcon,
  CheckCircle as CompletedIcon,
  PlayArrow as RunningIcon,
  Error as FailedIcon,
} from '@mui/icons-material'
import { Session } from '../../types'

interface SessionStatsProps {
  sessions: Session[]
}

const SessionStats: React.FC<SessionStatsProps> = ({ sessions }) => {
  const theme = useTheme()

  const stats = {
    total: sessions.length,
    completed: sessions.filter(s => s.status === 'completed').length,
    running: sessions.filter(s => s.status === 'running').length,
    failed: sessions.filter(s => s.status === 'failed').length,
  }

  const StatCard = ({ icon, title, value, color }: {
    icon: React.ReactNode
    title: string
    value: number
    color: string
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
      </CardContent>
    </Card>
  )

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Session Statistics
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={6} md={3}>
          <StatCard
            icon={<TimelineIcon />}
            title="Total Sessions"
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
          />
        </Grid>
        
        <Grid item xs={6} md={3}>
          <StatCard
            icon={<RunningIcon />}
            title="Running"
            value={stats.running}
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
    </Box>
  )
}

export default SessionStats