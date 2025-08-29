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
  ListItemText,
  Avatar,
} from '@mui/material'
import {
  BugReport as BugIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

const RecentFindings: React.FC = () => {
  const navigate = useNavigate()

  const findings = [
    {
      id: '1',
      title: 'SQL Injection in Login Form',
      severity: 'critical',
      url: '/login',
      timestamp: '2 minutes ago',
      type: 'SQL Injection',
    },
    {
      id: '2',
      title: 'Cross-Site Scripting (XSS)',
      severity: 'high',
      url: '/search',
      timestamp: '15 minutes ago',
      type: 'XSS',
    },
    {
      id: '3',
      title: 'Insecure Direct Object Reference',
      severity: 'high',
      url: '/api/users/{id}',
      timestamp: '23 minutes ago',
      type: 'IDOR',
    },
    {
      id: '4',
      title: 'Missing Security Headers',
      severity: 'medium',
      url: '/dashboard',
      timestamp: '1 hour ago',
      type: 'Configuration',
    },
    {
      id: '5',
      title: 'Information Disclosure',
      severity: 'low',
      url: '/api/info',
      timestamp: '2 hours ago',
      type: 'Information Leak',
    },
  ]

  const getSeverityColor = (severity: string) => {
    switch (severity) {
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

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <SecurityIcon />
      case 'high':
        return <WarningIcon />
      case 'medium':
        return <BugIcon />
      case 'low':
        return <InfoIcon />
      default:
        return <BugIcon />
    }
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Recent Findings"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheader="Latest security vulnerabilities"
        action={
          <Button
            size="small"
            endIcon={<LaunchIcon />}
            onClick={() => navigate('/findings')}
          >
            View All
          </Button>
        }
      />
      <CardContent sx={{ pt: 0, maxHeight: 400, overflow: 'auto' }}>
        <List disablePadding>
          {findings.map((finding, index) => (
            <ListItem
              key={finding.id}
              sx={{
                px: 0,
                py: 1.5,
                borderBottom: index < findings.length - 1 ? '1px solid' : 'none',
                borderColor: 'divider',
                cursor: 'pointer',
                borderRadius: 1,
                '&:hover': {
                  backgroundColor: 'action.hover',
                },
              }}
              onClick={() => navigate(`/findings/${finding.id}`)}
            >
              <Avatar
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: `${getSeverityColor(finding.severity)}.main`,
                  mr: 1.5,
                  '& .MuiSvgIcon-root': {
                    fontSize: 18,
                  },
                }}
              >
                {getSeverityIcon(finding.severity)}
              </Avatar>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: 600,
                        flexGrow: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {finding.title}
                    </Typography>
                    <Chip
                      label={finding.severity}
                      size="small"
                      color={getSeverityColor(finding.severity) as any}
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        mb: 0.5,
                      }}
                    >
                      {finding.url}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Chip
                        label={finding.type}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.65rem', height: 18 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {finding.timestamp}
                      </Typography>
                    </Box>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  )
}

export default RecentFindings
