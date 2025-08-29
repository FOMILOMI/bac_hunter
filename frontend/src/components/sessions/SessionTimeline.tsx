import React from 'react'
import {
  Box,
  Typography,
  Paper,
  useTheme,
} from '@mui/material'
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/lab'
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  CheckCircle as CompleteIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { Session } from '../../types'

interface SessionTimelineProps {
  session: Session
}

const SessionTimeline: React.FC<SessionTimelineProps> = ({ session }) => {
  const theme = useTheme()

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'start': return <StartIcon />
      case 'stop': return <StopIcon />
      case 'complete': return <CompleteIcon />
      case 'error': return <ErrorIcon />
      default: return <InfoIcon />
    }
  }

  const getEventColor = (type: string) => {
    switch (type) {
      case 'start': return theme.palette.primary.main
      case 'stop': return theme.palette.warning.main
      case 'complete': return theme.palette.success.main
      case 'error': return theme.palette.error.main
      default: return theme.palette.info.main
    }
  }

  // Mock timeline events - in real implementation, these would come from session logs
  const timelineEvents = [
    {
      id: '1',
      type: 'start',
      title: 'Session Started',
      description: 'Security scanning session initiated',
      timestamp: session.start_time || new Date().toISOString(),
    },
    {
      id: '2', 
      type: 'info',
      title: 'Target Analysis',
      description: 'Analyzing target application structure',
      timestamp: session.start_time || new Date().toISOString(),
    },
    {
      id: '3',
      type: 'complete',
      title: 'Session Completed',
      description: 'All security checks completed successfully',
      timestamp: session.end_time || new Date().toISOString(),
    }
  ]

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Session Timeline
      </Typography>
      
      <Timeline>
        {timelineEvents.map((event, index) => (
          <TimelineItem key={event.id}>
            <TimelineSeparator>
              <TimelineDot sx={{ color: getEventColor(event.type), bgcolor: 'transparent', border: `2px solid ${getEventColor(event.type)}` }}>
                {getEventIcon(event.type)}
              </TimelineDot>
              {index < timelineEvents.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent sx={{ py: '12px', px: 2 }}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="h6" component="h3">
                  {event.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {event.description}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {new Date(event.timestamp).toLocaleString()}
                </Typography>
              </Paper>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Box>
  )
}

export default SessionTimeline