import React from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  LinearProgress,
} from '@mui/material'
import {
  Psychology as AIIcon,
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

const AIInsightsWidget: React.FC = () => {
  const navigate = useNavigate()

  const insights = [
    {
      id: '1',
      type: 'optimization',
      title: 'Scan Performance Improvement',
      description: 'Detected opportunity to reduce scan time by 23% through parameter optimization',
      confidence: 87,
      priority: 'high',
      icon: <SpeedIcon />,
      color: 'primary',
    },
    {
      id: '2',
      type: 'security',
      title: 'Pattern Recognition Alert',
      description: 'Similar vulnerability patterns found across 3 different endpoints',
      confidence: 92,
      priority: 'critical',
      icon: <SecurityIcon />,
      color: 'error',
    },
    {
      id: '3',
      type: 'recommendation',
      title: 'Testing Strategy Optimization',
      description: 'AI suggests focusing on authentication bypass techniques for this target',
      confidence: 78,
      priority: 'medium',
      icon: <TrendingUpIcon />,
      color: 'info',
    },
  ]

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      case 'low':
        return 'success'
      default:
        return 'default'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 85) return 'success'
    if (confidence >= 70) return 'warning'
    return 'error'
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="AI Insights"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheader="Intelligent recommendations and analysis"
        action={
          <Button
            size="small"
            endIcon={<LaunchIcon />}
            onClick={() => navigate('/ai-insights')}
          >
            View All
          </Button>
        }
      />
      <CardContent sx={{ pt: 0 }}>
        <List disablePadding>
          {insights.map((insight, index) => (
            <ListItem
              key={insight.id}
              sx={{
                px: 0,
                py: 1.5,
                borderBottom: index < insights.length - 1 ? '1px solid' : 'none',
                borderColor: 'divider',
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: `${insight.color}.main`,
                    '& .MuiSvgIcon-root': {
                      fontSize: 18,
                    },
                  }}
                >
                  {insight.icon}
                </Avatar>
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, flexGrow: 1 }}>
                      {insight.title}
                    </Typography>
                    <Chip
                      label={insight.priority}
                      size="small"
                      color={getPriorityColor(insight.priority) as any}
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {insight.description}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Confidence:
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={insight.confidence}
                        sx={{
                          width: 60,
                          height: 4,
                          borderRadius: 2,
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getConfidenceColor(insight.confidence) + '.main',
                          },
                        }}
                      />
                      <Typography
                        variant="caption"
                        color={getConfidenceColor(insight.confidence) + '.main'}
                        sx={{ fontWeight: 600 }}
                      >
                        {insight.confidence}%
                      </Typography>
                    </Box>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>

        <Box sx={{ mt: 2, p: 2, backgroundColor: 'action.hover', borderRadius: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AIIcon color="primary" />
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              AI Learning Status
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Model trained on 1,247 scans • Last update: 2 hours ago
          </Typography>
          <LinearProgress
            variant="determinate"
            value={78}
            sx={{
              height: 6,
              borderRadius: 3,
              '& .MuiLinearProgress-bar': {
                backgroundColor: 'primary.main',
              },
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Learning progress: 78% complete
          </Typography>
        </Box>
      </CardContent>
    </Card>
  )
}

export default AIInsightsWidget
