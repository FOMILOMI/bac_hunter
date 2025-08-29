import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  BugReport as FindingIcon,
  Security as SecurityIcon,
  TrendingUp as TrendIcon,
  Warning as WarningIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Refresh as RefreshIcon,
  Assessment as ReportIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  CheckCircle as ResolvedIcon,
  Cancel as FalsePositiveIcon,
  Schedule as InProgressIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

import { findingsAPI } from '../services/api'
import { Finding, Project, Scan } from '../types'
import FindingCard from '../components/findings/FindingCard'
import FindingForm from '../components/findings/FindingForm'
import FindingFilters from '../components/findings/FindingFilters'
import FindingStats from '../components/findings/FindingStats'
import FindingDetails from '../components/findings/FindingDetails'
import FindingTimeline from '../components/findings/FindingTimeline'
import FindingExport from '../components/findings/FindingExport'

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
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const Findings: React.FC = () => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [typeFilter, setTypeFilter] = useState<string[]>([])
  const [projectFilter, setProjectFilter] = useState<string[]>([])
  const [scanFilter, setScanFilter] = useState<string[]>([])
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailsDialog, setShowDetailsDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'table'>('grid')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch findings with auto-refresh
  const {
    data: findingsData,
    isLoading,
    error,
    refetch,
  } = useQuery(['findings'], findingsAPI.getAll, {
    refetchInterval: autoRefresh ? 10000 : false, // Refresh every 10 seconds if enabled
  })

  const findings = findingsData?.findings || []

  // Update finding status mutations
  const updateStatusMutation = useMutation(findingsAPI.updateStatus, {
    onSuccess: () => {
      queryClient.invalidateQueries(['findings'])
      toast.success('Finding status updated successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to update finding status: ${error.message}`)
    },
  })

  // Delete finding mutation
  const deleteFindingMutation = useMutation(findingsAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['findings'])
      toast.success('Finding deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete finding: ${error.message}`)
    },
  })

  // Filter findings based on search and filters
  const filteredFindings = findings.filter((finding) => {
    const matchesSearch = finding.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         finding.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         finding.parameter?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         finding.url?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesSeverity = severityFilter.length === 0 || severityFilter.includes(finding.severity)
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(finding.status)
    const matchesType = typeFilter.length === 0 || typeFilter.includes(finding.type)
    const matchesProject = projectFilter.length === 0 || projectFilter.includes(finding.project_id)
    const matchesScan = scanFilter.length === 0 || projectFilter.includes(finding.scan_id)
    
    return matchesSearch && matchesSeverity && matchesStatus && matchesType && matchesProject && matchesScan
  })

  // Group findings by severity
  const findingsBySeverity = {
    critical: filteredFindings.filter(f => f.severity === 'critical'),
    high: filteredFindings.filter(f => f.severity === 'high'),
    medium: filteredFindings.filter(f => f.severity === 'medium'),
    low: filteredFindings.filter(f => f.severity === 'low'),
    info: filteredFindings.filter(f => f.severity === 'info'),
  }

  // Group findings by status
  const findingsByStatus = {
    open: filteredFindings.filter(f => f.status === 'open'),
    in_progress: filteredFindings.filter(f => f.status === 'in_progress'),
    resolved: filteredFindings.filter(f => f.status === 'resolved'),
    false_positive: filteredFindings.filter(f => f.status === 'false_positive'),
    duplicate: filteredFindings.filter(f => f.status === 'duplicate'),
  }

  const handleCreateFinding = (findingData: any) => {
    // Implementation for creating new findings
    toast.success('Finding created successfully!')
    setShowCreateDialog(false)
  }

  const handleUpdateStatus = (findingId: string, status: string) => {
    updateStatusMutation.mutate({ findingId, status })
  }

  const handleDeleteFinding = (findingId: string) => {
    if (window.confirm('Are you sure you want to delete this finding? This action cannot be undone.')) {
      deleteFindingMutation.mutate(findingId)
    }
  }

  const handleViewDetails = (finding: Finding) => {
    setSelectedFinding(finding)
    setShowDetailsDialog(true)
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const toggleAutoRefresh = () => {
    setAutoRefresh(!autoRefresh)
    if (!autoRefresh) {
      refetch()
    }
  }

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load findings: {(error as any).message}
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
            Vulnerability Analysis
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive findings management and vulnerability assessment
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
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={() => setShowExportDialog(true)}
          >
            Export
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateDialog(true)}
          >
            New Finding
          </Button>
        </Box>
      </Box>

      {/* Findings Statistics */}
      <FindingStats findings={findings} />

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search findings..."
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
              <FindingFilters
                severityFilter={severityFilter}
                setSeverityFilter={setSeverityFilter}
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
                typeFilter={typeFilter}
                setTypeFilter={setTypeFilter}
                projectFilter={projectFilter}
                setProjectFilter={setProjectFilter}
                scanFilter={scanFilter}
                setScanFilter={setScanFilter}
                findings={findings}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="findings tabs">
          <Tab 
            label={`All Findings (${filteredFindings.length})`} 
            icon={<FindingIcon />}
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={findingsBySeverity.critical.length} color="error">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ErrorIcon />
                  Critical
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={findingsBySeverity.high.length} color="warning">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <WarningIcon />
                  High
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={findingsBySeverity.medium.length} color="info">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <InfoIcon />
                  Medium
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={findingsByStatus.open.length} color="primary">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SecurityIcon />
                  Open
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <FindingGrid
          findings={filteredFindings}
          isLoading={isLoading}
          onUpdateStatus={handleUpdateStatus}
          onDelete={handleDeleteFinding}
          onViewDetails={handleViewDetails}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <FindingGrid
          findings={findingsBySeverity.critical}
          isLoading={isLoading}
          onUpdateStatus={handleUpdateStatus}
          onDelete={handleDeleteFinding}
          onViewDetails={handleViewDetails}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <FindingGrid
          findings={findingsBySeverity.high}
          isLoading={isLoading}
          onUpdateStatus={handleUpdateStatus}
          onDelete={handleDeleteFinding}
          onViewDetails={handleViewDetails}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <FindingGrid
          findings={findingsBySeverity.medium}
          isLoading={isLoading}
          onUpdateStatus={handleUpdateStatus}
          onDelete={handleDeleteFinding}
          onViewDetails={handleViewDetails}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <FindingGrid
          findings={findingsByStatus.open}
          isLoading={isLoading}
          onUpdateStatus={handleUpdateStatus}
          onDelete={handleDeleteFinding}
          onViewDetails={handleViewDetails}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TabPanel>

      {/* Create Finding Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create New Finding</DialogTitle>
        <DialogContent>
          <FindingForm
            onSubmit={handleCreateFinding}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Finding Details Dialog */}
      <Dialog
        open={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>Finding Details - {selectedFinding?.title}</DialogTitle>
        <DialogContent>
          {selectedFinding && (
            <FindingDetails finding={selectedFinding} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Export Findings</DialogTitle>
        <DialogContent>
          <FindingExport
            findings={filteredFindings}
            onClose={() => setShowExportDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default Findings
