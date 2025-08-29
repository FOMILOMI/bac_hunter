import React from 'react'
import { Typography, Box } from '@mui/material'
import { useParams } from 'react-router-dom'

const ScanDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Scan Detail
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Scan {id} details coming soon...
      </Typography>
    </Box>
  )
}

export default ScanDetail
