import React from 'react'
import { Box, Chip, Tooltip, useTheme } from '@mui/material'
import {
  CheckCircle,
  Error,
  Warning,
  Help,
  SignalCellular4Bar,
  SignalCellularConnectedNoInternet4Bar,
  SignalCellular0Bar
} from '@mui/icons-material'

export interface StatusIndicatorProps {
  status: string
  size?: 'small' | 'medium' | 'large'
  showLabel?: boolean
  variant?: 'chip' | 'icon' | 'both'
  className?: string
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  size = 'medium',
  showLabel = true,
  variant = 'both',
  className
}) => {
  const theme = useTheme()
  
  // Normalize status to lowercase for consistent comparison
  const normalizedStatus = status.toLowerCase()
  
  // Get status configuration
  const getStatusConfig = () => {
    switch (normalizedStatus) {
      case 'healthy':
      case 'operational':
      case 'connected':
      case 'active':
      case 'running':
      case 'completed':
      case 'success':
        return {
          icon: CheckCircle,
          color: theme.palette.success.main,
          bgColor: theme.palette.success.light,
          label: 'Healthy',
          description: 'System is operating normally'
        }
      
      case 'warning':
      case 'degraded':
      case 'partial':
      case 'pending':
      case 'queued':
        return {
          icon: Warning,
          color: theme.palette.warning.main,
          bgColor: theme.palette.warning.light,
          label: 'Warning',
          description: 'System has minor issues'
        }
      
      case 'error':
      case 'failed':
      case 'disconnected':
      case 'inactive':
      case 'stopped':
      case 'crashed':
        return {
          icon: Error,
          color: theme.palette.error.main,
          bgColor: theme.palette.error.light,
          label: 'Error',
          description: 'System has critical issues'
        }
      
      case 'unknown':
      case 'unavailable':
      case 'n/a':
      case 'none':
        return {
          icon: Help,
          color: theme.palette.grey[500],
          bgColor: theme.palette.grey[100],
          label: 'Unknown',
          description: 'Status is unknown or unavailable'
        }
      
      case 'connecting':
      case 'starting':
      case 'initializing':
        return {
          icon: SignalCellular4Bar,
          color: theme.palette.info.main,
          bgColor: theme.palette.info.light,
          label: 'Connecting',
          description: 'System is establishing connection'
        }
      
      case 'disconnected':
      case 'offline':
      case 'no_connection':
        return {
          icon: SignalCellular0Bar,
          color: theme.palette.grey[600],
          bgColor: theme.palette.grey[200],
          label: 'Disconnected',
          description: 'No network connection'
        }
      
      case 'poor_connection':
      case 'unstable':
        return {
          icon: SignalCellularConnectedNoInternet4Bar,
          color: theme.palette.warning.dark,
          bgColor: theme.palette.warning.light,
          label: 'Poor Connection',
          description: 'Connection is unstable'
        }
      
      default:
        // Try to match partial status strings
        if (normalizedStatus.includes('healthy') || normalizedStatus.includes('good')) {
          return {
            icon: CheckCircle,
            color: theme.palette.success.main,
            bgColor: theme.palette.success.light,
            label: 'Healthy',
            description: 'System is operating normally'
          }
        } else if (normalizedStatus.includes('error') || normalizedStatus.includes('fail')) {
          return {
            icon: Error,
            color: theme.palette.error.main,
            bgColor: theme.palette.error.light,
            label: 'Error',
            description: 'System has critical issues'
          }
        } else if (normalizedStatus.includes('warn') || normalizedStatus.includes('degraded')) {
          return {
            icon: Warning,
            color: theme.palette.warning.main,
            bgColor: theme.palette.warning.light,
            label: 'Warning',
            description: 'System has minor issues'
          }
        } else {
          return {
            icon: Help,
            color: theme.palette.grey[500],
            bgColor: theme.palette.grey[100],
            label: normalizedStatus.charAt(0).toUpperCase() + normalizedStatus.slice(1),
            description: `Status: ${status}`
          }
        }
    }
  }
  
  const statusConfig = getStatusConfig()
  const IconComponent = statusConfig.icon
  
  // Size configurations
  const getSizeConfig = () => {
    switch (size) {
      case 'small':
        return {
          iconSize: 16,
          chipHeight: 24,
          fontSize: '0.75rem'
        }
      case 'large':
        return {
          iconSize: 32,
          chipHeight: 40,
          fontSize: '1rem'
        }
      default: // medium
        return {
          iconSize: 24,
          chipHeight: 32,
          fontSize: '0.875rem'
        }
    }
  }
  
  const sizeConfig = getSizeConfig()
  
  // Render based on variant
  if (variant === 'icon') {
    return (
      <Tooltip title={statusConfig.description} arrow>
        <Box
          className={className}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: sizeConfig.iconSize + 8,
            height: sizeConfig.iconSize + 8,
            borderRadius: '50%',
            backgroundColor: statusConfig.bgColor,
            color: statusConfig.color
          }}
        >
          <IconComponent sx={{ fontSize: sizeConfig.iconSize }} />
        </Box>
      </Tooltip>
    )
  }
  
  if (variant === 'chip') {
    return (
      <Tooltip title={statusConfig.description} arrow>
        <Chip
          className={className}
          icon={<IconComponent sx={{ fontSize: sizeConfig.iconSize - 4 }} />}
          label={showLabel ? statusConfig.label : ''}
          size={size === 'small' ? 'small' : 'medium'}
          sx={{
            height: sizeConfig.chipHeight,
            fontSize: sizeConfig.fontSize,
            backgroundColor: statusConfig.bgColor,
            color: statusConfig.color,
            border: `1px solid ${statusConfig.color}`,
            '& .MuiChip-icon': {
              color: statusConfig.color
            }
          }}
        />
      </Tooltip>
    )
  }
  
  // Default: both icon and chip
  return (
    <Tooltip title={statusConfig.description} arrow>
      <Box
        className={className}
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 1
        }}
      >
        <Box
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: sizeConfig.iconSize + 4,
            height: sizeConfig.iconSize + 4,
            borderRadius: '50%',
            backgroundColor: statusConfig.bgColor,
            color: statusConfig.color
          }}
        >
          <IconComponent sx={{ fontSize: sizeConfig.iconSize }} />
        </Box>
        
        {showLabel && (
          <Box
            component="span"
            sx={{
              fontSize: sizeConfig.fontSize,
              color: statusConfig.color,
              fontWeight: 500
            }}
          >
            {statusConfig.label}
          </Box>
        )}
      </Box>
    </Tooltip>
  )
}

export default StatusIndicator
