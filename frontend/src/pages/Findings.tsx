import React, { useState, useEffect } from 'react'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Badge,
  Rating,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Collapse,
} from '@mui/material'
import {
  BugReport as BugIcon,
  Security as SecurityIcon,
  Psychology as AIIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Code as CodeIcon,
  Link as LinkIcon,
  Description as DescriptionIcon,
  Flag as FlagIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

import APIService, { Finding } from '../services/api'
import { useWebSocketStore } from '../store/webSocketStore'
import StatusIndicator from '../components/StatusIndicator'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`findings-tabpanel-${index}`}
      aria-labelledby={`findings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const Findings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    type: '',
    search: '',
    target_id: '',
  })
  const [expandedFilters, setExpandedFilters] = useState(false)

  const { connected } = useWebSocketStore()
  const queryClient = useQueryClient()

  // Fetch findings data
  const { data: findingsData, isLoading: findingsLoading, error: findingsError } = useQuery({
    queryKey: ['findings', filters],
    queryFn: () => APIService.listFindings({
      limit: 100,
      severity: filters.severity || undefined,
      status: filters.status || undefined,
      target_id: filters.target_id ? parseInt(filters.target_id) : undefined,
    }),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: targetsData, isLoading: targetsLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: () => APIService.listTargets({ limit: 100 }),
  })

  // Update finding mutation
  const updateFindingMutation = useMutation({
    mutationFn: ({ findingId, updates }: { findingId: number; updates: Partial<Finding> }) =>
      APIService.updateFinding(findingId, updates),
    onSuccess: () => {
      toast.success('Finding updated successfully')
      queryClient.invalidateQueries({ queryKey: ['findings'] })
    },
    onError: () => {
      toast.error('Failed to update finding')
    },
  })

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleUpdateFinding = (findingId: number, updates: Partial<Finding>) => {
    updateFindingMutation.mutate({ findingId, updates })
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'error'
      case 'high': return 'error'
      case 'medium': return 'warning'
      case 'low': return 'info'
      case 'info': return 'default'
      default: return 'default'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical': return <ErrorIcon />
      case 'high': return <WarningIcon />
      case 'medium': return <WarningIcon />
      case 'low': return <InfoIcon />
      case 'info': return <InfoIcon />
      default: return <InfoIcon />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open': return 'error'
      case 'investigating': return 'warning'
      case 'resolved': return 'success'
      case 'false_positive': return 'default'
      default: return 'default'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'idor': return <SecurityIcon />
      case 'auth_bypass': return <BugIcon />
      case 'privilege_escalation': return <SecurityIcon />
      case 'information_disclosure': return <DescriptionIcon />
      case 'endpoint': return <LinkIcon />
      default: return <BugIcon />
    }
  }

  const findings = findingsData?.findings || []
  const targets = targetsData?.targets || []

  // Filter findings based on search
  const filteredFindings = findings.filter(finding => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      return (
        finding.url.toLowerCase().includes(searchLower) ||
        finding.evidence.toLowerCase().includes(searchLower) ||
        finding.type.toLowerCase().includes(searchLower)
      )
    }
    return true
  })

  // Group findings by severity
  const findingsBySeverity = {
    critical: filteredFindings.filter(f => f.severity.toLowerCase() === 'critical'),
    high: filteredFindings.filter(f => f.severity.toLowerCase() === 'high'),
    medium: filteredFindings.filter(f => f.severity.toLowerCase() === 'medium'),
    low: filteredFindings.filter(f => f.severity.toLowerCase() === 'low'),
    info: filteredFindings.filter(f => f.severity.toLowerCase() === 'info'),
  }

  if (findingsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load findings data. Please check your connection and try again.
        </Alert>
        <Button variant="contained" onClick={() => queryClient.invalidateQueries()}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Security Findings
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <StatusIndicator connected={connected} />
            <Typography variant="body2" color="text.secondary">
              {connected ? 'Connected to BAC Hunter' : 'Disconnected'}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {/* Export findings */}}
          >
            Export
          </Button>
          <Button
            variant="contained"
            startIcon={<AIIcon />}
            onClick={() => {/* AI analysis */}}
          >
            AI Analysis
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Filters</Typography>
            <Button
              startIcon={<FilterIcon />}
              onClick={() => setExpandedFilters(!expandedFilters)}
              size="small"
            >
              {expandedFilters ? 'Hide' : 'Show'} Filters
            </Button>
          </Box>
          
          <Collapse in={expandedFilters}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Search"
                  placeholder="Search findings..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Severity</InputLabel>
                  <Select
                    value={filters.severity}
                    label="Severity"
                    onChange={(e) => handleFilterChange('severity', e.target.value)}
                  >
                    <MenuItem value="">All Severities</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="info">Info</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status}
                    label="Status"
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                  >
                    <MenuItem value="">All Statuses</MenuItem>
                    <MenuItem value="open">Open</MenuItem>
                    <MenuItem value="investigating">Investigating</MenuItem>
                    <MenuItem value="resolved">Resolved</MenuItem>
                    <MenuItem value="false_positive">False Positive</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Target</InputLabel>
                  <Select
                    value={filters.target_id}
                    label="Target"
                    onChange={(e) => handleFilterChange('target_id', e.target.value)}
                  >
                    <MenuItem value="">All Targets</MenuItem>
                    {targets.map((target) => (
                      <MenuItem key={target.id} value={target.id}>
                        {target.name || target.base_url}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Collapse>
        </CardContent>
      </Card>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                Total
              </Typography>
              <Typography variant="h4" color="primary">
                {findingsLoading ? <Skeleton width={40} /> : filteredFindings.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                Critical
              </Typography>
              <Typography variant="h4" color="error">
                {findingsLoading ? <Skeleton width={40} /> : findingsBySeverity.critical.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                High
              </Typography>
              <Typography variant="h4" color="error">
                {findingsLoading ? <Skeleton width={40} /> : findingsBySeverity.high.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                Medium
              </Typography>
              <Typography variant="h4" color="warning.main">
                {findingsLoading ? <Skeleton width={40} /> : findingsBySeverity.medium.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                Low
              </Typography>
              <Typography variant="h4" color="info.main">
                {findingsLoading ? <Skeleton width={40} /> : findingsBySeverity.low.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="text.secondary" gutterBottom>
                Info
              </Typography>
              <Typography variant="h4" color="text.secondary">
                {findingsLoading ? <Skeleton width={40} /> : findingsBySeverity.info.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="findings management tabs">
          <Tab label="All Findings" />
          <Tab label="Critical & High" />
          <Tab label="AI Insights" />
          <Tab label="Reports" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* All Findings */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              All Findings ({filteredFindings.length})
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Severity</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>URL</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {findingsLoading ? (
                    Array.from({ length: 5 }).map((_, index) => (
                      <TableRow key={index}>
                        <TableCell><Skeleton height={20} /></TableCell>
                        <TableCell><Skeleton height={20} /></TableCell>
                        <TableCell><Skeleton height={20} /></TableCell>
                        <TableCell><Skeleton height={20} /></TableCell>
                        <TableCell><Skeleton height={20} /></TableCell>
                        <TableCell><Skeleton height={20} /></TableCell>
                        <TableCell><Skeleton height={20} /></TableCell>
                      </TableRow>
                    ))
                  ) : filteredFindings.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} sx={{ textAlign: 'center', py: 4 }}>
                        <Typography variant="body1" color="text.secondary">
                          No findings found matching your criteria
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredFindings.map((finding) => (
                      <TableRow key={finding.id} hover>
                        <TableCell>
                          <Chip
                            icon={getSeverityIcon(finding.severity)}
                            label={finding.severity}
                            color={getSeverityColor(finding.severity) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getTypeIcon(finding.type)}
                            <Typography variant="body2">{finding.type}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Tooltip title={finding.url}>
                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                              {finding.url}
                            </Typography>
                          </Tooltip>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={finding.status}
                            color={getStatusColor(finding.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Rating
                            value={Math.ceil(finding.score / 20)}
                            readOnly
                            size="small"
                            max={5}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {finding.score.toFixed(1)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {new Date(finding.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="View Details">
                              <IconButton size="small" onClick={() => setSelectedFinding(finding)}>
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Edit">
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Mark as False Positive">
                              <IconButton 
                                size="small" 
                                color={finding.false_positive ? "success" : "default"}
                                onClick={() => handleUpdateFinding(finding.id, { 
                                  false_positive: !finding.false_positive 
                                })}
                              >
                                <FlagIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Critical & High Findings */}
        <Grid container spacing={3}>
          {findingsLoading ? (
            Array.from({ length: 6 }).map((_, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card>
                  <CardContent>
                    <Skeleton height={24} width="60%" sx={{ mb: 1 }} />
                    <Skeleton height={20} width="40%" sx={{ mb: 2 }} />
                    <Skeleton height={16} width="80%" sx={{ mb: 1 }} />
                    <Skeleton height={16} width="60%" />
                  </CardContent>
                </Card>
              </Grid>
            ))
          ) : (
            [...findingsBySeverity.critical, ...findingsBySeverity.high].map((finding) => (
              <Grid item xs={12} md={6} key={finding.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Chip
                        icon={getSeverityIcon(finding.severity)}
                        label={finding.severity}
                        color={getSeverityColor(finding.severity) as any}
                        size="small"
                      />
                      <Chip
                        label={finding.status}
                        color={getStatusColor(finding.status) as any}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                    
                    <Typography variant="h6" gutterBottom>
                      {finding.type}
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {finding.url}
                    </Typography>
                    
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {finding.evidence.substring(0, 150)}...
                    </Typography>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Rating
                        value={Math.ceil(finding.score / 20)}
                        readOnly
                        size="small"
                        max={5}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Score: {finding.score.toFixed(1)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                      <Button
                        size="small"
                        startIcon={<ViewIcon />}
                        onClick={() => setSelectedFinding(finding)}
                      >
                        View Details
                      </Button>
                      <Button
                        size="small"
                        startIcon={<AIIcon />}
                        onClick={() => {/* AI analysis */}}
                      >
                        AI Analysis
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* AI Insights */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI-Powered Analysis
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Pattern Detection:</strong> AI has identified similar vulnerability patterns across multiple endpoints.
                  </Typography>
                </Alert>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Risk Assessment:</strong> High-risk findings detected in authentication flows.
                  </Typography>
                </Alert>
                <Alert severity="success">
                  <Typography variant="body2">
                    <strong>Recommendation:</strong> Consider implementing additional access controls for sensitive endpoints.
                  </Typography>
                </Alert>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Model Status
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <AIIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="BAC ML Engine"
                      secondary="Active - 95% accuracy"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AIIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Anomaly Detector"
                      secondary="Active - 87% accuracy"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AIIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Pattern Analyzer"
                      secondary="Training - 73% accuracy"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* Reports */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Finding Reports
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Executive Summary
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      High-level overview of security posture and critical findings
                    </Typography>
                    <Button variant="outlined" startIcon={<DownloadIcon />}>
                      Generate PDF
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Technical Report
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Detailed technical analysis with remediation steps
                    </Typography>
                    <Button variant="outlined" startIcon={<DownloadIcon />}>
                      Generate HTML
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Compliance Report
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      OWASP Top 10 and industry compliance mapping
                    </Typography>
                    <Button variant="outlined" startIcon={<DownloadIcon />}>
                      Generate Report
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Custom Export
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Export findings in various formats (CSV, JSON, SARIF)
                    </Typography>
                    <Button variant="outlined" startIcon={<DownloadIcon />}>
                      Export Data
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Finding Details Dialog */}
      {selectedFinding && (
        <Dialog
          open={!!selectedFinding}
          onClose={() => setSelectedFinding(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {getTypeIcon(selectedFinding.type)}
              <Typography variant="h6">
                {selectedFinding.type} - {selectedFinding.severity} Severity
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>URL:</strong>
                </Typography>
                <Typography variant="body2" sx={{ mb: 2, wordBreak: 'break-all' }}>
                  {selectedFinding.url}
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Status:</strong>
                </Typography>
                <Chip
                  label={selectedFinding.status}
                  color={getStatusColor(selectedFinding.status) as any}
                  sx={{ mb: 2 }}
                />
                
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Score:</strong>
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Rating
                    value={Math.ceil(selectedFinding.score / 20)}
                    readOnly
                    max={5}
                  />
                  <Typography variant="body2">
                    {selectedFinding.score.toFixed(1)}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Created:</strong>
                </Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {new Date(selectedFinding.created_at).toLocaleString()}
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Updated:</strong>
                </Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {new Date(selectedFinding.updated_at).toLocaleString()}
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  <strong>False Positive:</strong>
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={selectedFinding.false_positive}
                      onChange={(e) => handleUpdateFinding(selectedFinding.id, {
                        false_positive: e.target.checked
                      })}
                    />
                  }
                  label="Mark as false positive"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Evidence:</strong>
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                  <Typography variant="body2" fontFamily="monospace">
                    {selectedFinding.evidence}
                  </Typography>
                </Paper>
              </Grid>
              
              {selectedFinding.notes && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    <strong>Notes:</strong>
                  </Typography>
                  <Typography variant="body2">
                    {selectedFinding.notes}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSelectedFinding(null)}>Close</Button>
            <Button
              variant="contained"
              startIcon={<AIIcon />}
              onClick={() => {/* AI analysis */}}
            >
              AI Analysis
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  )
}

export default Findings
