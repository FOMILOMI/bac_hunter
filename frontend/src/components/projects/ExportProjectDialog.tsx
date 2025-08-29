import React, { useState, useMemo } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  TextField,
  Chip,
  Alert,
  IconButton,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Switch,
  useTheme,
  alpha,
} from '@mui/material'
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  FileDownload as FileDownloadIcon,
  PictureAsPdf as PdfIcon,
  Code as JsonIcon,
  Description as ReportIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

import { Project } from '../../types'

interface ExportProjectDialogProps {
  open: boolean
  onClose: () => void
  projects: Project[]
}

const ExportProjectDialog: React.FC<ExportProjectDialogProps> = ({
  open,
  onClose,
  projects,
}) => {
  const theme = useTheme()
  const [exportFormat, setExportFormat] = useState<'json' | 'pdf' | 'html' | 'csv' | 'xml'>('json')
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])
  const [exportOptions, setExportOptions] = useState({
    includeFindings: true,
    includeScans: true,
    includeConfig: true,
    includeMetadata: true,
    includeAIInsights: true,
    compressOutput: false,
    includeAttachments: false,
  })
  const [customFileName, setCustomFileName] = useState('')
  const [isExporting, setIsExporting] = useState(false)

  // Generate default filename
  const defaultFileName = useMemo(() => {
    const timestamp = new Date().toISOString().split('T')[0]
    if (selectedProjects.length === 1) {
      const project = projects.find(p => p.id === selectedProjects[0])
      return `${project?.name || 'project'}_${timestamp}`
    } else if (selectedProjects.length > 1) {
      return `projects_${selectedProjects.length}_${timestamp}`
    }
    return `bac_hunter_export_${timestamp}`
  }, [selectedProjects, projects])

  const handleProjectSelection = (projectId: string, checked: boolean) => {
    if (checked) {
      setSelectedProjects([...selectedProjects, projectId])
    } else {
      setSelectedProjects(selectedProjects.filter(id => id !== projectId))
    }
  }

  const handleSelectAll = () => {
    if (selectedProjects.length === projects.length) {
      setSelectedProjects([])
    } else {
      setSelectedProjects(projects.map(p => p.id))
    }
  }

  const handleExportOptionChange = (option: string, value: boolean) => {
    setExportOptions(prev => ({ ...prev, [option]: value }))
  }

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <PdfIcon />
      case 'json':
        return <JsonIcon />
      case 'html':
        return <ReportIcon />
      case 'csv':
        return <ReportIcon />
      case 'xml':
        return <CodeIcon />
      default:
        return <FileDownloadIcon />
    }
  }

  const getFormatDescription = (format: string) => {
    switch (format) {
      case 'pdf':
        return 'Professional PDF report with findings and visualizations'
      case 'json':
        return 'Raw data export for integration with other tools'
      case 'html':
        return 'Interactive HTML report viewable in any browser'
      case 'csv':
        return 'Spreadsheet-compatible format for data analysis'
      case 'xml':
        return 'Structured XML format for enterprise systems'
      default:
        return 'Standard export format'
    }
  }

  const getFileExtension = (format: string) => {
    switch (format) {
      case 'pdf':
        return '.pdf'
      case 'json':
        return '.json'
      case 'html':
        return '.html'
      case 'csv':
        return '.csv'
      case 'xml':
        return '.xml'
      default:
        return '.txt'
    }
  }

  const validateExportOptions = () => {
    const errors: string[] = []
    
    if (selectedProjects.length === 0) {
      errors.push('Please select at least one project to export')
    }
    
    if (exportFormat === 'pdf' && !exportOptions.includeFindings) {
      errors.push('PDF export requires findings to be included')
    }
    
    if (exportFormat === 'csv' && exportOptions.includeAttachments) {
      errors.push('CSV format cannot include attachments')
    }
    
    return errors
  }

  const handleExport = async () => {
    const errors = validateExportOptions()
    if (errors.length > 0) {
      // In a real implementation, you would show these errors to the user
      console.error('Export validation errors:', errors)
      return
    }

    setIsExporting(true)
    
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // In a real implementation, this would call the backend export API
      const exportData = {
        projects: projects.filter(p => selectedProjects.includes(p.id)),
        format: exportFormat,
        options: exportOptions,
        filename: customFileName || defaultFileName + getFileExtension(exportFormat),
        timestamp: new Date().toISOString(),
      }
      
      console.log('Exporting data:', exportData)
      
      // Trigger download (mock implementation)
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = exportData.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      // Close dialog after successful export
      onClose()
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const canExport = selectedProjects.length > 0 && !isExporting

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '700px',
        },
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <DownloadIcon />
          Export Projects
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Export your projects in various formats for reporting, analysis, or integration with other tools.
          </Typography>

          {/* Project Selection */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="subtitle2">
                Select Projects to Export
              </Typography>
              <Button
                size="small"
                onClick={handleSelectAll}
                variant="outlined"
              >
                {selectedProjects.length === projects.length ? 'Deselect All' : 'Select All'}
              </Button>
            </Box>
            
            <Box sx={{ maxHeight: 200, overflow: 'auto', border: 1, borderColor: 'divider', borderRadius: 1 }}>
              <List dense>
                {projects.map((project) => (
                  <ListItem key={project.id} sx={{ py: 1 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon
                        color={selectedProjects.includes(project.id) ? 'primary' : 'disabled'}
                        fontSize="small"
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={project.name}
                      secondary={project.target_url}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        edge="end"
                        checked={selectedProjects.includes(project.id)}
                        onChange={(e) => handleProjectSelection(project.id, e.target.checked)}
                        size="small"
                      />
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
            
            {selectedProjects.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {selectedProjects.length} project{selectedProjects.length !== 1 ? 's' : ''} selected
                </Typography>
              </Box>
            )}
          </Box>

          {/* Export Format Selection */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Export Format
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {[
                { value: 'json', label: 'JSON', icon: JsonIcon },
                { value: 'pdf', label: 'PDF Report', icon: PdfIcon },
                { value: 'html', label: 'HTML', icon: ReportIcon },
                { value: 'csv', label: 'CSV', icon: ReportIcon },
                { value: 'xml', label: 'XML', icon: CodeIcon },
              ].map((format) => (
                <Button
                  key={format.value}
                  variant={exportFormat === format.value ? 'contained' : 'outlined'}
                  startIcon={<format.icon />}
                  onClick={() => setExportFormat(format.value as any)}
                  size="small"
                  sx={{ minWidth: 120 }}
                >
                  {format.label}
                </Button>
              ))}
            </Box>
            
            <Box sx={{ mt: 1, p: 2, backgroundColor: alpha(theme.palette.info.main, 0.1), borderRadius: 1 }}>
              <Typography variant="body2" color="info.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <InfoIcon fontSize="small" />
                {getFormatDescription(exportFormat)}
              </Typography>
            </Box>
          </Box>

          {/* Export Options */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SettingsIcon />
              Export Options
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeFindings}
                      onChange={(e) => handleExportOptionChange('includeFindings', e.target.checked)}
                      disabled={exportFormat === 'pdf'} // PDF always includes findings
                    />
                  }
                  label="Include Findings"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Export all vulnerability findings and details
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeScans}
                      onChange={(e) => handleExportOptionChange('includeScans', e.target.checked)}
                    />
                  }
                  label="Include Scan History"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Export scan execution logs and results
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeConfig}
                      onChange={(e) => handleExportOptionChange('includeConfig', e.target.checked)}
                    />
                  }
                  label="Include Configuration"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Export project settings and scan configuration
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeMetadata}
                      onChange={(e) => handleExportOptionChange('includeMetadata', e.target.checked)}
                    />
                  }
                  label="Include Metadata"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Export timestamps, tags, and project metadata
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeAIInsights}
                      onChange={(e) => handleExportOptionChange('includeAIInsights', e.target.checked)}
                    />
                  }
                  label="Include AI Insights"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Export AI-generated recommendations and analysis
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.compressOutput}
                      onChange={(e) => handleExportOptionChange('compressOutput', e.target.checked)}
                    />
                  }
                  label="Compress Output"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Create compressed archive for large exports
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.includeAttachments}
                      onChange={(e) => handleExportOptionChange('includeAttachments', e.target.checked)}
                      disabled={exportFormat === 'csv'}
                    />
                  }
                  label="Include Attachments"
                />
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                  Export screenshots, logs, and evidence files
                </Typography>
              </Grid>
            </Grid>
          </Box>

          {/* File Naming */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              File Naming
            </Typography>
            <TextField
              fullWidth
              placeholder={defaultFileName}
              value={customFileName}
              onChange={(e) => setCustomFileName(e.target.value)}
              size="small"
              helperText={`File will be saved as: ${(customFileName || defaultFileName) + getFileExtension(exportFormat)}`}
            />
          </Box>

          {/* Export Summary */}
          {canExport && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckIcon />
                  Export Summary
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Format:</strong> {exportFormat.toUpperCase()}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Projects:</strong> {selectedProjects.length}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Estimated Size:</strong> {selectedProjects.length * 50}KB - {selectedProjects.length * 200}KB
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Options:</strong> {Object.values(exportOptions).filter(Boolean).length} enabled
                  </Typography>
                </Box>
              </Alert>
            </motion.div>
          )}

          {/* Warnings */}
          {exportFormat === 'csv' && exportOptions.includeFindings && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Note:</strong> CSV export will flatten nested finding data. Consider using JSON format for complex data structures.
              </Typography>
            </Alert>
          )}

          {exportOptions.includeAttachments && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Note:</strong> Including attachments will significantly increase export size and time.
              </Typography>
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={onClose} variant="outlined">
          Cancel
        </Button>
        <Button
          onClick={handleExport}
          variant="contained"
          disabled={!canExport}
          startIcon={isExporting ? null : <DownloadIcon />}
        >
          {isExporting ? 'Exporting...' : 'Export Projects'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ExportProjectDialog
