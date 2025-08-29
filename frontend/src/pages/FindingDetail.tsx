import React from 'react'
import { Typography, Box } from '@mui/material'
import { useParams } from 'react-router-dom'

const FindingDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Finding Detail
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Finding {id} details coming soon...
      </Typography>
    </Box>
  )
}

export default FindingDetail
