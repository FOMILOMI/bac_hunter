import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemText,
  Button,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Download as DownloadIcon,
  Share as ShareIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { Report } from '../../types'

interface ReportDetailsProps {
  report: Report
  onEdit?: () => void
  onDownload?: () => void
  onShare?: () => void
}

const ReportDetails: React.FC<ReportDetailsProps> = ({
  report,
  onEdit,
  onDownload,
  onShare
}) => {
  const theme = useTheme()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return theme.palette.success.main
      case 'generating': return theme.palette.warning.main
      case 'failed': return theme.palette.error.main
      case 'scheduled': return theme.palette.info.main
      default: return theme.palette.text.secondary
    }
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ mb: 1 }}>
          {report.title}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {report.description}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip 
            label={report.status}
            sx={{ 
              bgcolor: alpha(getStatusColor(report.status), 0.1),
              color: getStatusColor(report.status)
            }}
          />
          <Chip label={report.type} variant="outlined" />
          <Chip label={report.format.toUpperCase()} variant="outlined" />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {report.status === 'completed' && (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={onDownload}
            >
              Download
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<ShareIcon />}
            onClick={onShare}
          >
            Share
          </Button>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={onEdit}
          >
            Edit
          </Button>
        </Box>
      </Box>

      {/* Report Information */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Report Information
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Created"
                    secondary={new Date(report.created_at).toLocaleString()}
                  />
                </ListItem>
                
                {report.generated_at && (
                  <ListItem>
                    <ListItemText
                      primary="Generated"
                      secondary={new Date(report.generated_at).toLocaleString()}
                    />
                  </ListItem>
                )}
                
                {report.file_size && (
                  <ListItem>
                    <ListItemText
                      primary="File Size"
                      secondary={`${(report.file_size / 1024).toFixed(1)} KB`}
                    />
                  </ListItem>
                )}
                
                {report.template_id && (
                  <ListItem>
                    <ListItemText
                      primary="Template"
                      secondary={report.template_id}
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
                Content Summary
              </Typography>
              
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Total Findings"
                    secondary={report.content?.summary?.total_findings || 0}
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemText
                    primary="Critical Issues"
                    secondary={report.content?.summary?.critical_findings || 0}
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemText
                    primary="Scan Duration"
                    secondary={`${report.content?.summary?.scan_duration || 0} minutes`}
                  />
                </ListItem>
                
                <ListItem>
                  <ListItemText
                    primary="Target URLs"
                    secondary={report.content?.summary?.target_urls?.length || 0}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Content Preview */}
      {report.content && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Content Preview
            </Typography>
            
            <Box sx={{ 
              bgcolor: alpha(theme.palette.primary.main, 0.05),
              p: 2,
              borderRadius: 1,
              border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
            }}>
              <pre style={{ 
                margin: 0, 
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word'
              }}>
                {JSON.stringify(report.content, null, 2)}
              </pre>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default ReportDetails