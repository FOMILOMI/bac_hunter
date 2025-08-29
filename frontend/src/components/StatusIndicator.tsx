import React from 'react'
import { Box, Typography, Chip, Tooltip } from '@mui/material'
import { useWebSocketStore, useDashboardStore } from '../store'

const StatusIndicator: React.FC = () => {
  const { connected } = useWebSocketStore()
  const { stats } = useDashboardStore()

  const activeScans = stats?.scan_health?.active_scans || 0

  return (
    <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
          System Status
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title={connected ? 'Connected to server' : 'Disconnected from server'}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: connected ? 'success.main' : 'error.main',
                boxShadow: connected 
                  ? '0 0 8px rgba(76, 175, 80, 0.6)' 
                  : '0 0 8px rgba(244, 67, 54, 0.6)',
                animation: connected ? 'pulse 2s infinite' : 'none',
              }}
            />
          </Tooltip>
          <Typography variant="caption" color={connected ? 'success.main' : 'error.main'}>
            {connected ? 'Online' : 'Offline'}
          </Typography>
        </Box>
      </Box>
      
      {activeScans > 0 && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            label={`${activeScans} Active Scan${activeScans > 1 ? 's' : ''}`}
            size="small"
            color="primary"
            variant="outlined"
            sx={{
              fontSize: '0.7rem',
              height: 20,
              '& .MuiChip-label': {
                px: 1,
              },
            }}
          />
        </Box>
      )}
    </Box>
  )
}

export default StatusIndicator
