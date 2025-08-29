import React from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  Chip,
  Avatar,
  LinearProgress,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Launch as LaunchIcon,
  MoreVert as MoreIcon,
  PlayArrow as ScanIcon,
  BugReport as FindingIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { Project } from '../../types'

interface ProjectsOverviewProps {
  projects: Project[]
}

const ProjectsOverview: React.FC<ProjectsOverviewProps> = ({ projects = [] }) => {
  const navigate = useNavigate()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'scanning':
        return 'primary'
      case 'failed':
        return 'error'
      case 'paused':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getStatusProgress = (status: string) => {
    switch (status) {
      case 'completed':
        return 100
      case 'scanning':
        return 65 // Mock progress
      case 'failed':
        return 0
      case 'paused':
        return 45
      default:
        return 0
    }
  }

  const recentProjects = projects.slice(0, 4)

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Recent Projects"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        action={
          <Button
            size="small"
            endIcon={<LaunchIcon />}
            onClick={() => navigate('/projects')}
          >
            View All
          </Button>
        }
      />
      <CardContent sx={{ pt: 0 }}>
        {recentProjects.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              No projects yet
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/projects')}
              startIcon={<LaunchIcon />}
            >
              Create First Project
            </Button>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {recentProjects.map((project) => (
              <Box
                key={project.id}
                sx={{
                  p: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 2,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'action.hover',
                  },
                }}
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexGrow: 1 }}>
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor: 'primary.main',
                        fontSize: '0.875rem',
                      }}
                    >
                      {project.name.charAt(0).toUpperCase()}
                    </Avatar>
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {project.name}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {project.target_url}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={project.status}
                      size="small"
                      color={getStatusColor(project.status) as any}
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                    <Tooltip title="More options">
                      <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                        <MoreIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                {project.status === 'scanning' && (
                  <LinearProgress
                    variant="determinate"
                    value={getStatusProgress(project.status)}
                    sx={{
                      mb: 1,
                      height: 4,
                      borderRadius: 2,
                      backgroundColor: 'action.hover',
                    }}
                  />
                )}

                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ScanIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {project.scan_count} scans
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <FindingIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">
                        {project.finding_count} findings
                      </Typography>
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(project.created_at).toLocaleDateString()}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

export default ProjectsOverview
