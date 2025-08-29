import React from 'react'
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  Skeleton
} from '@mui/material'
import {
  Visibility,
  BugReport,
  Security,
  Warning,
  Info,
  Error
} from '@mui/icons-material'
import { motion } from 'framer-motion'

interface Finding {
  id: number
  type: string
  severity: string
  url: string
  target: string
  created_at: string
}

interface RecentFindingsTableProps {
  findings: Finding[]
  className?: string
}

const RecentFindingsTable: React.FC<RecentFindingsTableProps> = ({ findings, className }) => {
  const theme = useTheme()
  
  // Get severity configuration
  const getSeverityConfig = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return {
          icon: Error,
          color: theme.palette.error.main,
          bgColor: theme.palette.error.light,
          label: 'Critical'
        }
      case 'high':
        return {
          icon: Error,
          color: theme.palette.error.dark,
          bgColor: theme.palette.error.light,
          label: 'High'
        }
      case 'medium':
        return {
          icon: Warning,
          color: theme.palette.warning.main,
          bgColor: theme.palette.warning.light,
          label: 'Medium'
        }
      case 'low':
        return {
          icon: Info,
          color: theme.palette.info.main,
          bgColor: theme.palette.info.light,
          label: 'Low'
        }
      default:
        return {
          icon: Info,
          color: theme.palette.grey[500],
          bgColor: theme.palette.grey[100],
          label: severity
        }
    }
  }
  
  // Get finding type icon
  const getFindingTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'idor':
      case 'broken_access_control':
        return <Security />
      case 'vulnerability':
      case 'security_issue':
        return <BugReport />
      default:
        return <Info />
    }
  }
  
  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 60) {
      return `${diffMins}m ago`
    } else if (diffHours < 24) {
      return `${diffHours}h ago`
    } else {
      return `${diffDays}d ago`
    }
  }
  
  // Truncate URL for display
  const truncateUrl = (url: string, maxLength: number = 50) => {
    if (url.length <= maxLength) return url
    return url.substring(0, maxLength) + '...'
  }
  
  // Handle finding click
  const handleFindingClick = (findingId: number) => {
    window.location.href = `/findings/${findingId}`
  }
  
  // Loading state
  if (findings.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          No findings available
        </Typography>
      </Box>
    )
  }
  
  return (
    <TableContainer component={Paper} variant="outlined" className={className}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 'bold' }}>Type</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Severity</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>URL</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Target</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Discovered</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {findings.map((finding, index) => {
            const severityConfig = getSeverityConfig(finding.severity)
            const SeverityIcon = severityConfig.icon
            
            return (
              <motion.tr
                key={finding.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                component={TableRow}
                sx={{
                  '&:hover': {
                    backgroundColor: theme.palette.action.hover,
                    cursor: 'pointer'
                  }
                }}
                onClick={() => handleFindingClick(finding.id)}
              >
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getFindingTypeIcon(finding.type)}
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {finding.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Typography>
                  </Box>
                </TableCell>
                
                <TableCell>
                  <Chip
                    icon={<SeverityIcon />}
                    label={severityConfig.label}
                    size="small"
                    sx={{
                      backgroundColor: severityConfig.bgColor,
                      color: severityConfig.color,
                      fontWeight: 'bold',
                      '& .MuiChip-icon': {
                        color: severityConfig.color
                      }
                    }}
                  />
                </TableCell>
                
                <TableCell>
                  <Tooltip title={finding.url} arrow>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {truncateUrl(finding.url)}
                    </Typography>
                  </Tooltip>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {finding.target}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(finding.created_at)}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Tooltip title="View Details" arrow>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleFindingClick(finding.id)
                      }}
                      sx={{
                        color: theme.palette.primary.main,
                        '&:hover': {
                          backgroundColor: `${theme.palette.primary.main}10`
                        }
                      }}
                    >
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </motion.tr>
            )
          })}
        </TableBody>
      </Table>
    </TableContainer>
  )
}

export default RecentFindingsTable