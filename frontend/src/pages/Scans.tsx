import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Skeleton,
  Tooltip,
  Menu,
  ListItemIcon,
  ListItemText,
  Divider,
  Tabs,
  Tab,
  useTheme,
  alpha,
  LinearProgress,
  Badge,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Download as ExportIcon,
  Settings as SettingsIcon,
  BugReport as FindingIcon,
  Assessment as ReportIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  TrendingUp as TrendIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

import { scansAPI } from '../services/api'
import { Scan, Project } from '../types'
import ScanCard from '../components/scans/ScanCard'
import ScanForm from '../components/scans/ScanForm'
import ScanFilters from '../components/scans/ScanFilters'
import ScanStats from '../components/scans/ScanStats'
import ScanLogs from '../components/scans/ScanLogs'
import ScanProgress from '../components/scans/ScanProgress'
import ScanGrid from '../components/scans/ScanGrid'
import ScanMetrics from '../components/scans/ScanMetrics'

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
      id={`scans-tabpanel-${index}`}
      aria-labelledby={`scans-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const Scans: React.FC = () => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [projectFilter, setProjectFilter] = useState<string[]>([])
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showLogsDialog, setShowLogsDialog] = useState(false)
  const [showMetricsDialog, setShowMetricsDialog] = useState(false)
  const [selectedScan, setSelectedScan] = useState<Scan | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch scans with auto-refresh
  const {
    data: scansData,
    isLoading,
    error,
    refetch,
  } = useQuery(['scans'], scansAPI.getAll, {
    refetchInterval: autoRefresh ? 5000 : false, // Refresh every 5 seconds if enabled
  })

  const scans = scansData?.scans || []

  // Create scan mutation
  const createScanMutation = useMutation(scansAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
      toast.success('Scan created and started successfully!')
      setShowCreateDialog(false)
    },
    onError: (error: any) => {
      toast.error(`Failed to create scan: ${error.message}`)
    },
  })

  // Control scan mutations
  const pauseScanMutation = useMutation(scansAPI.pause, {
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
      toast.success('Scan paused successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to pause scan: ${error.message}`)
    },
  })

  const resumeScanMutation = useMutation(scansAPI.resume, {
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
      toast.success('Scan resumed successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to resume scan: ${error.message}`)
    },
  })

  const stopScanMutation = useMutation(scansAPI.stop, {
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
      toast.success('Scan stopped successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to stop scan: ${error.message}`)
    },
  })

  // Delete scan mutation
  const deleteScanMutation = useMutation(scansAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['scans'])
      toast.success('Scan deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete scan: ${error.message}`)
    },
  })

  // Filter scans based on search and filters
  const filteredScans = scans.filter((scan) => {
    const matchesSearch = scan.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scan.target_url?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scan.scan_type?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(scan.status)
    
    const matchesProject = projectFilter.length === 0 || 
                          projectFilter.includes(scan.project_id)
    
    return matchesSearch && matchesStatus && matchesProject
  })

  // Group scans by status
  const scansByStatus = {
    running: filteredScans.filter(s => s.status === 'running'),
    paused: filteredScans.filter(s => s.status === 'paused'),
    completed: filteredScans.filter(s => s.status === 'completed'),
    failed: filteredScans.filter(s => s.status === 'failed'),
    queued: filteredScans.filter(s => s.status === 'queued'),
  }

  const handleCreateScan = (scanData: any) => {
    createScanMutation.mutate(scanData)
  }

  const handlePauseScan = (scanId: string) => {
    pauseScanMutation.mutate(scanId)
  }

  const handleResumeScan = (scanId: string) => {
    resumeScanMutation.mutate(scanId)
  }

  const handleStopScan = (scanId: string) => {
    if (window.confirm('Are you sure you want to stop this scan? This action cannot be undone.')) {
      stopScanMutation.mutate(scanId)
    }
  }

  const handleDeleteScan = (scanId: string) => {
    if (window.confirm('Are you sure you want to delete this scan? This action cannot be undone.')) {
      deleteScanMutation.mutate(scanId)
    }
  }

  const handleViewLogs = (scan: Scan) => {
    setSelectedScan(scan)
    setShowLogsDialog(true)
  }

  const handleViewMetrics = (scan: Scan) => {
    setSelectedScan(scan)
    setShowMetricsDialog(true)
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  // Wrapper functions to convert Scan objects to IDs
  const handleStopScanWrapper = (scan: Scan) => {
    handleStopScan(scan.id)
  }

  const handleDeleteScanWrapper = (scan: Scan) => {
    handleDeleteScan(scan.id)
  }

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh)
    if (!autoRefresh) {
      refetch()
    }
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load scans: {(error as any).message}
        </Alert>
        <Button onClick={() => refetch()} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            Scan Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and control security testing scans in real-time
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={toggleAutoRefresh}
                size="small"
              />
            }
            label="Auto-refresh"
            sx={{ mr: 2 }}
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateDialog(true)}
          >
            New Scan
          </Button>
        </Box>
      </Box>

      {/* Scan Statistics */}
      <ScanStats scans={scans} />

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search scans..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <ScanFilters
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
                projectFilter={projectFilter}
                setProjectFilter={setProjectFilter}
                scans={scans}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="scan tabs">
          <Tab 
            label={`All Scans (${filteredScans.length})`} 
            icon={<SecurityIcon />}
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={scansByStatus.running.length} color="primary">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendIcon />
                  Running
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={`Paused (${scansByStatus.paused.length})`} 
            icon={<PauseIcon />}
            iconPosition="start"
          />
          <Tab 
            label={`Completed (${scansByStatus.completed.length})`} 
            icon={<SuccessIcon />}
            iconPosition="start"
          />
          <Tab 
            label={`Failed (${scansByStatus.failed.length})`} 
            icon={<ErrorIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <ScanGrid
          scans={filteredScans}
          isLoading={isLoading}
          onPause={handlePauseScan}
          onResume={handleResumeScan}
          onStop={handleStopScanWrapper}
          onDelete={handleDeleteScanWrapper}
          onViewLogs={handleViewLogs}
          onViewMetrics={handleViewMetrics}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <ScanGrid
          scans={scansByStatus.running}
          isLoading={isLoading}
          onPause={handlePauseScan}
          onResume={handleResumeScan}
          onStop={handleStopScanWrapper}
          onDelete={handleDeleteScanWrapper}
          onViewLogs={handleViewLogs}
          onViewMetrics={handleViewMetrics}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <ScanGrid
          scans={scansByStatus.paused}
          isLoading={isLoading}
          onPause={handlePauseScan}
          onResume={handleResumeScan}
          onStop={handleStopScanWrapper}
          onDelete={handleDeleteScanWrapper}
          onViewLogs={handleViewLogs}
          onViewMetrics={handleViewMetrics}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <ScanGrid
          scans={scansByStatus.completed}
          isLoading={isLoading}
          onPause={handlePauseScan}
          onResume={handleResumeScan}
          onStop={handleStopScanWrapper}
          onDelete={handleDeleteScanWrapper}
          onViewLogs={handleViewLogs}
          onViewMetrics={handleViewMetrics}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <ScanGrid
          scans={scansByStatus.failed}
          isLoading={isLoading}
          onPause={handlePauseScan}
          onResume={handleResumeScan}
          onStop={handleStopScanWrapper}
          onDelete={handleDeleteScanWrapper}
          onViewLogs={handleViewLogs}
          onViewMetrics={handleViewMetrics}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      {/* Create Scan Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create New Scan</DialogTitle>
        <DialogContent>
          <ScanForm
            onSubmit={handleCreateScan}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Scan Logs Dialog */}
      <Dialog
        open={showLogsDialog}
        onClose={() => setShowLogsDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '80vh' }
        }}
      >
        <DialogTitle>Scan Logs - {selectedScan?.name}</DialogTitle>
        <DialogContent>
          {selectedScan && (
            <ScanLogs scan={selectedScan} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLogsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Scan Metrics Dialog */}
      <Dialog
        open={showMetricsDialog}
        onClose={() => setShowMetricsDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Scan Metrics - {selectedScan?.name}</DialogTitle>
        <DialogContent>
          {selectedScan && (
            <ScanMetrics scan={selectedScan} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowMetricsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Scans
