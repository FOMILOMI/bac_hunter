import React from 'react'
import {
  Grid,
  Box,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material'
import { AnimatePresence } from 'framer-motion'
import { Report } from '../../types'
import ReportCard from './ReportCard'

interface ReportGridProps {
  reports: Report[]
  loading?: boolean
  error?: string
  onView?: (report: Report) => void
  onEdit?: (report: Report) => void
  onDelete?: (report: Report) => void
  onDownload?: (report: Report) => void
}

const ReportGrid: React.FC<ReportGridProps> = ({
  reports,
  loading = false,
  error,
  onView,
  onEdit,
  onDelete,
  onDownload
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

  if (reports.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h6" color="text.secondary">
          No reports found
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Create your first report to get started
        </Typography>
      </Box>
    )
  }

  return (
    <Grid container spacing={2}>
      <AnimatePresence>
        {reports.map((report) => (
          <Grid item xs={12} md={6} lg={4} key={report.id}>
            <ReportCard
              report={report}
              onView={onView}
              onEdit={onEdit}
              onDelete={onDelete}
              onDownload={onDownload}
            />
          </Grid>
        ))}
      </AnimatePresence>
    </Grid>
  )
}

export default ReportGrid