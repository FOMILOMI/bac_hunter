import React from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Box,
  useTheme,
  alpha,
  LinearProgress,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Replay as ReplayIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { Session } from '../../types'

interface SessionCardProps {
  session: Session
  onView?: (session: Session) => void
  onEdit?: (session: Session) => void
  onDelete?: (session: Session) => void
  onReplay?: (session: Session) => void
}

const SessionCard: React.FC<SessionCardProps> = ({
  session,
  onView,
  onEdit,
  onDelete,
  onReplay
}) => {
  const theme = useTheme()
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return theme.palette.success.main
      case 'running': return theme.palette.primary.main
      case 'failed': return theme.palette.error.main
      case 'stopped': return theme.palette.warning.main
      default: return theme.palette.text.secondary
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon />
      case 'running': return <PlayIcon />
      case 'failed': return <DeleteIcon />
      default: return <TimelineIcon />
    }
  }

  const getDuration = () => {
    if (session.start_time && session.end_time) {
      const duration = new Date(session.end_time).getTime() - new Date(session.start_time).getTime()
      return Math.round(duration / 1000 / 60) // minutes
    }
    return session.duration ? Math.round(session.duration / 60) : 0
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <Card 
        sx={{ 
          mb: 2,
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: theme.shadows[4],
            transform: 'translateY(-2px)'
          }
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {getStatusIcon(session.status)}
              <Box>
                <Typography variant="h6" component="h2">
                  {session.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {session.type} session
                </Typography>
              </Box>
            </Box>
            <IconButton
              size="small"
              onClick={(e) => setAnchorEl(e.currentTarget)}
            >
              <MoreIcon />
            </IconButton>
          </Box>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            <Chip 
              size="small" 
              label={session.status}
              sx={{ 
                bgcolor: alpha(getStatusColor(session.status), 0.1),
                color: getStatusColor(session.status)
              }}
            />
            <Chip size="small" label={session.type} variant="outlined" />
            <Chip size="small" label={`${getDuration()} min`} variant="outlined" />
          </Box>

          {/* Progress bar for running sessions */}
          {session.status === 'running' && (
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="caption">Progress</Typography>
                <Typography variant="caption">{session.progress || 0}%</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={session.progress || 0} 
                sx={{ height: 6, borderRadius: 3 }}
              />
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              {session.start_time && `Started: ${new Date(session.start_time).toLocaleString()}`}
            </Typography>
            {session.requests_count && (
              <Typography variant="caption" color="text.secondary">
                {session.requests_count} requests
              </Typography>
            )}
          </Box>
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between' }}>
          <Box>
            <Button
              size="small"
              startIcon={<ViewIcon />}
              onClick={() => onView?.(session)}
            >
              View
            </Button>
          </Box>
          <Box>
            {session.status === 'completed' && (
              <Button
                size="small"
                startIcon={<ReplayIcon />}
                onClick={() => onReplay?.(session)}
              >
                Replay
              </Button>
            )}
          </Box>
        </CardActions>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItem onClick={() => { onView?.(session); setAnchorEl(null) }}>
            <ListItemIcon><ViewIcon /></ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
          
          {session.status === 'completed' && (
            <MenuItem onClick={() => { onReplay?.(session); setAnchorEl(null) }}>
              <ListItemIcon><ReplayIcon /></ListItemIcon>
              <ListItemText>Replay Session</ListItemText>
            </MenuItem>
          )}
          
          <MenuItem onClick={() => { onEdit?.(session); setAnchorEl(null) }}>
            <ListItemIcon><EditIcon /></ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          
          <MenuItem 
            onClick={() => { onDelete?.(session); setAnchorEl(null) }}
            sx={{ color: theme.palette.error.main }}
          >
            <ListItemIcon><DeleteIcon sx={{ color: theme.palette.error.main }} /></ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </Menu>
      </Card>
    </motion.div>
  )
}

export default SessionCard