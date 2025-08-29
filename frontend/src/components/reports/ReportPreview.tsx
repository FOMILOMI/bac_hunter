import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Divider,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Visibility as ViewIcon,
  Download as DownloadIcon,
  PictureAsPdf as PDFIcon,
  Description as HTMLIcon,
} from '@mui/icons-material'
import { Report } from '../../types'

interface ReportPreviewProps {
  report: Report
  onDownload?: () => void
  onFullView?: () => void
}

const ReportPreview: React.FC<ReportPreviewProps> = ({
  report,
  onDownload,
  onFullView
}) => {
  const theme = useTheme()

  const renderPreviewContent = () => {
    if (!report.content) {
      return (
        <Typography color="text.secondary" sx={{ fontStyle: 'italic' }}>
          No content available for preview
        </Typography>
      )
    }

    return (
      <Box>
        {/* Executive Summary */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Executive Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: alpha(theme.palette.error.main, 0.1) }}>
                <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                  <Typography variant="h4" sx={{ color: theme.palette.error.main }}>
                    {report.content.summary?.critical_findings || 0}
                  </Typography>
                  <Typography variant="caption">Critical</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: alpha(theme.palette.warning.main, 0.1) }}>
                <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                  <Typography variant="h4" sx={{ color: theme.palette.warning.main }}>
                    {report.content.summary?.high_findings || 0}
                  </Typography>
                  <Typography variant="caption">High</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: alpha(theme.palette.info.main, 0.1) }}>
                <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                  <Typography variant="h4" sx={{ color: theme.palette.info.main }}>
                    {report.content.summary?.medium_findings || 0}
                  </Typography>
                  <Typography variant="caption">Medium</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={3}>
              <Card sx={{ bgcolor: alpha(theme.palette.success.main, 0.1) }}>
                <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                  <Typography variant="h4" sx={{ color: theme.palette.success.main }}>
                    {report.content.summary?.low_findings || 0}
                  </Typography>
                  <Typography variant="caption">Low</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Key Metrics */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Key Metrics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Total Findings
              </Typography>
              <Typography variant="h6">
                {report.content.summary?.total_findings || 0}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Scan Duration
              </Typography>
              <Typography variant="h6">
                {report.content.summary?.scan_duration || 0} min
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Targets Scanned
              </Typography>
              <Typography variant="h6">
                {report.content.summary?.target_urls?.length || 0}
              </Typography>
            </Grid>
          </Grid>
        </Box>

        {/* Sample Content */}
        {report.format === 'html' && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Content Preview
            </Typography>
            <Card sx={{ 
              bgcolor: alpha(theme.palette.background.paper, 0.5),
              border: `1px solid ${theme.palette.divider}`
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  &lt;html&gt;<br />
                  &nbsp;&nbsp;&lt;head&gt;<br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&lt;title&gt;{report.title}&lt;/title&gt;<br />
                  &nbsp;&nbsp;&lt;/head&gt;<br />
                  &nbsp;&nbsp;&lt;body&gt;<br />
                  &nbsp;&nbsp;&nbsp;&nbsp;&lt;h1&gt;Security Assessment Report&lt;/h1&gt;<br />
                  &nbsp;&nbsp;&nbsp;&nbsp;...report content...<br />
                  &nbsp;&nbsp;&lt;/body&gt;<br />
                  &lt;/html&gt;
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>
    )
  }

  return (
    <Box>
      {/* Preview Header */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        mb: 3,
        p: 2,
        bgcolor: alpha(theme.palette.primary.main, 0.05),
        borderRadius: 1
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {report.format === 'html' ? <HTMLIcon /> : <PDFIcon />}
          <Typography variant="h6">
            Report Preview
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ViewIcon />}
            onClick={onFullView}
          >
            Full View
          </Button>
          {report.status === 'completed' && (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={onDownload}
            >
              Download
            </Button>
          )}
        </Box>
      </Box>

      {/* Preview Content */}
      <Card>
        <CardContent>
          {renderPreviewContent()}
        </CardContent>
      </Card>
    </Box>
  )
}

export default ReportPreview