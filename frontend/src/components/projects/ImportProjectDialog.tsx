import React, { useState, useRef } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  IconButton,
  Chip,
  useTheme,
  alpha,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material'
import {
  Close as CloseIcon,
  Upload as UploadIcon,
  FileUpload as FileUploadIcon,
  Link as LinkIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { motion } from 'framer-motion'

interface ImportProjectDialogProps {
  open: boolean
  onClose: () => void
  onImport: (data: any) => void
}

const ImportProjectDialog: React.FC<ImportProjectDialogProps> = ({
  open,
  onClose,
  onImport,
}) => {
  const theme = useTheme()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [importMethod, setImportMethod] = useState<'file' | 'url' | 'paste'>('file')
  const [importFormat, setImportFormat] = useState<'json' | 'har' | 'config' | 'auto'>('auto')
  const [importData, setImportData] = useState('')
  const [importUrl, setImportUrl] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [validationResults, setValidationResults] = useState<any>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setImportData('')
      setImportUrl('')
      
      // Auto-detect format based on file extension
      if (file.name.endsWith('.har')) {
        setImportFormat('har')
      } else if (file.name.endsWith('.json')) {
        setImportFormat('json')
      } else if (file.name.endsWith('.config') || file.name.endsWith('.conf')) {
        setImportFormat('config')
      } else {
        setImportFormat('auto')
      }
    }
  }

  const handleFileRead = async () => {
    if (!selectedFile) return

    try {
      const text = await selectedFile.text()
      setImportData(text)
      validateImportData(text, importFormat)
    } catch (error) {
      setValidationErrors(['Failed to read file. Please check if the file is accessible.'])
    }
  }

  const handleUrlImport = async () => {
    if (!importUrl.trim()) return

    try {
      setIsValidating(true)
      const response = await fetch(importUrl)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const text = await response.text()
      setImportData(text)
      validateImportData(text, importFormat)
    } catch (error) {
      setValidationErrors([`Failed to fetch from URL: ${(error as Error).message}`])
    } finally {
      setIsValidating(false)
    }
  }

  const validateImportData = (data: string, format: string) => {
    setIsValidating(true)
    setValidationErrors([])
    
    try {
      let parsedData: any
      
      switch (format) {
        case 'json':
          parsedData = JSON.parse(data)
          break
        case 'har':
          parsedData = JSON.parse(data)
          if (!parsedData.log || !parsedData.log.entries) {
            throw new Error('Invalid HAR format: missing log.entries')
          }
          break
        case 'config':
          // Parse config format (could be INI, YAML, or custom format)
          parsedData = parseConfigFormat(data)
          break
        case 'auto':
          // Try to auto-detect format
          try {
            parsedData = JSON.parse(data)
            if (parsedData.log && parsedData.log.entries) {
              setImportFormat('har')
            } else if (parsedData.name && parsedData.target_url) {
              setImportFormat('json')
            } else {
              setImportFormat('config')
            }
          } catch {
            parsedData = parseConfigFormat(data)
            setImportFormat('config')
          }
          break
        default:
          throw new Error('Unsupported import format')
      }

      // Validate project structure
      const errors = validateProjectStructure(parsedData, format)
      if (errors.length > 0) {
        setValidationErrors(errors)
        setValidationResults(null)
      } else {
        setValidationResults({
          data: parsedData,
          format,
          summary: generateImportSummary(parsedData, format),
        })
      }
    } catch (error) {
      setValidationErrors([`Validation failed: ${(error as Error).message}`])
      setValidationResults(null)
    } finally {
      setIsValidating(false)
    }
  }

  const parseConfigFormat = (data: string): any => {
    // Simple config parser - in real implementation this would be more sophisticated
    const lines = data.split('\n')
    const config: any = {}
    
    lines.forEach(line => {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=')
        if (key && valueParts.length > 0) {
          config[key.trim()] = valueParts.join('=').trim()
        }
      }
    })
    
    return config
  }

  const validateProjectStructure = (data: any, format: string): string[] => {
    const errors: string[] = []
    
    if (format === 'json' || format === 'config') {
      if (!data.name) errors.push('Missing project name')
      if (!data.target_url) errors.push('Missing target URL')
      if (data.target_url && !isValidUrl(data.target_url)) {
        errors.push('Invalid target URL format')
      }
    } else if (format === 'har') {
      if (!data.log?.entries || !Array.isArray(data.log.entries)) {
        errors.push('Invalid HAR format: missing or invalid entries')
      }
    }
    
    return errors
  }

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  }

  const generateImportSummary = (data: any, format: string): any => {
    if (format === 'har') {
      return {
        type: 'HAR File',
        entries: data.log?.entries?.length || 0,
        domains: [...new Set(data.log?.entries?.map((e: any) => new URL(e.request.url).hostname))].length,
        timeRange: {
          start: data.log?.pages?.[0]?.startedDateTime,
          end: data.log?.pages?.[0]?.startedDateTime,
        },
      }
    } else {
      return {
        type: 'Project Configuration',
        name: data.name,
        target: data.target_url,
        hasScanConfig: !!data.scan_config,
        hasAuth: !!data.scan_config?.authentication,
        tags: data.tags?.length || 0,
      }
    }
  }

  const handleImport = () => {
    if (validationResults) {
      onImport(validationResults.data)
      onClose()
    }
  }

  const resetForm = () => {
    setImportMethod('file')
    setImportFormat('auto')
    setImportData('')
    setImportUrl('')
    setSelectedFile(null)
    setValidationErrors([])
    setValidationResults(null)
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '600px',
        },
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <UploadIcon />
          Import Project
        </Typography>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Import projects from various sources including HAR files, JSON configurations, or external URLs.
          </Typography>

          {/* Import Method Selection */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Import Method
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {[
                { value: 'file', label: 'File Upload', icon: FileUploadIcon },
                { value: 'url', label: 'URL Import', icon: LinkIcon },
                { value: 'paste', label: 'Paste Data', icon: CodeIcon },
              ].map((method) => (
                <Button
                  key={method.value}
                  variant={importMethod === method.value ? 'contained' : 'outlined'}
                  startIcon={<method.icon />}
                  onClick={() => setImportMethod(method.value as any)}
                  size="small"
                >
                  {method.label}
                </Button>
              ))}
            </Box>
          </Box>

          {/* Import Format Selection */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Import Format
            </Typography>
            <FormControl fullWidth size="small">
              <InputLabel>Format</InputLabel>
              <Select
                value={importFormat}
                onChange={(e) => setImportFormat(e.target.value as any)}
                label="Format"
              >
                <MenuItem value="auto">Auto-detect</MenuItem>
                <MenuItem value="json">JSON Configuration</MenuItem>
                <MenuItem value="har">HAR File</MenuItem>
                <MenuItem value="config">Config File</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Import Method Specific Content */}
          {importMethod === 'file' && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                File Upload
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json,.har,.config,.conf,.txt"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <Button
                  variant="outlined"
                  onClick={() => fileInputRef.current?.click()}
                  startIcon={<FileUploadIcon />}
                >
                  Choose File
                </Button>
                {selectedFile && (
                  <>
                    <Chip
                      label={selectedFile.name}
                      onDelete={() => setSelectedFile(null)}
                      color="primary"
                      variant="outlined"
                    />
                    <Button
                      variant="contained"
                      onClick={handleFileRead}
                      disabled={!selectedFile}
                      size="small"
                    >
                      Read File
                    </Button>
                  </>
                )}
              </Box>
            </Box>
          )}

          {importMethod === 'url' && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                URL Import
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  placeholder="https://example.com/config.json"
                  value={importUrl}
                  onChange={(e) => setImportUrl(e.target.value)}
                  size="small"
                />
                <Button
                  variant="contained"
                  onClick={handleUrlImport}
                  disabled={!importUrl.trim() || isValidating}
                  size="small"
                >
                  {isValidating ? 'Fetching...' : 'Fetch'}
                </Button>
              </Box>
            </Box>
          )}

          {importMethod === 'paste' && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Paste Data
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={8}
                placeholder="Paste your JSON, HAR, or config data here..."
                value={importData}
                onChange={(e) => setImportData(e.target.value)}
                size="small"
              />
            </Box>
          )}

          {/* Validation Button */}
          {(importData || selectedFile) && (
            <Box sx={{ mb: 3 }}>
              <Button
                variant="contained"
                onClick={() => validateImportData(importData, importFormat)}
                disabled={isValidating || (!importData && !selectedFile)}
                startIcon={<SecurityIcon />}
                fullWidth
              >
                {isValidating ? 'Validating...' : 'Validate Import Data'}
              </Button>
            </Box>
          )}

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Validation Errors:
              </Typography>
              <List dense>
                {validationErrors.map((error, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <ErrorIcon color="error" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={error} />
                  </ListItem>
                ))}
              </List>
            </Alert>
          )}

          {/* Validation Results */}
          {validationResults && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Alert severity="success" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckIcon />
                  Validation Successful
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    <strong>Format:</strong> {validationResults.format.toUpperCase()}
                  </Typography>
                  {validationResults.format === 'har' && (
                    <>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>Entries:</strong> {validationResults.summary.entries}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>Domains:</strong> {validationResults.summary.domains}
                      </Typography>
                    </>
                  )}
                  {validationResults.format === 'json' && (
                    <>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>Project:</strong> {validationResults.summary.name}
                      </Typography>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        <strong>Target:</strong> {validationResults.summary.target}
                      </Typography>
                    </>
                  )}
                </Box>
              </Alert>
            </motion.div>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose} variant="outlined">
          Cancel
        </Button>
        <Button
          onClick={handleImport}
          variant="contained"
          disabled={!validationResults}
          startIcon={<UploadIcon />}
        >
          Import Project
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default ImportProjectDialog
