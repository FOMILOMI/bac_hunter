import React from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
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
  PlayArrow as ScanIcon,
  BugReport as FindingIcon,
  FolderOpen as ProjectIcon,
  Assessment as ReportIcon,
  Psychology as AIIcon,
} from '@mui/icons-material'
import { formatDistanceToNow } from 'date-fns'

interface ActivityItem {
  id: string
  type: 'scan_started' | 'scan_completed' | 'finding_discovered' | 'project_created' | 'ai_insight_generated'
  title: string
  description: string
  timestamp: string
  project_id?: string
  scan_id?: string
  finding_id?: string
}

interface ActivityTimelineProps {
  activities: ActivityItem[]
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ activities = [] }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'scan_started':
      case 'scan_completed':
        return <ScanIcon />
      case 'finding_discovered':
        return <FindingIcon />
      case 'project_created':
        return <ProjectIcon />
      case 'ai_insight_generated':
        return <AIIcon />
      default:
        return <ReportIcon />
    }
  }

  const getColor = (type: string) => {
    switch (type) {
      case 'scan_started':
        return 'primary'
      case 'scan_completed':
        return 'success'
      case 'finding_discovered':
        return 'error'
      case 'project_created':
        return 'info'
      case 'ai_insight_generated':
        return 'secondary'
      default:
        return 'default'
    }
  }

  const getSeverityColor = (description: string) => {
    if (description.toLowerCase().includes('critical')) return 'error'
    if (description.toLowerCase().includes('high')) return 'warning'
    if (description.toLowerCase().includes('medium')) return 'info'
    if (description.toLowerCase().includes('low')) return 'success'
    return 'default'
  }

  // Mock activities if none provided
  const mockActivities: ActivityItem[] = [
    {
      id: '1',
      type: 'finding_discovered',
      title: 'Critical vulnerability found',
      description: 'SQL Injection detected in login form',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 minutes ago
    },
    {
      id: '2',
      type: 'scan_completed',
      title: 'Scan completed',
      description: 'Comprehensive scan of example.com finished',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
    },
    {
      id: '3',
      type: 'ai_insight_generated',
      title: 'AI recommendation available',
      description: 'New optimization suggestions generated',
      timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
    },
    {
      id: '4',
      type: 'project_created',
      title: 'New project created',
      description: 'Security assessment for API Gateway',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
    },
    {
      id: '5',
      type: 'scan_started',
      title: 'Scan initiated',
      description: 'Started vulnerability assessment',
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(), // 3 hours ago
    },
  ]

  const displayActivities = activities.length > 0 ? activities : mockActivities

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Recent Activity"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheader="Latest system events and updates"
      />
      <CardContent sx={{ pt: 0, maxHeight: 400, overflow: 'auto' }}>
        {displayActivities.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No recent activity
            </Typography>
          </Box>
        ) : (
          <Timeline sx={{ p: 0 }}>
            {displayActivities.slice(0, 5).map((activity, index) => (
              <TimelineItem key={activity.id}>
                <TimelineSeparator>
                  <TimelineDot color={getColor(activity.type) as any} variant="outlined">
                    {getIcon(activity.type)}
                  </TimelineDot>
                  {index < displayActivities.length - 1 && <TimelineConnector />}
                </TimelineSeparator>
                <TimelineContent sx={{ py: '12px', px: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {activity.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 1, flexShrink: 0 }}>
                      {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {activity.description}
                  </Typography>
                  {activity.type === 'finding_discovered' && (
                    <Chip
                      label={activity.description.toLowerCase().includes('critical') ? 'Critical' : 
                            activity.description.toLowerCase().includes('high') ? 'High' :
                            activity.description.toLowerCase().includes('medium') ? 'Medium' : 'Low'}
                      size="small"
                      color={getSeverityColor(activity.description) as any}
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  )}
                </TimelineContent>
              </TimelineItem>
            ))}
          </Timeline>
        )}
      </CardContent>
    </Card>
  )
}

export default ActivityTimeline
