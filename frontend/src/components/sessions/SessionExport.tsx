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
  Grid,
  Alert,
  LinearProgress,
} from '@mui/material'
import {
  Download as DownloadIcon,
} from '@mui/icons-material'
import toast from 'react-hot-toast'
import { Session } from '../../types'

interface SessionExportProps {
  sessions: Session[]
  onClose: () => void
}

const SessionExport: React.FC<SessionExportProps> = ({ sessions, onClose }) => {
  const [exportFormat, setExportFormat] = useState('json')
  const [fileName, setFileName] = useState('')
  const [isExporting, setIsExporting] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleExport = async () => {
    setIsExporting(true)
    setProgress(0)

    try {
      // Simulate export progress
      const interval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90))
      }, 200)

      // Mock export - in real implementation would call API
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      clearInterval(interval)
      setProgress(100)

      // Generate download
      const data = JSON.stringify(sessions, null, 2)
      const blob = new Blob([data], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName || `sessions_export_${new Date().toISOString().split('T')[0]}.${exportFormat}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success('Sessions exported successfully!')
      setTimeout(onClose, 1000)

    } catch (error: any) {
      toast.error(`Export failed: ${error.message}`)
    } finally {
      setIsExporting(false)
      setProgress(0)
    }
  }

  return (
    <Box sx={{ minWidth: 400 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Export Sessions
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Export Format</InputLabel>
            <Select
              value={exportFormat}
              label="Export Format"
              onChange={(e) => setExportFormat(e.target.value)}
            >
              <MenuItem value="json">JSON</MenuItem>
              <MenuItem value="csv">CSV</MenuItem>
              <MenuItem value="xml">XML</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="File Name (Optional)"
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
            placeholder={`sessions_export_${new Date().toISOString().split('T')[0]}`}
          />
        </Grid>
      </Grid>

      {isExporting && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Exporting {sessions.length} sessions... {progress}%
          </Typography>
          <LinearProgress variant="determinate" value={progress} />
        </Box>
      )}

      <Alert severity="info" sx={{ mt: 2 }}>
        Exporting {sessions.length} session(s) in {exportFormat.toUpperCase()} format.
      </Alert>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button onClick={onClose} disabled={isExporting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={<DownloadIcon />}
          onClick={handleExport}
          disabled={isExporting}
        >
          {isExporting ? 'Exporting...' : 'Export'}
        </Button>
      </Box>
    </Box>
  )
}

export default SessionExport