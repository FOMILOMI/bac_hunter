import React, { useState, useEffect } from 'react'
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Grid,
  Typography,
  Chip,
  Autocomplete,
  FormControlLabel,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Preview as PreviewIcon,
} from '@mui/icons-material'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'

import { Report, Project, Scan } from '../../types'

const reportSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
  type: z.enum(['executive', 'technical', 'compliance', 'detailed', 'custom']),
  format: z.enum(['pdf', 'html', 'json', 'csv']),
  project_id: z.string().optional(),
  scan_id: z.string().optional(),
  include_charts: z.boolean().default(true),
  include_metadata: z.boolean().default(true),
  template_id: z.string().optional(),
})

type ReportFormData = z.infer<typeof reportSchema>

interface ReportFormProps {
  report?: Report
  projects?: Project[]
  scans?: Scan[]
  onSubmit: (data: ReportFormData) => void
  onCancel: () => void
}

const ReportForm: React.FC<ReportFormProps> = ({
  report,
  projects = [],
  scans = [],
  onSubmit,
  onCancel
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { control, handleSubmit, watch, setValue, formState: { errors } } = useForm<ReportFormData>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      title: report?.title || '',
      description: report?.description || '',
      type: report?.type || 'technical',
      format: report?.format || 'pdf',
      project_id: report?.project_id || '',
      scan_id: report?.scan_id || '',
      include_charts: true,
      include_metadata: true,
      template_id: report?.template_id || '',
    }
  })

  const selectedProjectId = watch('project_id')
  const reportType = watch('type')
  const reportFormat = watch('format')

  const reportTypes = [
    { value: 'executive', label: 'Executive Summary', description: 'High-level overview for executives' },
    { value: 'technical', label: 'Technical Report', description: 'Detailed technical findings and analysis' },
    { value: 'compliance', label: 'Compliance Report', description: 'Regulatory compliance assessment' },
    { value: 'detailed', label: 'Detailed Analysis', description: 'Comprehensive security analysis' },
    { value: 'custom', label: 'Custom Report', description: 'User-defined report template' },
  ]

  const formatOptions = [
    { value: 'pdf', label: 'PDF', description: 'Professional PDF document' },
    { value: 'html', label: 'HTML', description: 'Interactive web report' },
    { value: 'json', label: 'JSON', description: 'Machine-readable data export' },
    { value: 'csv', label: 'CSV', description: 'Spreadsheet-compatible format' },
  ]

  const filteredScans = scans.filter(scan => 
    !selectedProjectId || scan.project_id === selectedProjectId
  )

  const onFormSubmit = async (data: ReportFormData) => {
    setIsSubmitting(true)
    try {
      await onSubmit(data)
      toast.success('Report configuration saved successfully!')
    } catch (error: any) {
      toast.error(`Failed to save report: ${error.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit(onFormSubmit)} sx={{ maxWidth: 800 }}>
      {/* Basic Information */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Basic Information
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Controller
            name="title"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Report Title"
                error={!!errors.title}
                helperText={errors.title?.message}
                required
              />
            )}
          />
        </Grid>
        
        <Grid item xs={12}>
          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                multiline
                rows={3}
                label="Description"
                placeholder="Brief description of this report..."
              />
            )}
          />
        </Grid>
      </Grid>

      {/* Report Configuration */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Report Configuration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Controller
                name="type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Report Type</InputLabel>
                    <Select {...field} label="Report Type">
                      {reportTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          <Box>
                            <Typography variant="body2">{type.label}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {type.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="format"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Output Format</InputLabel>
                    <Select {...field} label="Output Format">
                      {formatOptions.map((format) => (
                        <MenuItem key={format.value} value={format.value}>
                          <Box>
                            <Typography variant="body2">{format.label}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {format.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Data Sources */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Data Sources</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Controller
                name="project_id"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    {...field}
                    options={projects}
                    getOptionLabel={(option) => option.name || ''}
                    value={projects.find(p => p.id === field.value) || null}
                    onChange={(_, value) => field.onChange(value?.id || '')}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Project (Optional)"
                        placeholder="Select a project..."
                      />
                    )}
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_id"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    {...field}
                    options={filteredScans}
                    getOptionLabel={(option) => option.name || ''}
                    value={filteredScans.find(s => s.id === field.value) || null}
                    onChange={(_, value) => field.onChange(value?.id || '')}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Scan (Optional)"
                        placeholder="Select a scan..."
                      />
                    )}
                  />
                )}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Report Options */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Report Options</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Controller
                name="include_charts"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Switch {...field} checked={field.value} />}
                    label="Include Charts and Visualizations"
                  />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="include_metadata"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={<Switch {...field} checked={field.value} />}
                    label="Include Technical Metadata"
                  />
                )}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Preview Alert */}
      {reportType && reportFormat && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            This will generate a <strong>{reportTypes.find(t => t.value === reportType)?.label}</strong> 
            {' '}in <strong>{reportFormat.toUpperCase()}</strong> format.
          </Typography>
        </Alert>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          variant="outlined"
          startIcon={<PreviewIcon />}
          disabled={isSubmitting}
        >
          Preview
        </Button>
        <Button
          type="submit"
          variant="contained"
          startIcon={<SaveIcon />}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Creating...' : report ? 'Update Report' : 'Generate Report'}
        </Button>
      </Box>
    </Box>
  )
}

export default ReportForm