import React, { useState } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  LinearProgress,
  Tooltip,
  useTheme,
  alpha,
  Divider,
} from '@mui/material'
import {
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  Download as ExportIcon,
  Settings as SettingsIcon,
  BugReport as FindingIcon,
  PlayArrow as ScanIcon,
  Assessment as ReportIcon,
  Schedule as ScheduleIcon,
  History as HistoryIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { Project } from '../../types'

interface ProjectCardProps {
  project: Project
  onEdit: (project: Project) => void
  onDelete: (id: string) => void
  onStartScan: (id: string) => void
  onPauseScan?: (id: string) => void
  onStopScan?: (id: string) => void
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onEdit,
  onDelete,
  onStartScan,
  onPauseScan,
  onStopScan,
}) => {
  const theme = useTheme()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation()
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleAction = (action: () => void) => {
    handleMenuClose()
    action()
  }

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'scanning':
        return <ScanIcon fontSize="small" />
      case 'completed':
        return <AssessmentIcon fontSize="small" />
      case 'failed':
        return <BugReport fontSize="small" />
      case 'paused':
        return <PauseIcon fontSize="small" />
      default:
        return <HistoryIcon fontSize="small" />
    }
  }

  const getSeverityDistribution = () => {
    // Mock data - in real implementation this would come from project findings
    return {
      critical: Math.floor(Math.random() * 5),
      high: Math.floor(Math.random() * 10),
      medium: Math.floor(Math.random() * 15),
      low: Math.floor(Math.random() * 20),
    }
  }

  const severityData = getSeverityDistribution()
  const totalFindings = Object.values(severityData).reduce((a, b) => a + b, 0)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        className="hover-lift"
        sx={{
          height: '100%',
          cursor: 'pointer',
          position: 'relative',
          overflow: 'visible',
          '&:hover': {
            borderColor: theme.palette.primary.main,
          },
        }}
        onClick={() => navigate(`/projects/${project.id}`)}
      >
        {/* Status indicator bar */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            backgroundColor: alpha(theme.palette[getStatusColor(project.status) as any]?.main || theme.palette.grey[500], 0.3),
            borderTopLeftRadius: theme.shape.borderRadius,
            borderTopRightRadius: theme.shape.borderRadius,
          }}
        />

        <CardContent sx={{ pt: 3 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  mb: 0.5,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {project.name}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  mb: 1,
                }}
              >
                {project.description || 'No description provided'}
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  display: 'block',
                  fontFamily: 'monospace',
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {project.target_url}
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={handleMenuOpen}
              sx={{ ml: 1, flexShrink: 0 }}
            >
              <MoreIcon />
            </IconButton>
          </Box>

          {/* Status and Progress */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Chip
                icon={getStatusIcon(project.status)}
                label={project.status}
                size="small"
                color={getStatusColor(project.status) as any}
                variant="outlined"
                sx={{ fontSize: '0.75rem', height: 24 }}
              />
              <Typography variant="caption" color="text.secondary">
                {new Date(project.created_at).toLocaleDateString()}
              </Typography>
            </Box>
            
            {project.status === 'scanning' && (
              <Box sx={{ mt: 1 }}>
                <LinearProgress
                  variant="indeterminate"
                  sx={{
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: theme.palette.primary.main,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Scan in progress...
                </Typography>
              </Box>
            )}
          </Box>

          {/* Statistics */}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2, mb: 2 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary.main" sx={{ fontWeight: 600 }}>
                {project.scan_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Scans
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="warning.main" sx={{ fontWeight: 600 }}>
                {project.finding_count}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Findings
              </Typography>
            </Box>
          </Box>

          {/* Severity Distribution */}
          {totalFindings > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                Severity Distribution
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {severityData.critical > 0 && (
                  <Box
                    sx={{
                      flex: severityData.critical,
                      height: 8,
                      backgroundColor: theme.palette.error.main,
                      borderRadius: 1,
                    }}
                  />
                )}
                {severityData.high > 0 && (
                  <Box
                    sx={{
                      flex: severityData.high,
                      height: 8,
                      backgroundColor: theme.palette.warning.main,
                      borderRadius: 1,
                    }}
                  />
                )}
                {severityData.medium > 0 && (
                  <Box
                    sx={{
                      flex: severityData.medium,
                      height: 8,
                      backgroundColor: theme.palette.info.main,
                      borderRadius: 1,
                    }}
                  />
                )}
                {severityData.low > 0 && (
                  <Box
                    sx={{
                      flex: severityData.low,
                      height: 8,
                      backgroundColor: theme.palette.success.main,
                      borderRadius: 1,
                    }}
                  />
                )}
              </Box>
            </Box>
          )}

          {/* Tags */}
          {project.tags && project.tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {project.tags.slice(0, 3).map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              ))}
              {project.tags.length > 3 && (
                <Chip
                  label={`+${project.tags.length - 3}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              )}
            </Box>
          )}
        </CardContent>

        {/* Actions */}
        <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
            <Tooltip title="View Details">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/projects/${project.id}`)
                }}
                sx={{ flexGrow: 1 }}
              >
                <ViewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            {project.status !== 'scanning' && (
              <Tooltip title="Start Scan">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    onStartScan(project.id)
                  }}
                  sx={{ flexGrow: 1 }}
                  color="primary"
                >
                  <StartIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            
            {project.status === 'scanning' && (
              <>
                <Tooltip title="Pause Scan">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      onPauseScan?.(project.id)
                    }}
                    sx={{ flexGrow: 1 }}
                    color="warning"
                  >
                    <PauseIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Stop Scan">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation()
                      onStopScan?.(project.id)
                    }}
                    sx={{ flexGrow: 1 }}
                    color="error"
                  >
                    <StopIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Box>
        </CardActions>

        {/* Action Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          onClick={(e) => e.stopPropagation()}
        >
          <MenuItem onClick={() => handleAction(() => navigate(`/projects/${project.id}`))}>
            <ListItemIcon>
              <ViewIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => onEdit(project))}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit Project</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/projects/${project.id}/scans`))}>
            <ListItemIcon>
              <ScanIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Manage Scans</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/projects/${project.id}/findings`))}>
            <ListItemIcon>
              <FindingIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Findings</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/projects/${project.id}/reports`))}>
            <ListItemIcon>
              <ReportIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Generate Reports</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={() => handleAction(() => navigate(`/projects/${project.id}/settings`))}>
            <ListItemIcon>
              <SettingsIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Project Settings</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/projects/${project.id}/schedule`))}>
            <ListItemIcon>
              <ScheduleIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Schedule Scans</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={() => handleAction(() => onDelete(project.id))}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText sx={{ color: 'error.main' }}>Delete Project</ListItemText>
          </MenuItem>
        </Menu>
      </Card>
    </motion.div>
  )
}

export default ProjectCard
