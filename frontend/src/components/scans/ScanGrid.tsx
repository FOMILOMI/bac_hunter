import React from 'react'
import {
  Grid,
  Box,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material'
import { AnimatePresence } from 'framer-motion'
import { Scan } from '../../types'
import ScanCard from './ScanCard'

interface ScanGridProps {
  scans: Scan[]
  loading?: boolean
  error?: string
  onView?: (scan: Scan) => void
  onEdit?: (scan: Scan) => void
  onDelete?: (scan: Scan) => void
  onStart?: (scan: Scan) => void
  onStop?: (scan: Scan) => void
}

const ScanGrid: React.FC<ScanGridProps> = ({
  scans,
  loading = false,
  error,
  onView,
  onEdit,
  onDelete,
  onStart,
  onStop
}) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    )
  }

  if (scans.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h6" color="text.secondary">
          No scans found
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Create your first scan to get started
        </Typography>
      </Box>
    )
  }

  return (
    <Grid container spacing={2}>
      <AnimatePresence>
        {scans.map((scan) => (
          <Grid item xs={12} md={6} lg={4} key={scan.id}>
            <ScanCard
              scan={scan}
              onView={onView}
              onEdit={onEdit}
              onDelete={onDelete}
              onStart={onStart}
              onStop={onStop}
            />
          </Grid>
        ))}
      </AnimatePresence>
    </Grid>
  )
}

export default ScanGrid