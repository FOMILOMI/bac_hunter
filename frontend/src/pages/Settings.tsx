import React from 'react'
import { Typography, Box } from '@mui/material'

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Settings
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Application settings and preferences coming soon...
      </Typography>
    </Box>
  )
}

export default Settings
