import React, { useEffect, useState } from 'react'
import { useQuery } from 'react-query'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  useTheme,
  alpha,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Psychology as AIIcon,
  Refresh as RefreshIcon,
  Launch as LaunchIcon,
  BugReport as BugIcon,
  PlayArrow as ScanIcon,
  FolderOpen as ProjectIcon,
  Timeline as TimelineIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

import { dashboardAPI, projectsAPI } from '../services/api'
import { useDashboardStore, useProjectsStore } from '../store'
import StatsCard from '../components/dashboard/StatsCard'
import SeverityChart from '../components/dashboard/SeverityChart'
import TrendChart from '../components/dashboard/TrendChart'
import ActivityTimeline from '../components/dashboard/ActivityTimeline'
import ProjectsOverview from '../components/dashboard/ProjectsOverview'
import ScanProgress from '../components/dashboard/ScanProgress'
import AIInsightsWidget from '../components/dashboard/AIInsightsWidget'
import QuickActions from '../components/dashboard/QuickActions'
import SystemHealth from '../components/dashboard/SystemHealth'
import RecentFindings from '../components/dashboard/RecentFindings'

const Dashboard: React.FC = () => {
  const theme = useTheme()
  const [refreshKey, setRefreshKey] = useState(0)
  
  const { stats, setStats, setLoading, setError } = useDashboardStore()
  const { projects, setProjects } = useProjectsStore()

  // Fetch dashboard stats
  const { data: statsData, isLoading: statsLoading, error: statsError } = useQuery(
    ['dashboard-stats', refreshKey],
    dashboardAPI.getStats,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      onSuccess: (data) => {
        setStats(data)
        setError(null)
      },
      onError: (error: any) => {
        setError(error.message)
      },
    }
  )

  // Fetch projects for overview
  const { data: projectsData } = useQuery(
    ['projects-overview', refreshKey],
    projectsAPI.getAll,
    {
      refetchInterval: 60000, // Refresh every minute
      onSuccess: (data) => {
        setProjects(data.projects)
      },
    }
  )

  // Fetch activity data
  const { data: activityData } = useQuery(
    ['dashboard-activity', refreshKey],
    dashboardAPI.getActivity,
    {
      refetchInterval: 30000,
    }
  )

  useEffect(() => {
    setLoading(statsLoading)
  }, [statsLoading, setLoading])

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  const mockStats = {
    total_projects: projects?.length || 0,
    active_scans: 2,
    total_findings: 47,
    critical_findings: 3,
    high_findings: 12,
    medium_findings: 18,
    low_findings: 14,
    ai_insights_count: 23,
    scan_success_rate: 94.5,
    average_scan_duration: 12.3,
    recent_activity: activityData || [],
  }

  const currentStats = stats || mockStats

  return (
    <Box sx={{ minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            Security Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time overview of your security testing activities
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Refresh data">
            <IconButton onClick={handleRefresh} disabled={statsLoading}>
              <RefreshIcon className={statsLoading ? 'spin' : ''} />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<LaunchIcon />}
            href="/projects"
            sx={{ ml: 1 }}
          >
            New Project
          </Button>
        </Box>
      </Box>

      {/* Loading indicator */}
      {statsLoading && (
        <LinearProgress sx={{ mb: 2, borderRadius: 1 }} />
      )}

      <Grid container spacing={3}>
        {/* Stats Cards Row */}
        <Grid item xs={12}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <StatsCard
                  title="Total Projects"
                  value={currentStats.total_projects}
                  icon={<ProjectIcon />}
                  color="primary"
                  trend={{ value: 12, direction: 'up' }}
                />
              </motion.div>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <StatsCard
                  title="Active Scans"
                  value={currentStats.active_scans}
                  icon={<ScanIcon />}
                  color="info"
                  trend={{ value: 3, direction: 'up' }}
                />
              </motion.div>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <StatsCard
                  title="Total Findings"
                  value={currentStats.total_findings}
                  icon={<BugIcon />}
                  color="warning"
                  trend={{ value: 8, direction: 'up' }}
                />
              </motion.div>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
              >
                <StatsCard
                  title="AI Insights"
                  value={currentStats.ai_insights_count}
                  icon={<AIIcon />}
                  color="secondary"
                  trend={{ value: 15, direction: 'up' }}
                />
              </motion.div>
            </Grid>
          </Grid>
        </Grid>

        {/* Critical Findings Alert */}
        {currentStats.critical_findings > 0 && (
          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
            >
              <Card
                sx={{
                  background: `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.1)} 0%, ${alpha(theme.palette.error.main, 0.05)} 100%)`,
                  border: `1px solid ${alpha(theme.palette.error.main, 0.3)}`,
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar sx={{ bgcolor: 'error.main' }}>
                      <SecurityIcon />
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" color="error.main" sx={{ fontWeight: 600 }}>
                        Critical Security Issues Detected
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {currentStats.critical_findings} critical vulnerabilities require immediate attention
                      </Typography>
                    </Box>
                    <Button
                      variant="contained"
                      color="error"
                      href="/findings?severity=critical"
                      endIcon={<LaunchIcon />}
                    >
                      Review Now
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        )}

        {/* Charts Row */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <SeverityChart
              data={{
                critical: currentStats.critical_findings,
                high: currentStats.high_findings,
                medium: currentStats.medium_findings,
                low: currentStats.low_findings,
              }}
            />
          </motion.div>
        </Grid>

        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
          >
            <TrendChart />
          </motion.div>
        </Grid>

        {/* System Health and Performance */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
          >
            <SystemHealth
              successRate={currentStats.scan_success_rate}
              avgDuration={currentStats.average_scan_duration}
            />
          </motion.div>
        </Grid>

        {/* AI Insights Widget */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
          >
            <AIInsightsWidget />
          </motion.div>
        </Grid>

        {/* Projects Overview */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
          >
            <ProjectsOverview projects={projects || []} />
          </motion.div>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.1 }}
          >
            <QuickActions />
          </motion.div>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 }}
          >
            <ActivityTimeline activities={currentStats.recent_activity} />
          </motion.div>
        </Grid>

        {/* Recent Findings */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.3 }}
          >
            <RecentFindings />
          </motion.div>
        </Grid>

        {/* Scan Progress (if any active scans) */}
        {currentStats.active_scans > 0 && (
          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.4 }}
            >
              <ScanProgress />
            </motion.div>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

export default Dashboard
