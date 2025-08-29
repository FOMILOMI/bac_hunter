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
  LinearProgress,
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
  Slider,
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
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Settings as SettingsIcon,
  Psychology as AIIcon,
  BugReport as BugIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

import APIService, { ScanRequest, Scan } from '../services/api'
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
      id={`scan-tabpanel-${index}`}
      aria-labelledby={`scan-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const Scans: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const [newScanDialog, setNewScanDialog] = useState(false)
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null)
  const [scanConfig, setScanConfig] = useState<ScanRequest>({
    target: '',
    mode: 'standard',
    max_rps: 2.0,
    phases: ['recon', 'access'],
    enable_ai: true,
  })

  const { connected, addMessage } = useWebSocketStore()
  const queryClient = useQueryClient()

  // Fetch scans data
  const { data: scansData, isLoading: scansLoading, error: scansError } = useQuery({
    queryKey: ['scans'],
    queryFn: () => APIService.listScans({ limit: 100 }),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const { data: targetsData, isLoading: targetsLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: () => APIService.listTargets({ limit: 100 }),
  })

  // Scan mutations
  const createScanMutation = useMutation({
    mutationFn: (scan: ScanRequest) => APIService.createScan(scan),
    onSuccess: (data) => {
      toast.success(`Scan started: ${data.scan_id}`)
      setNewScanDialog(false)
      setScanConfig({
        target: '',
        mode: 'standard',
        max_rps: 2.0,
        phases: ['recon', 'access'],
        enable_ai: true,
      })
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: (error) => {
      toast.error('Failed to start scan')
    },
  })

  const startScanMutation = useMutation({
    mutationFn: (scanId: number) => APIService.startScan(scanId),
    onSuccess: () => {
      toast.success('Scan started successfully')
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: () => {
      toast.error('Failed to start scan')
    },
  })

  const stopScanMutation = useMutation({
    mutationFn: (scanId: number) => APIService.stopScan(scanId),
    onSuccess: () => {
      toast.success('Scan stopped successfully')
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
    onError: () => {
      toast.error('Failed to stop scan')
    },
  })

  // Handle WebSocket messages
  useEffect(() => {
    if (addMessage) {
      // Listen for scan updates
      const handleScanUpdate = (message: any) => {
        if (message.type === 'scan_update') {
          queryClient.invalidateQueries({ queryKey: ['scans'] })
        }
      }
      
      // This would be set up in the WebSocket store
    }
  }, [addMessage, queryClient])

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleCreateScan = () => {
    if (!scanConfig.target.trim()) {
      toast.error('Please enter a target URL')
      return
    }
    createScanMutation.mutate(scanConfig)
  }

  const handleScanAction = (scan: Scan, action: 'start' | 'stop') => {
    if (action === 'start') {
      startScanMutation.mutate(scan.id)
    } else if (action === 'stop') {
      stopScanMutation.mutate(scan.id)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'success'
      case 'completed': return 'primary'
      case 'failed': return 'error'
      case 'pending': return 'warning'
      case 'stopped': return 'default'
      default: return 'default'
    }
  }

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'stealth': return 'info'
      case 'standard': return 'primary'
      case 'aggressive': return 'warning'
      case 'maximum': return 'error'
      default: return 'default'
    }
  }

  const scans = scansData?.scans || []
  const targets = targetsData?.targets || []

  if (scansError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load scans data. Please check your connection and try again.
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
            Scan Management
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <StatusIndicator connected={connected} />
            <Typography variant="body2" color="text.secondary">
              {connected ? 'Connected to BAC Hunter' : 'Disconnected'}
            </Typography>
          </Box>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setNewScanDialog(true)}
        >
          New Scan
        </Button>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="scan management tabs">
          <Tab label="Active Scans" />
          <Tab label="Scan History" />
          <Tab label="Templates" />
          <Tab label="Configuration" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* Active Scans */}
        <Grid container spacing={3}>
          {scansLoading ? (
            // Loading skeletons
            Array.from({ length: 6 }).map((_, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
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
          ) : scans.filter(s => ['running', 'pending'].includes(s.status)).length === 0 ? (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No Active Scans
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Start a new scan to begin security testing
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setNewScanDialog(true)}
                  >
                    Create Scan
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ) : (
            scans
              .filter(s => ['running', 'pending'].includes(s.status))
              .map((scan) => (
                <Grid item xs={12} md={6} lg={4} key={scan.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Typography variant="h6" noWrap sx={{ maxWidth: '70%' }}>
                          {scan.name}
                        </Typography>
                        <Chip
                          label={scan.status}
                          color={getStatusColor(scan.status) as any}
                          size="small"
                        />
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Target: {targets.find(t => t.id === scan.target_id)?.base_url || `ID: ${scan.target_id}`}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Chip
                          label={scan.mode}
                          color={getModeColor(scan.mode) as any}
                          size="small"
                          variant="outlined"
                        />
                        {scan.enable_ai && (
                          <Chip
                            label="AI Enabled"
                            color="secondary"
                            size="small"
                            variant="outlined"
                            icon={<AIIcon />}
                          />
                        )}
                      </Box>

                      {scan.status === 'running' && (
                        <Box sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="body2">Progress</Typography>
                            <Typography variant="body2">{Math.round(scan.progress * 100)}%</Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={scan.progress * 100}
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      )}

                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {scan.status === 'pending' && (
                            <Button
                              size="small"
                              startIcon={<PlayIcon />}
                              onClick={() => handleScanAction(scan, 'start')}
                              disabled={startScanMutation.isPending}
                            >
                              Start
                            </Button>
                          )}
                          {scan.status === 'running' && (
                            <Button
                              size="small"
                              startIcon={<StopIcon />}
                              onClick={() => handleScanAction(scan, 'stop')}
                              disabled={stopScanMutation.isPending}
                              color="error"
                            >
                              Stop
                            </Button>
                          )}
                        </Box>
                        
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="View Details">
                            <IconButton size="small" onClick={() => setSelectedScan(scan)}>
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View Logs">
                            <IconButton size="small">
                              <TimelineIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Scan History */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Scan History
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Target</TableCell>
                    <TableCell>Mode</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {scansLoading ? (
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
                  ) : (
                    scans
                      .filter(s => ['completed', 'failed', 'stopped'].includes(s.status))
                      .map((scan) => (
                        <TableRow key={scan.id}>
                          <TableCell>{scan.name}</TableCell>
                          <TableCell>
                            {targets.find(t => t.id === scan.target_id)?.base_url || `ID: ${scan.target_id}`}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={scan.mode}
                              color={getModeColor(scan.mode) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={scan.status}
                              color={getStatusColor(scan.status) as any}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={scan.progress * 100}
                                sx={{ width: 60, height: 6 }}
                              />
                              <Typography variant="body2">
                                {Math.round(scan.progress * 100)}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            {new Date(scan.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Tooltip title="View Details">
                                <IconButton size="small" onClick={() => setSelectedScan(scan)}>
                                  <ViewIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Download Report">
                                <IconButton size="small">
                                  <DownloadIcon />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete">
                                <IconButton size="small" color="error">
                                  <DeleteIcon />
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

      <TabPanel value={tabValue} index={2}>
        {/* Scan Templates */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Scan Template
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Standard security assessment with AI-powered analysis
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Mode:</strong> Standard
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Phases:</strong> Reconnaissance, Access Control Testing
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>AI:</strong> Enabled
                  </Typography>
                  <Typography variant="body2">
                    <strong>Rate Limit:</strong> 2 RPS
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setScanConfig({
                      target: '',
                      mode: 'standard',
                      max_rps: 2.0,
                      phases: ['recon', 'access'],
                      enable_ai: true,
                    })
                    setNewScanDialog(true)
                  }}
                >
                  Use Template
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Stealth Scan Template
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Low-profile scanning for sensitive environments
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Mode:</strong> Stealth
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Phases:</strong> Reconnaissance only
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>AI:</strong> Disabled
                  </Typography>
                  <Typography variant="body2">
                    <strong>Rate Limit:</strong> 0.5 RPS
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setScanConfig({
                      target: '',
                      mode: 'stealth',
                      max_rps: 0.5,
                      phases: ['recon'],
                      enable_ai: false,
                    })
                    setNewScanDialog(true)
                  }}
                >
                  Use Template
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Comprehensive Audit Template
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Full security assessment with all phases and AI analysis
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Mode:</strong> Aggressive
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Phases:</strong> All phases
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>AI:</strong> Enabled
                  </Typography>
                  <Typography variant="body2">
                    <strong>Rate Limit:</strong> 5 RPS
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setScanConfig({
                      target: '',
                      mode: 'aggressive',
                      max_rps: 5.0,
                      phases: ['recon', 'access', 'audit', 'exploit'],
                      enable_ai: true,
                    })
                    setNewScanDialog(true)
                  }}
                >
                  Use Template
                </Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Custom Template
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create your own scan configuration
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setNewScanDialog(true)}
                >
                  Create Custom
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* Configuration */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Global Scan Configuration
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Default Scan Mode</InputLabel>
                  <Select
                    value="standard"
                    label="Default Scan Mode"
                  >
                    <MenuItem value="stealth">Stealth</MenuItem>
                    <MenuItem value="standard">Standard</MenuItem>
                    <MenuItem value="aggressive">Aggressive</MenuItem>
                    <MenuItem value="maximum">Maximum</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Default Rate Limit</InputLabel>
                  <Select
                    value={2.0}
                    label="Default Rate Limit"
                  >
                    <MenuItem value={0.5}>0.5 RPS (Stealth)</MenuItem>
                    <MenuItem value={1.0}>1.0 RPS (Conservative)</MenuItem>
                    <MenuItem value={2.0}>2.0 RPS (Standard)</MenuItem>
                    <MenuItem value={5.0}>5.0 RPS (Aggressive)</MenuItem>
                    <MenuItem value={10.0}>10.0 RPS (Maximum)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable AI by default"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Obey robots.txt by default"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* New Scan Dialog */}
      <Dialog
        open={newScanDialog}
        onClose={() => setNewScanDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Scan</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Target URL"
                placeholder="https://example.com"
                value={scanConfig.target}
                onChange={(e) => setScanConfig({ ...scanConfig, target: e.target.value })}
                helperText="Enter the target URL or domain to scan"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Scan Mode</InputLabel>
                <Select
                  value={scanConfig.mode}
                  label="Scan Mode"
                  onChange={(e) => setScanConfig({ ...scanConfig, mode: e.target.value })}
                >
                  <MenuItem value="stealth">Stealth (Low profile)</MenuItem>
                  <MenuItem value="standard">Standard (Balanced)</MenuItem>
                  <MenuItem value="aggressive">Aggressive (Thorough)</MenuItem>
                  <MenuItem value="maximum">Maximum (Comprehensive)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Requests per Second"
                type="number"
                value={scanConfig.max_rps}
                onChange={(e) => setScanConfig({ ...scanConfig, max_rps: parseFloat(e.target.value) })}
                inputProps={{ min: 0.1, max: 20, step: 0.1 }}
                helperText="Rate limiting for respectful scanning"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Scan Phases
              </Typography>
              <Grid container spacing={1}>
                {['recon', 'access', 'audit', 'exploit'].map((phase) => (
                  <Grid item key={phase}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={scanConfig.phases.includes(phase)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setScanConfig({
                                ...scanConfig,
                                phases: [...scanConfig.phases, phase]
                              })
                            } else {
                              setScanConfig({
                                ...scanConfig,
                                phases: scanConfig.phases.filter(p => p !== phase)
                              })
                            }
                          }}
                        />
                      }
                      label={phase.charAt(0).toUpperCase() + phase.slice(1)}
                    />
                  </Grid>
                ))}
              </Grid>
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={scanConfig.enable_ai}
                    onChange={(e) => setScanConfig({ ...scanConfig, enable_ai: e.target.checked })}
                  />
                }
                label="Enable AI-powered analysis"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Obey robots.txt"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewScanDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateScan}
            variant="contained"
            disabled={createScanMutation.isPending}
          >
            {createScanMutation.isPending ? 'Creating...' : 'Create Scan'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Scan Details Dialog */}
      {selectedScan && (
        <Dialog
          open={!!selectedScan}
          onClose={() => setSelectedScan(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Scan Details: {selectedScan.name}</DialogTitle>
          <DialogContent>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Status:</strong> {selectedScan.status}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Mode:</strong> {selectedScan.mode}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Target ID:</strong> {selectedScan.target_id}
                </Typography>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Created:</strong> {new Date(selectedScan.created_at).toLocaleString()}
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  <strong>Progress:</strong> {Math.round(selectedScan.progress * 100)}%
                </Typography>
                {selectedScan.started_at && (
                  <Typography variant="subtitle2" gutterBottom>
                    <strong>Started:</strong> {new Date(selectedScan.started_at).toLocaleString()}
                  </Typography>
                )}
                {selectedScan.completed_at && (
                  <Typography variant="subtitle2" gutterBottom>
                    <strong>Completed:</strong> {new Date(selectedScan.completed_at).toLocaleString()}
                  </Typography>
                )}
                {selectedScan.error_message && (
                  <Typography variant="subtitle2" color="error">
                    <strong>Error:</strong> {selectedScan.error_message}
                  </Typography>
                )}
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSelectedScan(null)}>Close</Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  )
}

export default Scans
