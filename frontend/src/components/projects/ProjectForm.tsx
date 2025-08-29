import React, { useState, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Button,
  Grid,
  Typography,
  Chip,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Alert,
  useTheme,
  alpha,
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Close as CloseIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Settings as SettingsIcon,
  Code as CodeIcon,
} from '@mui/icons-material'

import { Project, ScanConfig, AuthConfig } from '../../types'

// Validation schema
const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(100, 'Project name too long'),
  description: z.string().max(500, 'Description too long').optional(),
  target_url: z.string().url('Invalid URL format'),
  scan_config: z.object({
    scan_type: z.enum(['quick', 'comprehensive', 'stealth', 'aggressive', 'custom']),
    ai_enabled: z.boolean(),
    rl_optimization: z.boolean(),
    max_rps: z.number().min(0.1, 'RPS must be at least 0.1').max(100, 'RPS too high'),
    timeout: z.number().min(10, 'Timeout must be at least 10 seconds').max(3600, 'Timeout too long'),
    phases: z.array(z.enum(['recon', 'access', 'audit', 'exploit', 'report'])).min(1, 'At least one phase required'),
    authentication: z.object({
      type: z.enum(['none', 'basic', 'bearer', 'cookie', 'custom']),
      credentials: z.object({
        username: z.string().optional(),
        password: z.string().optional(),
        token: z.string().optional(),
        cookie: z.string().optional(),
        headers: z.record(z.string()).optional(),
      }).optional(),
    }).optional(),
    custom_headers: z.record(z.string()).optional(),
    proxy: z.object({
      enabled: z.boolean(),
      host: z.string().optional(),
      port: z.number().optional(),
      username: z.string().optional(),
      password: z.string().optional(),
    }).optional(),
  }),
  tags: z.array(z.string()).optional(),
})

type ProjectFormData = z.infer<typeof projectSchema>

interface ProjectFormProps {
  project?: Project
  onSubmit: (data: Partial<Project>) => void
  onCancel: () => void
  isEditing?: boolean
}

const ProjectForm: React.FC<ProjectFormProps> = ({
  project,
  onSubmit,
  onCancel,
  isEditing = false,
}) => {
  const theme = useTheme()
  const [expandedAccordion, setExpandedAccordion] = useState<string | null>('basic')
  const [customHeaders, setCustomHeaders] = useState<Array<{ key: string; value: string }>>([])
  const [tags, setTags] = useState<string[]>(project?.tags || [])
  const [newTag, setNewTag] = useState('')

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setValue,
    reset,
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: project?.name || '',
      description: project?.description || '',
      target_url: project?.target_url || '',
      scan_config: {
        scan_type: project?.scan_config?.scan_type || 'comprehensive',
        ai_enabled: project?.scan_config?.ai_enabled ?? true,
        rl_optimization: project?.scan_config?.rl_optimization ?? true,
        max_rps: project?.scan_config?.max_rps || 2.0,
        timeout: project?.scan_config?.timeout || 300,
        phases: project?.scan_config?.phases || ['recon', 'access'],
        authentication: {
          type: project?.scan_config?.authentication?.type || 'none',
          credentials: project?.scan_config?.authentication?.credentials || {},
        },
        custom_headers: project?.scan_config?.custom_headers || {},
        proxy: {
          enabled: project?.scan_config?.proxy?.enabled || false,
          host: project?.scan_config?.proxy?.host || '',
          port: project?.scan_config?.proxy?.port || 8080,
          username: project?.scan_config?.proxy?.username || '',
          password: project?.scan_config?.proxy?.password || '',
        },
      },
      tags: project?.tags || [],
    },
  })

  const watchedScanType = watch('scan_config.scan_type')
  const watchedAuthType = watch('scan_config.authentication.type')
  const watchedProxyEnabled = watch('scan_config.proxy.enabled')

  useEffect(() => {
    // Update custom headers when they change
    const headersObj = customHeaders.reduce((acc, { key, value }) => {
      if (key.trim()) acc[key.trim()] = value.trim()
      return acc
    }, {} as Record<string, string>)
    setValue('scan_config.custom_headers', headersObj)
  }, [customHeaders, setValue])

  useEffect(() => {
    // Update tags when they change
    setValue('tags', tags)
  }, [tags, setValue])

  const handleFormSubmit = (data: ProjectFormData) => {
    onSubmit(data)
  }

  const addCustomHeader = () => {
    setCustomHeaders([...customHeaders, { key: '', value: '' }])
  }

  const removeCustomHeader = (index: number) => {
    setCustomHeaders(customHeaders.filter((_, i) => i !== index))
  }

  const updateCustomHeader = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...customHeaders]
    updated[index][field] = value
    setCustomHeaders(updated)
  }

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()])
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove))
  }

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      addTag()
    }
  }

  return (
    <Box component="form" onSubmit={handleSubmit(handleFormSubmit)}>
      {/* Basic Information */}
      <Accordion
        expanded={expandedAccordion === 'basic'}
        onChange={() => setExpandedAccordion(expandedAccordion === 'basic' ? null : 'basic')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon />
            Basic Information
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Project Name"
                    fullWidth
                    required
                    error={!!errors.name}
                    helperText={errors.name?.message}
                    placeholder="Enter project name"
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
                    label="Description"
                    fullWidth
                    multiline
                    rows={3}
                    error={!!errors.description}
                    helperText={errors.description?.message || 'Optional project description'}
                    placeholder="Describe your security testing project"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="target_url"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Target URL"
                    fullWidth
                    required
                    error={!!errors.target_url}
                    helperText={errors.target_url?.message}
                    placeholder="https://example.com"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Tags
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                {tags.map((tag, index) => (
                  <Chip
                    key={index}
                    label={tag}
                    onDelete={() => removeTag(tag)}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Add tag"
                  size="small"
                  sx={{ flexGrow: 1 }}
                />
                <Button
                  onClick={addTag}
                  variant="outlined"
                  size="small"
                  disabled={!newTag.trim()}
                >
                  Add
                </Button>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Scan Configuration */}
      <Accordion
        expanded={expandedAccordion === 'scan'}
        onChange={() => setExpandedAccordion(expandedAccordion === 'scan' ? null : 'scan')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon />
            Scan Configuration
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_config.scan_type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Scan Type</InputLabel>
                    <Select {...field} label="Scan Type">
                      <MenuItem value="quick">Quick Scan</MenuItem>
                      <MenuItem value="comprehensive">Comprehensive</MenuItem>
                      <MenuItem value="stealth">Stealth Mode</MenuItem>
                      <MenuItem value="aggressive">Aggressive</MenuItem>
                      <MenuItem value="custom">Custom</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_config.max_rps"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Max Requests Per Second"
                    type="number"
                    fullWidth
                    inputProps={{ step: 0.1, min: 0.1, max: 100 }}
                    error={!!errors.scan_config?.max_rps}
                    helperText={errors.scan_config?.max_rps?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_config.timeout"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Timeout (seconds)"
                    type="number"
                    fullWidth
                    inputProps={{ min: 10, max: 3600 }}
                    error={!!errors.scan_config?.timeout}
                    helperText={errors.scan_config?.timeout?.message}
                  />
                )}
              />
            </Grid>
            <Grid item xs={12}>
              <Controller
                name="scan_config.phases"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Scan Phases</InputLabel>
                    <Select
                      {...field}
                      multiple
                      label="Scan Phases"
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip key={value} label={value} size="small" />
                          ))}
                        </Box>
                      )}
                    >
                      <MenuItem value="recon">Reconnaissance</MenuItem>
                      <MenuItem value="access">Access Control Testing</MenuItem>
                      <MenuItem value="audit">Security Audit</MenuItem>
                      <MenuItem value="exploit">Exploitation</MenuItem>
                      <MenuItem value="report">Reporting</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_config.ai_enabled"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Switch
                        checked={field.value}
                        onChange={field.onChange}
                      />
                    }
                    label="Enable AI Insights"
                  />
                )}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_config.rl_optimization"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Switch
                        checked={field.value}
                        onChange={field.onChange}
                      />
                    }
                    label="Reinforcement Learning"
                  />
                )}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Authentication */}
      <Accordion
        expanded={expandedAccordion === 'auth'}
        onChange={() => setExpandedAccordion(expandedAccordion === 'auth' ? null : 'auth')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon />
            Authentication
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Controller
                name="scan_config.authentication.type"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>Authentication Type</InputLabel>
                    <Select {...field} label="Authentication Type">
                      <MenuItem value="none">No Authentication</MenuItem>
                      <MenuItem value="basic">Basic Auth</MenuItem>
                      <MenuItem value="bearer">Bearer Token</MenuItem>
                      <MenuItem value="cookie">Cookie-based</MenuItem>
                      <MenuItem value="custom">Custom Headers</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            
            {watchedAuthType === 'basic' && (
              <>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="scan_config.authentication.credentials.username"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Username"
                        fullWidth
                        placeholder="Enter username"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="scan_config.authentication.credentials.password"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Password"
                        type="password"
                        fullWidth
                        placeholder="Enter password"
                      />
                    )}
                  />
                </Grid>
              </>
            )}

            {watchedAuthType === 'bearer' && (
              <Grid item xs={12}>
                <Controller
                  name="scan_config.authentication.credentials.token"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Bearer Token"
                      fullWidth
                      placeholder="Enter bearer token"
                    />
                  )}
                />
              </Grid>
            )}

            {watchedAuthType === 'cookie' && (
              <Grid item xs={12}>
                <Controller
                  name="scan_config.authentication.credentials.cookie"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Cookie String"
                      fullWidth
                      placeholder="name=value; name2=value2"
                    />
                  )}
                />
              </Grid>
            )}
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Advanced Settings */}
      <Accordion
        expanded={expandedAccordion === 'advanced'}
        onChange={() => setExpandedAccordion(expandedAccordion === 'advanced' ? null : 'advanced')}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SettingsIcon />
            Advanced Settings
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            {/* Custom Headers */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Custom Headers
              </Typography>
              {customHeaders.map((header, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1 }}>
                  <TextField
                    value={header.key}
                    onChange={(e) => updateCustomHeader(index, 'key', e.target.value)}
                    placeholder="Header name"
                    size="small"
                    sx={{ flexGrow: 1 }}
                  />
                  <TextField
                    value={header.value}
                    onChange={(e) => updateCustomHeader(index, 'value', e.target.value)}
                    placeholder="Header value"
                    size="small"
                    sx={{ flexGrow: 1 }}
                  />
                  <IconButton
                    onClick={() => removeCustomHeader(index)}
                    size="small"
                    color="error"
                  >
                    <CloseIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                onClick={addCustomHeader}
                startIcon={<AddIcon />}
                variant="outlined"
                size="small"
                sx={{ mt: 1 }}
              >
                Add Header
              </Button>
            </Grid>

            {/* Proxy Settings */}
            <Grid item xs={12}>
              <Controller
                name="scan_config.proxy.enabled"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Switch
                        checked={field.value}
                        onChange={field.onChange}
                      />
                    }
                    label="Use Proxy"
                  />
                )}
              />
            </Grid>

            {watchedProxyEnabled && (
              <>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="scan_config.proxy.host"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Proxy Host"
                        fullWidth
                        placeholder="proxy.example.com"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="scan_config.proxy.port"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Proxy Port"
                        type="number"
                        fullWidth
                        inputProps={{ min: 1, max: 65535 }}
                        placeholder="8080"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="scan_config.proxy.username"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Proxy Username"
                        fullWidth
                        placeholder="Optional"
                      />
                    )}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Controller
                    name="scan_config.proxy.password"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        label="Proxy Password"
                        type="password"
                        fullWidth
                        placeholder="Optional"
                      />
                    )}
                  />
                </Grid>
              </>
            )}
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Form Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button onClick={onCancel} variant="outlined">
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : isEditing ? 'Update Project' : 'Create Project'}
        </Button>
      </Box>
    </Box>
  )
}

export default ProjectForm
