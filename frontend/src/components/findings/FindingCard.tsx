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
  Tooltip,
  useTheme,
  alpha,
  Divider,
  Grid,
  LinearProgress,
} from '@mui/material'
import {
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  BugReport as FindingIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as ResolvedIcon,
  Cancel as FalsePositiveIcon,
  Schedule as InProgressIcon,
  OpenInNew as ExternalIcon,
  Link as LinkIcon,
  Code as CodeIcon,
  Timeline as TimelineIcon,
  Assessment as ReportIcon,
  Download as ExportIcon,
  Share as ShareIcon,
  Flag as FlagIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

import { Finding } from '../../types'

interface FindingCardProps {
  finding: Finding
  onUpdateStatus: (id: string, status: string) => void
  onDelete: (id: string) => void
  onViewDetails: (finding: Finding) => void
}

const FindingCard: React.FC<FindingCardProps> = ({
  finding,
  onUpdateStatus,
  onDelete,
  onViewDetails,
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

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      case 'low':
        return 'success'
      case 'info':
        return 'default'
      default:
        return 'default'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <ErrorIcon fontSize="small" />
      case 'high':
        return <WarningIcon fontSize="small" />
      case 'medium':
        return <InfoIcon fontSize="small" />
      case 'low':
        return <CheckCircle fontSize="small" />
      case 'info':
        return <InfoIcon fontSize="small" />
      default:
        return <InfoIcon fontSize="small" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'error'
      case 'in_progress':
        return 'warning'
      case 'resolved':
        return 'success'
      case 'false_positive':
        return 'info'
      case 'duplicate':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'open':
        return <SecurityIcon fontSize="small" />
      case 'in_progress':
        return <InProgressIcon fontSize="small" />
      case 'resolved':
        return <ResolvedIcon fontSize="small" />
      case 'false_positive':
        return <FalsePositiveIcon fontSize="small" />
      case 'duplicate':
        return <FlagIcon fontSize="small" />
      default:
        return <SecurityIcon fontSize="small" />
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'sql_injection':
        return <CodeIcon />
      case 'xss':
        return <CodeIcon />
      case 'csrf':
        return <SecurityIcon />
      case 'authentication':
        return <SecurityIcon />
      case 'authorization':
        return <SecurityIcon />
      case 'information_disclosure':
        return <InfoIcon />
      case 'business_logic':
        return <TimelineIcon />
      default:
        return <FindingIcon />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'sql_injection':
        return 'error'
      case 'xss':
        return 'warning'
      case 'csrf':
        return 'info'
      case 'authentication':
        return 'primary'
      case 'authorization':
        return 'secondary'
      case 'information_disclosure':
        return 'info'
      case 'business_logic':
        return 'warning'
      default:
        return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const truncateText = (text: string, maxLength: number) => {
    if (!text) return ''
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
  }

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
          border: 2,
          borderColor: alpha(theme.palette[getSeverityColor(finding.severity) as any]?.main || theme.palette.grey[500], 0.3),
          '&:hover': {
            borderColor: theme.palette[getSeverityColor(finding.severity) as any]?.main || theme.palette.grey[500],
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows[8],
          },
          transition: 'all 0.3s ease',
        }}
        onClick={() => onViewDetails(finding)}
      >
        {/* Severity indicator bar */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 4,
            backgroundColor: theme.palette[getSeverityColor(finding.severity) as any]?.main || theme.palette.grey[500],
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
                {finding.title || `Finding ${finding.id}`}
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
                {truncateText(finding.description || 'No description available', 80)}
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

          {/* Severity and Status */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                icon={getSeverityIcon(finding.severity)}
                label={finding.severity}
                size="small"
                color={getSeverityColor(finding.severity) as any}
                variant="outlined"
                sx={{ fontSize: '0.75rem', height: 24 }}
              />
              <Chip
                icon={getStatusIcon(finding.status)}
                label={finding.status?.replace('_', ' ') || 'unknown'}
                size="small"
                color={getStatusColor(finding.status) as any}
                variant="outlined"
                sx={{ fontSize: '0.75rem', height: 24 }}
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              {finding.created_at ? formatDate(finding.created_at) : 'Unknown date'}
            </Typography>
          </Box>

          {/* Finding Information */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    backgroundColor: alpha(theme.palette[getTypeColor(finding.type) as any]?.main || theme.palette.grey[500], 0.1),
                    color: theme.palette[getTypeColor(finding.type) as any]?.main || theme.palette.grey[500],
                    mx: 'auto',
                    mb: 0.5,
                  }}
                >
                  {getTypeIcon(finding.type)}
                </Avatar>
                <Typography variant="caption" color="text.secondary">
                  {finding.type?.replace('_', ' ') || 'Unknown'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="warning.main" sx={{ fontWeight: 600 }}>
                  {finding.cvss_score || 'N/A'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  CVSS Score
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Finding Details */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Finding Details
            </Typography>
            <Grid container spacing={1}>
              {finding.parameter && (
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">
                    Parameter:
                  </Typography>
                  <Typography variant="caption" sx={{ ml: 0.5, fontFamily: 'monospace' }}>
                    {finding.parameter}
                  </Typography>
                </Grid>
              )}
              {finding.url && (
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">
                    URL:
                  </Typography>
                  <Typography variant="caption" sx={{ ml: 0.5, fontFamily: 'monospace' }}>
                    {truncateText(finding.url, 50)}
                  </Typography>
                </Grid>
              )}
              {finding.method && (
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Method:
                  </Typography>
                  <Typography variant="caption" sx={{ ml: 0.5 }}>
                    {finding.method}
                  </Typography>
                </Grid>
              )}
              {finding.status_code && (
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Status:
                  </Typography>
                  <Typography variant="caption" sx={{ ml: 0.5 }}>
                    {finding.status_code}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Box>

          {/* Evidence Preview */}
          {finding.evidence && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                Evidence Preview
              </Typography>
              <Paper
                sx={{
                  p: 1,
                  backgroundColor: alpha(theme.palette.grey[900], 0.1),
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  maxHeight: 60,
                  overflow: 'hidden',
                }}
              >
                {truncateText(finding.evidence, 100)}
              </Paper>
            </Box>
          )}

          {/* Tags */}
          {finding.tags && finding.tags.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
              {finding.tags.slice(0, 3).map((tag, index) => (
                <Chip
                  key={index}
                  label={tag}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              ))}
              {finding.tags.length > 3 && (
                <Chip
                  label={`+${finding.tags.length - 3}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.65rem', height: 20 }}
                />
              )}
            </Box>
          )}

          {/* Risk Level Indicator */}
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Risk Level
              </Typography>
              <Typography variant="caption" sx={{ fontWeight: 600 }}>
                {finding.risk_level || 'Unknown'}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={finding.risk_score || 0}
              sx={{
                height: 4,
                borderRadius: 2,
                backgroundColor: alpha(theme.palette[getSeverityColor(finding.severity) as any]?.main || theme.palette.grey[500], 0.2),
                '& .MuiLinearProgress-bar': {
                  backgroundColor: theme.palette[getSeverityColor(finding.severity) as any]?.main || theme.palette.grey[500],
                  borderRadius: 2,
                },
              }}
            />
          </Box>
        </CardContent>

        {/* Actions */}
        <CardActions sx={{ pt: 0, px: 2, pb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, width: '100%' }}>
            <Tooltip title="View Details">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  onViewDetails(finding)
                }}
                sx={{ flexGrow: 1 }}
              >
                <ViewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Mark as In Progress">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  onUpdateStatus(finding.id, 'in_progress')
                }}
                sx={{ flexGrow: 1 }}
                color="warning"
              >
                <InProgressIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Mark as Resolved">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  onUpdateStatus(finding.id, 'resolved')
                }}
                sx={{ flexGrow: 1 }}
                color="success"
              >
                <ResolvedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Mark as False Positive">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation()
                  onUpdateStatus(finding.id, 'false_positive')
                }}
                sx={{ flexGrow: 1 }}
                color="info"
              >
                <FalsePositiveIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </CardActions>

        {/* Action Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          onClick={(e) => e.stopPropagation()}
        >
          <MenuItem onClick={() => handleAction(() => onViewDetails(finding))}>
            <ListItemIcon>
              <ViewIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/findings/${finding.id}/edit`))}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit Finding</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/findings/${finding.id}/timeline`))}>
            <ListItemIcon>
              <TimelineIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Timeline</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => navigate(`/findings/${finding.id}/report`))}>
            <ListItemIcon>
              <ReportIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Generate Report</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={() => handleAction(() => window.open(finding.url, '_blank'))}>
            <ListItemIcon>
              <ExternalIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Open URL</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => {})}>
            <ListItemIcon>
              <ShareIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Share Finding</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={() => handleAction(() => {})}>
            <ListItemIcon>
              <ExportIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Export</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={() => handleAction(() => onDelete(finding.id))}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText sx={{ color: 'error.main' }}>Delete Finding</ListItemText>
          </MenuItem>
        </Menu>
      </Card>
    </motion.div>
  )
}

export default FindingCard
