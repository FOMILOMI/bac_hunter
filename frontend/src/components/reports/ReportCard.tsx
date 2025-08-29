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
} from '@mui/material'
import {
  Assessment as ReportIcon,
  MoreVert as MoreIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { Report } from '../../types'

interface ReportCardProps {
  report: Report
  onView?: (report: Report) => void
  onEdit?: (report: Report) => void
  onDelete?: (report: Report) => void
  onDownload?: (report: Report) => void
}

const ReportCard: React.FC<ReportCardProps> = ({
  report,
  onView,
  onEdit,
  onDelete,
  onDownload
}) => {
  const theme = useTheme()
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return theme.palette.success.main
      case 'generating': return theme.palette.warning.main
      case 'failed': return theme.palette.error.main
      case 'scheduled': return theme.palette.info.main
      default: return theme.palette.text.secondary
    }
  }

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf': return <ReportIcon />
      case 'html': return <ViewIcon />
      case 'csv': return <DownloadIcon />
      case 'json': return <DownloadIcon />
      default: return <ReportIcon />
    }
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
              {getFormatIcon(report.format)}
              <Box>
                <Typography variant="h6" component="h2">
                  {report.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {report.description}
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
              label={report.status}
              sx={{ 
                bgcolor: alpha(getStatusColor(report.status), 0.1),
                color: getStatusColor(report.status)
              }}
            />
            <Chip size="small" label={report.type} variant="outlined" />
            <Chip size="small" label={report.format.toUpperCase()} variant="outlined" />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Created: {new Date(report.created_at).toLocaleDateString()}
            </Typography>
            {report.file_size && (
              <Typography variant="caption" color="text.secondary">
                Size: {(report.file_size / 1024).toFixed(1)} KB
              </Typography>
            )}
          </Box>
        </CardContent>

        <CardActions sx={{ justifyContent: 'space-between' }}>
          <Box>
            <Button
              size="small"
              startIcon={<ViewIcon />}
              onClick={() => onView?.(report)}
            >
              View
            </Button>
          </Box>
          <Box>
            {report.status === 'completed' && (
              <Button
                size="small"
                startIcon={<DownloadIcon />}
                onClick={() => onDownload?.(report)}
              >
                Download
              </Button>
            )}
          </Box>
        </CardActions>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItem onClick={() => { onView?.(report); setAnchorEl(null) }}>
            <ListItemIcon><ViewIcon /></ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
          {report.status === 'completed' && (
            <MenuItem onClick={() => { onDownload?.(report); setAnchorEl(null) }}>
              <ListItemIcon><DownloadIcon /></ListItemIcon>
              <ListItemText>Download</ListItemText>
            </MenuItem>
          )}
          <MenuItem onClick={() => { /* Share functionality */ setAnchorEl(null) }}>
            <ListItemIcon><ShareIcon /></ListItemIcon>
            <ListItemText>Share</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { onEdit?.(report); setAnchorEl(null) }}>
            <ListItemIcon><EditIcon /></ListItemIcon>
            <ListItemText>Edit</ListItemText>
          </MenuItem>
          <MenuItem 
            onClick={() => { onDelete?.(report); setAnchorEl(null) }}
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

export default ReportCard