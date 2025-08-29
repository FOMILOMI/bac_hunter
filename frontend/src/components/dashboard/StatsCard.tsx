import React from 'react'
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  useTheme,
  alpha,
} from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material'

interface StatsCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  color: 'primary' | 'secondary' | 'info' | 'warning' | 'error' | 'success'
  trend?: {
    value: number
    direction: 'up' | 'down'
    period?: string
  }
  subtitle?: string
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  color,
  trend,
  subtitle,
}) => {
  const theme = useTheme()

  const colorMap = {
    primary: theme.palette.primary.main,
    secondary: theme.palette.secondary.main,
    info: theme.palette.info.main,
    warning: theme.palette.warning.main,
    error: theme.palette.error.main,
    success: theme.palette.success.main,
  }

  const selectedColor = colorMap[color]

  return (
    <Card
      className="hover-lift"
      sx={{
        height: '100%',
        background: `linear-gradient(135deg, ${alpha(selectedColor, 0.05)} 0%, ${alpha(selectedColor, 0.02)} 100%)`,
        border: `1px solid ${alpha(selectedColor, 0.1)}`,
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 3,
          background: `linear-gradient(90deg, ${selectedColor} 0%, ${alpha(selectedColor, 0.7)} 100%)`,
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontWeight: 500, mb: 1, textTransform: 'uppercase', letterSpacing: 0.5 }}
            >
              {title}
            </Typography>
            <Typography
              variant="h3"
              sx={{
                fontWeight: 700,
                color: selectedColor,
                lineHeight: 1.2,
                mb: subtitle ? 0.5 : 0,
              }}
            >
              {typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              backgroundColor: alpha(selectedColor, 0.1),
              color: selectedColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>

        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={trend.direction === 'up' ? <TrendingUpIcon /> : <TrendingDownIcon />}
              label={`${trend.direction === 'up' ? '+' : '-'}${trend.value}%`}
              size="small"
              color={trend.direction === 'up' ? 'success' : 'error'}
              variant="outlined"
              sx={{
                fontSize: '0.75rem',
                height: 24,
                '& .MuiChip-icon': {
                  fontSize: '0.875rem',
                },
              }}
            />
            <Typography variant="caption" color="text.secondary">
              {trend.period || 'vs last month'}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

export default StatsCard
