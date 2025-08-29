import React from 'react'
import {
  Grid,
  Box,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material'
import { AnimatePresence } from 'framer-motion'
import { Session } from '../../types'
import SessionCard from './SessionCard'

interface SessionGridProps {
  sessions: Session[]
  loading?: boolean
  error?: string
  onView?: (session: Session) => void
  onEdit?: (session: Session) => void
  onDelete?: (session: Session) => void
  onReplay?: (session: Session) => void
}

const SessionGrid: React.FC<SessionGridProps> = ({
  sessions,
  loading = false,
  error,
  onView,
  onEdit,
  onDelete,
  onReplay
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

  if (sessions.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h6" color="text.secondary">
          No sessions found
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Start a scan to create your first session
        </Typography>
      </Box>
    )
  }

  return (
    <Grid container spacing={2}>
      <AnimatePresence>
        {sessions.map((session) => (
          <Grid item xs={12} md={6} lg={4} key={session.id}>
            <SessionCard
              session={session}
              onView={onView}
              onEdit={onEdit}
              onDelete={onDelete}
              onReplay={onReplay}
            />
          </Grid>
        ))}
      </AnimatePresence>
    </Grid>
  )
}

export default SessionGrid