import React from 'react'
import { Typography, Box } from '@mui/material'
import { useParams } from 'react-router-dom'

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  
  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 2 }}>
        Project Detail
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Project {id} details coming soon...
      </Typography>
    </Box>
  )
}

export default ProjectDetail
