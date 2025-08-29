import React, { useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  useTheme,
  alpha,
  Tooltip,
  LinearProgress,
} from '@mui/material'
import {
  FolderOpen as ProjectIcon,
  PlayArrow as ActiveIcon,
  CheckCircle as CompletedIcon,
  Error as FailedIcon,
  Pause as PausedIcon,
  BugReport as FindingIcon,
  Security as SecurityIcon,
  TrendingUp as TrendIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

import { Project } from '../../types'

interface ProjectStatsProps {
  projects: Project[]
}

const ProjectStats: React.FC<ProjectStatsProps> = ({ projects }) => {
  const theme = useTheme()

  const stats = useMemo(() => {
    const totalProjects = projects.length
    const activeProjects = projects.filter(p => p.status === 'scanning').length
    const completedProjects = projects.filter(p => p.status === 'completed').length
    const failedProjects = projects.filter(p => p.status === 'failed').length
    const pausedProjects = projects.filter(p => p.status === 'paused').length
    
    const totalFindings = projects.reduce((sum, p) => sum + (p.finding_count || 0), 0)
    const totalScans = projects.reduce((sum, p) => sum + (p.scan_count || 0), 0)
    
    const avgFindingsPerProject = totalProjects > 0 ? (totalFindings / totalProjects).toFixed(1) : 0
    const avgScansPerProject = totalProjects > 0 ? (totalScans / totalProjects).toFixed(1) : 0
    
    const completionRate = totalProjects > 0 ? ((completedProjects / totalProjects) * 100).toFixed(1) : 0
    const successRate = totalProjects > 0 ? (((completedProjects + activeProjects) / totalProjects) * 100).toFixed(1) : 0

    return {
      totalProjects,
      activeProjects,
      completedProjects,
      failedProjects,
      pausedProjects,
      totalFindings,
      totalScans,
      avgFindingsPerProject,
      avgScansPerProject,
      completionRate,
      successRate,
    }
  }, [projects])

  const statCards = [
    {
      title: 'Total Projects',
      value: stats.totalProjects,
      icon: ProjectIcon,
      color: 'primary',
      description: 'All projects in the system',
      trend: null,
    },
    {
      title: 'Active Scans',
      value: stats.activeProjects,
      icon: ActiveIcon,
      color: 'info',
      description: 'Currently running scans',
      trend: stats.activeProjects > 0 ? 'up' : 'stable',
    },
    {
      title: 'Completed',
      value: stats.completedProjects,
      icon: CompletedIcon,
      color: 'success',
      description: 'Successfully completed scans',
      trend: 'up',
    },
    {
      title: 'Failed',
      value: stats.failedProjects,
      icon: FailedIcon,
      color: 'error',
      description: 'Failed or errored scans',
      trend: stats.failedProjects > 0 ? 'down' : 'stable',
    },
    {
      title: 'Total Findings',
      value: stats.totalFindings,
      icon: FindingIcon,
      color: 'warning',
      description: 'Security vulnerabilities found',
      trend: stats.totalFindings > 0 ? 'up' : 'stable',
    },
    {
      title: 'Total Scans',
      value: stats.totalScans,
      icon: SecurityIcon,
      color: 'secondary',
      description: 'All scan executions',
      trend: 'up',
    },
  ]

  const getTrendIcon = (trend: string | null) => {
    if (!trend) return null
    return (
      <TrendIcon
        sx={{
          fontSize: '1rem',
          color: trend === 'up' ? 'success.main' : trend === 'down' ? 'error.main' : 'text.secondary',
          transform: trend === 'down' ? 'rotate(180deg)' : 'none',
        }}
      />
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scanning':
        return theme.palette.info.main
      case 'completed':
        return theme.palette.success.main
      case 'failed':
        return theme.palette.error.main
      case 'paused':
        return theme.palette.warning.main
      default:
        return theme.palette.grey[500]
    }
  }

  return (
    <Box sx={{ mb: 3 }}>
      {/* Main Stats Grid */}
      <Grid container spacing={3}>
        {statCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={stat.title}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card
                sx={{
                  height: '100%',
                  position: 'relative',
                  overflow: 'visible',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: theme.shadows[8],
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <CardContent sx={{ p: 2.5, textAlign: 'center' }}>
                  {/* Icon */}
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: alpha(theme.palette[stat.color as any]?.main || theme.palette.primary.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      margin: '0 auto 1rem',
                      color: theme.palette[stat.color as any]?.main || theme.palette.primary.main,
                    }}
                  >
                    <stat.icon sx={{ fontSize: '1.5rem' }} />
                  </Box>

                  {/* Value */}
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {stat.value.toLocaleString()}
                  </Typography>

                  {/* Title */}
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                    {stat.title}
                  </Typography>

                  {/* Description */}
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    {stat.description}
                  </Typography>

                  {/* Trend Indicator */}
                  {stat.trend && (
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                      {getTrendIcon(stat.trend)}
                      <Typography variant="caption" color="text.secondary">
                        {stat.trend === 'up' ? 'Trending up' : stat.trend === 'down' ? 'Trending down' : 'Stable'}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* Progress Metrics */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CompletedIcon color="success" />
                Completion Rate
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h4" color="success.main" sx={{ fontWeight: 700 }}>
                  {stats.completionRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  of projects completed successfully
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={parseFloat(stats.completionRate)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: alpha(theme.palette.success.main, 0.2),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: theme.palette.success.main,
                    borderRadius: 4,
                  },
                }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendIcon color="primary" />
                Success Rate
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h4" color="primary.main" sx={{ fontWeight: 700 }}>
                  {stats.successRate}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  of projects running or completed
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={parseFloat(stats.successRate)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: theme.palette.primary.main,
                    borderRadius: 4,
                  },
                }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Status Distribution */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Project Status Distribution
          </Typography>
          <Grid container spacing={2}>
            {[
              { status: 'scanning', label: 'Scanning', count: stats.activeProjects, color: 'info' },
              { status: 'completed', label: 'Completed', count: stats.completedProjects, color: 'success' },
              { status: 'failed', label: 'Failed', count: stats.failedProjects, color: 'error' },
              { status: 'paused', label: 'Paused', count: stats.pausedProjects, color: 'warning' },
            ].map((item) => (
              <Grid item xs={12} sm={6} md={3} key={item.status}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: getStatusColor(item.status),
                    }}
                  />
                  <Typography variant="body2" sx={{ flexGrow: 1 }}>
                    {item.label}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {item.count}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ({stats.totalProjects > 0 ? ((item.count / stats.totalProjects) * 100).toFixed(1) : 0}%)
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Averages */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Average Metrics
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Findings per Project
                  </Typography>
                  <Typography variant="h5" color="warning.main" sx={{ fontWeight: 600 }}>
                    {stats.avgFindingsPerProject}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Scans per Project
                  </Typography>
                  <Typography variant="h5" color="secondary.main" sx={{ fontWeight: 600 }}>
                    {stats.avgScansPerProject}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Recent Activity
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Active Scans
                  </Typography>
                  <Typography variant="h5" color="info.main" sx={{ fontWeight: 600 }}>
                    {stats.activeProjects}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Paused
                  </Typography>
                  <Typography variant="h5" color="warning.main" sx={{ fontWeight: 600 }}>
                    {stats.pausedProjects}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default ProjectStats
