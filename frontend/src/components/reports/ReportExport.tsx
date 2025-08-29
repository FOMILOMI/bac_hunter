import React, { useState } from 'react'
import {
  Box,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  FormControlLabel,
  Checkbox,
  Grid,
  Alert,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
} from '@mui/material'
import {
  Download as DownloadIcon,
  PictureAsPdf as PDFIcon,
  Description as HTMLIcon,
  TableChart as CSVIcon,
  DataObject as JSONIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'

import { Report } from '../../types'
import { exportAPI } from '../../services/api'

interface ReportExportProps {
  reports: Report[]
  onClose: () => void
}

const ReportExport: React.FC<ReportExportProps> = ({ reports, onClose }) => {
  const theme = useTheme()
  const [exportFormat, setExportFormat] = useState('pdf')
  const [selectedReports, setSelectedReports] = useState<string[]>([])
  const [includeMetadata, setIncludeMetadata] = useState(true)
  const [includeCharts, setIncludeCharts] = useState(true)
  const [customFileName, setCustomFileName] = useState('')
  const [isExporting, setIsExporting] = useState(false)
  const [exportProgress, setExportProgress] = useState(0)

  const formatOptions = [
    { value: 'pdf', label: 'PDF Report', icon: <PDFIcon /> },
    { value: 'html', label: 'HTML Report', icon: <HTMLIcon /> },
    { value: 'csv', label: 'CSV Data', icon: <CSVIcon /> },
    { value: 'json', label: 'JSON Export', icon: <JSONIcon /> },
  ]

  const handleSelectAll = () => {
    if (selectedReports.length === reports.length) {
      setSelectedReports([])
    } else {
      setSelectedReports(reports.map(r => r.id))
    }
  }

  const handleSelectReport = (reportId: string) => {
    if (selectedReports.includes(reportId)) {
      setSelectedReports(selectedReports.filter(id => id !== reportId))
    } else {
      setSelectedReports([...selectedReports, reportId])
    }
  }

  const getFileExtension = (format: string) => {
    const extensions = {
      pdf: '.pdf',
      html: '.html',
      csv: '.csv',
      json: '.json',
    }
    return extensions[format as keyof typeof extensions] || '.txt'
  }

  const handleExport = async () => {
    if (selectedReports.length === 0) {
      toast.error('Please select at least one report to export')
      return
    }

    setIsExporting(true)
    setExportProgress(0)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setExportProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      // Call export API
      const exportOptions = {
        format: exportFormat,
        include_metadata: includeMetadata,
        include_charts: includeCharts,
        report_ids: selectedReports,
      }

      const result = await exportAPI.exportReports(exportOptions)
      
      clearInterval(progressInterval)
      setExportProgress(100)

      // Generate download
      const fileName = customFileName || `bac_hunter_reports_${new Date().toISOString().split('T')[0]}${getFileExtension(exportFormat)}`
      
      // Mock download for now
      const blob = new Blob([JSON.stringify(result, null, 2)], { 
        type: exportFormat === 'json' ? 'application/json' : 'text/plain' 
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success('Reports exported successfully!')
      setTimeout(() => {
        onClose()
      }, 1000)

    } catch (error: any) {
      toast.error(`Export failed: ${error.message}`)
      setExportProgress(0)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Box sx={{ minWidth: 500 }}>
      {/* Format Selection */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Export Format
        </Typography>
        <Grid container spacing={2}>
          {formatOptions.map((option) => (
            <Grid item xs={6} key={option.value}>
              <Button
                variant={exportFormat === option.value ? 'contained' : 'outlined'}
                fullWidth
                startIcon={option.icon}
                onClick={() => setExportFormat(option.value)}
                sx={{ p: 1.5 }}
              >
                {option.label}
              </Button>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Report Selection */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            Select Reports ({selectedReports.length} of {reports.length} selected)
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ mb: 2 }}>
            <Button
              size="small"
              variant="outlined"
              onClick={handleSelectAll}
              startIcon={<CheckIcon />}
            >
              {selectedReports.length === reports.length ? 'Deselect All' : 'Select All'}
            </Button>
          </Box>
          
          <List dense sx={{ maxHeight: 200, overflow: 'auto' }}>
            {reports.map((report) => (
              <ListItem
                key={report.id}
                button
                onClick={() => handleSelectReport(report.id)}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 1,
                  mb: 0.5,
                  bgcolor: selectedReports.includes(report.id) 
                    ? alpha(theme.palette.primary.main, 0.1)
                    : 'transparent'
                }}
              >
                <ListItemIcon>
                  <Checkbox
                    checked={selectedReports.includes(report.id)}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemText
                  primary={report.title}
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Chip size="small" label={report.type} />
                      <Chip size="small" label={report.format} />
                      <Typography variant="caption" color="text.secondary">
                        {report.created_at}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </AccordionDetails>
      </Accordion>

      {/* Options */}
      <Box sx={{ mt: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Export Options
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Custom File Name"
              value={customFileName}
              onChange={(e) => setCustomFileName(e.target.value)}
              placeholder={`bac_hunter_reports_${new Date().toISOString().split('T')[0]}`}
              helperText={`File extension ${getFileExtension(exportFormat)} will be added automatically`}
            />
          </Grid>
          
          <Grid item xs={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                />
              }
              label="Include Metadata"
            />
          </Grid>
          
          <Grid item xs={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={includeCharts}
                  onChange={(e) => setIncludeCharts(e.target.checked)}
                />
              }
              label="Include Charts"
            />
          </Grid>
        </Grid>
      </Box>

      {/* Export Progress */}
      {isExporting && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Exporting reports... {exportProgress}%
          </Typography>
          <LinearProgress variant="determinate" value={exportProgress} />
        </Box>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button onClick={onClose} disabled={isExporting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExport}
          disabled={selectedReports.length === 0 || isExporting}
        >
          {isExporting ? 'Exporting...' : 'Export Reports'}
        </Button>
      </Box>
    </Box>
  )
}

export default ReportExport