import React from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Pause as PauseIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'

const ScanProgress: React.FC = () => {
  const activeScans = [
    {
      id: '1',
      name: 'Comprehensive Scan - example.com',
      progress: 67,
      phase: 'access',
      status: 'running',
      eta: '8 minutes',
      findings: 12,
    },
    {
      id: '2',
      name: 'API Security Test - api.example.com',
      progress: 34,
      phase: 'recon',
      status: 'running',
      eta: '15 minutes',
      findings: 3,
    },
  ]

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'recon':
        return 'info'
      case 'access':
        return 'warning'
      case 'audit':
        return 'primary'
      case 'exploit':
        return 'error'
      default:
        return 'default'
    }
  }

  return (
    <Card>
      <CardHeader
        title="Active Scans"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
        subheader="Real-time scan monitoring"
      />
      <CardContent sx={{ pt: 0 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {activeScans.map((scan) => (
            <Box
              key={scan.id}
              sx={{
                p: 2,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 2,
                backgroundColor: 'background.paper',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {scan.name}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={scan.phase}
                      size="small"
                      color={getPhaseColor(scan.phase) as any}
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {scan.findings} findings • ETA: {scan.eta}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Tooltip title="Pause scan">
                    <IconButton size="small">
                      <PauseIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Stop scan">
                    <IconButton size="small" color="error">
                      <StopIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View details">
                    <IconButton size="small" color="primary">
                      <ViewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              <Box sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    Progress
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {scan.progress}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={scan.progress}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 4,
                    },
                  }}
                />
              </Box>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  )
}

export default ScanProgress
