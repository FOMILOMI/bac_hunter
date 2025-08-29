import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  useTheme,
} from '@mui/material'
import { Session } from '../../types'

interface SessionVisualizerProps {
  session: Session
}

const SessionVisualizer: React.FC<SessionVisualizerProps> = ({ session }) => {
  const theme = useTheme()

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Session Visualization
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Request Flow
              </Typography>
              
              <Box sx={{ 
                height: 300,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `2px dashed ${theme.palette.divider}`,
                borderRadius: 2
              }}>
                <Typography color="text.secondary">
                  Session flow visualization will be displayed here
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Response Analysis
              </Typography>
              
              <Box sx={{ 
                height: 300,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: `2px dashed ${theme.palette.divider}`,
                borderRadius: 2
              }}>
                <Typography color="text.secondary">
                  Response analysis chart will be displayed here
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default SessionVisualizer