import React from 'react'
import {
  Box,
  Grid,
  Skeleton,
  Typography,
  Button,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
} from '@mui/material'
import {
  ViewModule as GridIcon,
  ViewList as ListIcon,
  Add as AddIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'

import { Scan } from '../../types'
import ScanCard from './ScanCard'

interface ScanGridProps {
  scans: Scan[]
  isLoading: boolean
  onPause: (id: string) => void
  onResume: (id: string) => void
  onStop: (id: string) => void
  onDelete: (id: string) => void
  onViewLogs: (scan: Scan) => void
  onViewMetrics: (scan: Scan) => void
  viewMode: 'grid' | 'list'
  setViewMode: (mode: 'grid' | 'list') => void
}

const ScanGrid: React.FC<ScanGridProps> = ({
  scans,
  isLoading,
  onPause,
  onResume,
  onStop,
  onDelete,
  onViewLogs,
  onViewMetrics,
  viewMode,
  setViewMode,
}) => {
  const theme = useTheme()

  if (isLoading) {
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6" color="text.secondary">
            Loading scans...
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Grid View">
              <IconButton
                size="small"
                onClick={() => setViewMode('grid')}
                color={viewMode === 'grid' ? 'primary' : 'default'}
              >
                <GridIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="List View">
              <IconButton
                size="small"
                onClick={() => setViewMode('list')}
                color={viewMode === 'list' ? 'primary' : 'default'}
              >
                <ListIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Grid container spacing={3}>
          {Array.from({ length: 6 }).map((_, index) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
              <Skeleton
                variant="rectangular"
                height={400}
                sx={{ borderRadius: 2 }}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    )
  }

  if (scans.length === 0) {
    return (
      <Box
        sx={{
          textAlign: 'center',
          py: 8,
          px: 3,
        }}
      >
        <Box
          sx={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 2rem',
            fontSize: '3rem',
            color: theme.palette.primary.main,
          }}
        >
          🔍
        </Box>
        
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
          No scans found
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
          {viewMode === 'grid' 
            ? 'Get started by creating your first security scan. Configure scan parameters, select targets, and begin vulnerability assessment.'
            : 'No scans match your current filters. Try adjusting your search criteria or create a new scan.'
          }
        </Typography>
        
        <Button
          variant="contained"
          size="large"
          startIcon={<AddIcon />}
          sx={{ px: 4, py: 1.5 }}
        >
          Create Your First Scan
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      {/* View Mode Toggle */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          {scans.length} scan{scans.length !== 1 ? 's' : ''} found
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Grid View">
            <IconButton
              size="small"
              onClick={() => setViewMode('grid')}
              color={viewMode === 'grid' ? 'primary' : 'default'}
              sx={{
                backgroundColor: viewMode === 'grid' 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent',
              }}
            >
              <GridIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="List View">
            <IconButton
              size="small"
              onClick={() => setViewMode('list')}
              color={viewMode === 'list' ? 'primary' : 'default'}
              sx={{
                backgroundColor: viewMode === 'list' 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent',
              }}
            >
              <ListIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Scans Grid/List */}
      <AnimatePresence mode="wait">
        {viewMode === 'grid' ? (
          <Grid container spacing={3}>
            {scans.map((scan, index) => (
              <Grid
                item
                xs={12}
                sm={6}
                md={4}
                lg={3}
                key={scan.id}
                component={motion.div}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <ScanCard
                  scan={scan}
                  onPause={onPause}
                  onResume={onResume}
                  onStop={onStop}
                  onDelete={onDelete}
                  onViewLogs={onViewLogs}
                  onViewMetrics={onViewMetrics}
                />
              </Grid>
            ))}
          </Grid>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {scans.map((scan, index) => (
              <motion.div
                key={scan.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <ScanCard
                  scan={scan}
                  onPause={onPause}
                  onResume={onResume}
                  onStop={onStop}
                  onDelete={onDelete}
                  onViewLogs={onViewLogs}
                  onViewMetrics={onViewMetrics}
                />
              </motion.div>
            ))}
          </Box>
        )}
      </AnimatePresence>

      {/* Load More Button (if needed) */}
      {scans.length >= 20 && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Button variant="outlined" size="large">
            Load More Scans
          </Button>
        </Box>
      )}
    </Box>
  )
}

export default ScanGrid
