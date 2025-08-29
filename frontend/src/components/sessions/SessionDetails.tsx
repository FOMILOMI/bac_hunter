import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  Chip,
  useTheme,
  alpha,
} from '@mui/material'
import { Session } from '../../types'

interface SessionDetailsProps {
  session: Session
}

const SessionDetails: React.FC<SessionDetailsProps> = ({ session }) => {
  const theme = useTheme()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return theme.palette.success.main
      case 'running': return theme.palette.primary.main
      case 'failed': return theme.palette.error.main
      default: return theme.palette.text.secondary
    }
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        {session.name}
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Session Information
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={
                      <Chip
                        size="small"
                        label={session.status}
                        sx={{
                          bgcolor: alpha(getStatusColor(session.status), 0.1),
                          color: getStatusColor(session.status)
                        }}
                      />
                    }
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemText
                    primary="Type"
                    secondary={session.type}
                  />
                </ListItem>
                
                {session.start_time && (
                  <ListItem>
                    <ListItemText
                      primary="Start Time"
                      secondary={new Date(session.start_time).toLocaleString()}
                    />
                  </ListItem>
                )}
                
                {session.end_time && (
                  <ListItem>
                    <ListItemText
                      primary="End Time"
                      secondary={new Date(session.end_time).toLocaleString()}
                    />
                  </ListItem>
                )}
                
                {session.duration && (
                  <ListItem>
                    <ListItemText
                      primary="Duration"
                      secondary={`${Math.round(session.duration / 60)} minutes`}
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Session Metrics
              </Typography>
              
              <List dense>
                {session.requests_count && (
                  <ListItem>
                    <ListItemText
                      primary="Total Requests"
                      secondary={session.requests_count}
                    />
                  </ListItem>
                )}
                
                {session.responses_count && (
                  <ListItem>
                    <ListItemText
                      primary="Total Responses"
                      secondary={session.responses_count}
                    />
                  </ListItem>
                )}
                
                {session.findings_count && (
                  <ListItem>
                    <ListItemText
                      primary="Findings Generated"
                      secondary={session.findings_count}
                    />
                  </ListItem>
                )}
                
                {session.progress && (
                  <ListItem>
                    <ListItemText
                      primary="Progress"
                      secondary={`${session.progress}%`}
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default SessionDetails