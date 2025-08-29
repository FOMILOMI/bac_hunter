import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  useTheme,
  alpha,
  LinearProgress,
  Badge,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Alert,
  Skeleton,
  Tooltip,
  CircularProgress,
  Avatar,
  CardActions,
  Collapse,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  TrendingUp as TrendIcon,
  Security as SecurityIcon,
  BugReport as FindingIcon,
  Psychology as AIIcon,
  Assessment as ReportIcon,
  Storage as SessionIcon,
  Code as CodeIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  AutoAwesome as AutoAwesomeIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
  Email as EmailIcon,
  CloudDownload as CloudDownloadIcon,
  PictureAsPdf as PDFIcon,
  Description as HTMLIcon,
  TableChart as CSVIcon,
  DataObject as JSONIcon,
  Upload as UploadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Replay as ReplayIcon,
  AccountTree as TreeIcon,
  NetworkCheck as NetworkIcon,
  Http as HttpIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  Send as SendIcon,
  Save as SaveIcon,
  Folder as FolderIcon,
  History as HistoryIcon,
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as ShowChartIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { dashboardAPI } from '../services/api'
import { Project, Scan, Finding, AIInsight, Report, Session } from '../types'
import DashboardWidget from '../components/dashboard/DashboardWidget'
import MetricsOverview from '../components/dashboard/MetricsOverview'
import RecentActivity from '../components/dashboard/RecentActivity'
import QuickActions from '../components/dashboard/QuickActions'
import SecurityOverview from '../components/dashboard/SecurityOverview'
import PerformanceMetrics from '../components/dashboard/PerformanceMetrics'

const Dashboard: React.FC = () => {
  const theme = useTheme()
  const navigate = useNavigate()
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [expandedWidgets, setExpandedWidgets] = useState<Set<string>>(new Set())

  // Fetch dashboard data with auto-refresh
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery(['dashboard'], dashboardAPI.getOverview, {
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds if enabled
  })

  const data = dashboardData || {
    projects: [],
    scans: [],
    findings: [],
    insights: [],
    reports: [],
    sessions: [],
    metrics: {},
    recentActivity: [],
  }

  const toggleWidgetExpansion = (widgetId: string) => {
    const newExpanded = new Set(expandedWidgets)
    if (newExpanded.has(widgetId)) {
      newExpanded.delete(widgetId)
    } else {
      newExpanded.add(widgetId)
    }
    setExpandedWidgets(newExpanded)
  }

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'new-project':
        navigate('/projects')
        break
      case 'new-scan':
        navigate('/scans')
        break
      case 'view-findings':
        navigate('/findings')
        break
      case 'ai-insights':
        navigate('/ai-insights')
        break
      case 'generate-report':
        navigate('/reports')
        break
      case 'manage-sessions':
        navigate('/sessions')
        break
      case 'api-testing':
        navigate('/api-testing')
        break
      default:
        break
    }
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load dashboard data: {(error as any).message}
        </Alert>
        <Button onClick={() => refetch()} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            Dashboard Overview
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive overview of your security testing activities and insights
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Quick Actions */}
      <QuickActions onAction={handleQuickAction} />

      {/* Metrics Overview */}
      <MetricsOverview
        projects={data.projects}
        scans={data.scans}
        findings={data.findings}
        insights={data.insights}
        reports={data.reports}
        sessions={data.sessions}
        isLoading={isLoading}
      />

      {/* Main Dashboard Grid */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Security Overview */}
        <Grid item xs={12} lg={8}>
          <DashboardWidget
            title="Security Overview"
            icon={<SecurityIcon />}
            expanded={expandedWidgets.has('security')}
            onToggleExpansion={() => toggleWidgetExpansion('security')}
          >
            <SecurityOverview
              findings={data.findings}
              scans={data.scans}
              isLoading={isLoading}
            />
          </DashboardWidget>
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} lg={4}>
          <DashboardWidget
            title="Performance Metrics"
            icon={<SpeedIcon />}
            expanded={expandedWidgets.has('performance')}
            onToggleExpansion={() => toggleWidgetExpansion('performance')}
          >
            <PerformanceMetrics
              scans={data.scans}
              sessions={data.sessions}
              isLoading={isLoading}
            />
          </DashboardWidget>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} lg={6}>
          <DashboardWidget
            title="Recent Activity"
            icon={<TimelineIcon />}
            expanded={expandedWidgets.has('activity')}
            onToggleExpansion={() => toggleWidgetExpansion('activity')}
          >
            <RecentActivity
              activity={data.recentActivity}
              isLoading={isLoading}
            />
          </DashboardWidget>
        </Grid>

        {/* AI Insights Summary */}
        <Grid item xs={12} lg={6}>
          <DashboardWidget
            title="AI Insights Summary"
            icon={<AIIcon />}
            expanded={expandedWidgets.has('ai-insights')}
            onToggleExpansion={() => toggleWidgetExpansion('ai-insights')}
          >
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                      {data.insights.filter(i => i.category === 'security').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Security Insights
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="warning.main" sx={{ fontWeight: 700 }}>
                      {data.insights.filter(i => i.category === 'performance').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Performance Tips
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <List dense>
                    {data.insights.slice(0, 3).map((insight, index) => (
                      <ListItem key={insight.id || index}>
                        <ListItemIcon>
                          <AIIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={insight.title}
                          secondary={insight.description}
                          primaryTypographyProps={{ variant: 'body2', fontWeight: 600 }}
                          secondaryTypographyProps={{ variant: 'caption' }}
                        />
                        <Chip
                          label={insight.category}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              </Grid>
            </Box>
          </DashboardWidget>
        </Grid>

        {/* Projects Summary */}
        <Grid item xs={12} lg={4}>
          <DashboardWidget
            title="Projects Summary"
            icon={<FolderIcon />}
            expanded={expandedWidgets.has('projects')}
            onToggleExpansion={() => toggleWidgetExpansion('projects')}
          >
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Active Projects: {data.projects.filter(p => p.status === 'active').length}
              </Typography>
              <List dense>
                {data.projects.slice(0, 5).map((project, index) => (
                  <ListItem key={project.id || index}>
                    <ListItemIcon>
                      <FolderIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={project.name}
                      secondary={`${project.scans?.length || 0} scans`}
                      primaryTypographyProps={{ variant: 'body2', fontWeight: 600 }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                    <Chip
                      label={project.status}
                      size="small"
                      color={project.status === 'active' ? 'success' : 'default'}
                      variant="outlined"
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          </DashboardWidget>
        </Grid>

        {/* Scans Status */}
        <Grid item xs={12} lg={4}>
          <DashboardWidget
            title="Scans Status"
            icon={<SearchIcon />}
            expanded={expandedWidgets.has('scans')}
            onToggleExpansion={() => toggleWidgetExpansion('scans')}
          >
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="info.main" sx={{ fontWeight: 700 }}>
                      {data.scans.filter(s => s.status === 'running').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Running
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="success.main" sx={{ fontWeight: 700 }}>
                      {data.scans.filter(s => s.status === 'completed').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Completed
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <LinearProgress
                    variant="determinate"
                    value={
                      data.scans.length > 0
                        ? (data.scans.filter(s => s.status === 'completed').length / data.scans.length) * 100
                        : 0
                    }
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Completion Rate
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </DashboardWidget>
        </Grid>

        {/* Findings Summary */}
        <Grid item xs={12} lg={4}>
          <DashboardWidget
            title="Findings Summary"
            icon={<FindingIcon />}
            expanded={expandedWidgets.has('findings')}
            onToggleExpansion={() => toggleWidgetExpansion('findings')}
          >
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="error.main" sx={{ fontWeight: 700 }}>
                      {data.findings.filter(f => f.severity === 'critical').length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Critical
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="warning.main" sx={{ fontWeight: 700 }}>
                      {data.findings.filter(f => f.severity === 'high').length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      High
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={4}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Typography variant="h4" color="info.main" sx={{ fontWeight: 700 }}>
                      {data.findings.filter(f => f.severity === 'medium').length}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Medium
                    </Typography>
                  </Card>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                    Total: {data.findings.length} findings
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </DashboardWidget>
        </Grid>
      </Grid>

      {/* Bottom Row - Full Width Widgets */}
      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12}>
          <DashboardWidget
            title="System Health & Status"
            icon={<NetworkIcon />}
            expanded={expandedWidgets.has('system-health')}
            onToggleExpansion={() => toggleWidgetExpansion('system-health')}
          >
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h6" color="success.main" sx={{ fontWeight: 700 }}>
                    Online
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Backend Status
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h6" color="success.main" sx={{ fontWeight: 700 }}>
                    {data.scans.filter(s => s.status === 'running').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Scans
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h6" color="info.main" sx={{ fontWeight: 700 }}>
                    {data.sessions.filter(s => s.status === 'active').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Sessions
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', p: 2 }}>
                  <Typography variant="h6" color="primary.main" sx={{ fontWeight: 700 }}>
                    {data.reports.filter(r => r.status === 'generating').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Reports in Progress
                  </Typography>
                </Card>
              </Grid>
            </Grid>
          </DashboardWidget>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard
