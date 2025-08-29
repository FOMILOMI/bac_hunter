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
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  Slider,
  FormGroup,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Assessment as ReportIcon,
  TrendingUp as TrendIcon,
  Download as DownloadIcon,
  Security as SecurityIcon,
  BugReport as FindingIcon,
  Refresh as RefreshIcon,
  Share as ShareIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  AutoAwesome as AutoAwesomeIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
  Email as EmailIcon,
  CloudDownload as CloudDownloadIcon,
  PictureAsPdf as PDFIcon,
  Code as CodeIcon,
  Description as HTMLIcon,
  TableChart as CSVIcon,
  DataObject as JSONIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

import { reportsAPI } from '../services/api'
import { Report, Project, Scan, Finding } from '../types'
import ReportCard from '../components/reports/ReportCard'
import ReportForm from '../components/reports/ReportForm'
import ReportFilters from '../components/reports/ReportFilters'
import ReportStats from '../components/reports/ReportStats'
import ReportDetails from '../components/reports/ReportDetails'
import ReportPreview from '../components/reports/ReportPreview'
import ReportExport from '../components/reports/ReportExport'
import ReportGrid from '../components/reports/ReportGrid'

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
      id={`reports-tabpanel-${index}`}
      aria-labelledby={`reports-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const Reports: React.FC = () => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [typeFilter, setTypeFilter] = useState<string[]>([])
  const [projectFilter, setProjectFilter] = useState<string[]>([])
  const [scanFilter, setScanFilter] = useState<string[]>([])
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailsDialog, setShowDetailsDialog] = useState(false)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'timeline'>('grid')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch reports with auto-refresh
  const {
    data: reportsData,
    isLoading,
    error,
    refetch,
  } = useQuery(['reports'], reportsAPI.getAll, {
    refetchInterval: autoRefresh ? 20000 : false, // Refresh every 20 seconds if enabled
  })

  const reports = reportsData?.reports || []

  // Generate report mutation
  const generateReportMutation = useMutation(reportsAPI.generate, {
    onSuccess: () => {
      queryClient.invalidateQueries(['reports'])
      toast.success('Report generated successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to generate report: ${error.message}`)
    },
  })

  // Delete report mutation
  const deleteReportMutation = useMutation(reportsAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['reports'])
      toast.success('Report deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete report: ${error.message}`)
    },
  })

  // Filter reports based on search and filters
  const filteredReports = reports.filter((report) => {
    const matchesSearch = report.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         report.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         report.type?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(report.status)
    const matchesType = typeFilter.length === 0 || typeFilter.includes(report.type)
    const matchesProject = projectFilter.length === 0 || projectFilter.includes(report.project_id)
    const matchesScan = scanFilter.length === 0 || projectFilter.includes(report.scan_id)
    
    return matchesSearch && matchesStatus && matchesType && matchesProject && matchesScan
  })

  // Group reports by status
  const reportsByStatus = {
    draft: filteredReports.filter(r => r.status === 'draft'),
    generating: filteredReports.filter(r => r.status === 'generating'),
    completed: filteredReports.filter(r => r.status === 'completed'),
    failed: filteredReports.filter(r => r.status === 'failed'),
    scheduled: filteredReports.filter(r => r.status === 'scheduled'),
  }

  // Group reports by type
  const reportsByType = {
    executive: filteredReports.filter(r => r.type === 'executive'),
    technical: filteredReports.filter(r => r.type === 'technical'),
    compliance: filteredReports.filter(r => r.type === 'compliance'),
    detailed: filteredReports.filter(r => r.type === 'detailed'),
    custom: filteredReports.filter(r => r.type === 'custom'),
  }

  const handleCreateReport = (reportData: any) => {
    generateReportMutation.mutate(reportData)
    setShowCreateDialog(false)
  }

  const handleDeleteReport = (reportId: string) => {
    if (window.confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
      deleteReportMutation.mutate(reportId)
    }
  }

  const handleViewDetails = (report: Report) => {
    setSelectedReport(report)
    setShowDetailsDialog(true)
  }

  const handlePreviewReport = (report: Report) => {
    setSelectedReport(report)
    setShowPreviewDialog(true)
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

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load reports: {(error as any).message}
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
            Reports & Analytics
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Generate comprehensive security reports and export findings
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
            Export All
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateDialog(true)}
          >
            Generate Report
          </Button>
        </Box>
      </Box>

      {/* Reports Statistics */}
      <ReportStats reports={reports} />

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search reports..."
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
              <ReportFilters
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
                typeFilter={typeFilter}
                setTypeFilter={setTypeFilter}
                projectFilter={projectFilter}
                setProjectFilter={setProjectFilter}
                scanFilter={scanFilter}
                setScanFilter={setScanFilter}
                reports={reports}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="reports tabs">
          <Tab 
            label={`All Reports (${filteredReports.length})`} 
            icon={<ReportIcon />}
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={reportsByStatus.completed.length} color="success">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircle />
                  Completed
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={reportsByStatus.generating.length} color="warning">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SpeedIcon />
                  Generating
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={reportsByType.executive.length} color="primary">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TrendIcon />
                  Executive
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={reportsByType.technical.length} color="info">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CodeIcon />
                  Technical
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <ReportGrid
          reports={filteredReports}
          isLoading={isLoading}
          onDelete={handleDeleteReport}
          onViewDetails={handleViewDetails}
          onPreview={handlePreviewReport}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10))
            setPage(0)
          }}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <ReportGrid
          reports={reportsByStatus.completed}
          isLoading={isLoading}
          onDelete={handleDeleteReport}
          onViewDetails={handleViewDetails}
          onPreview={handlePreviewReport}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10))
            setPage(0)
          }}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <ReportGrid
          reports={reportsByStatus.generating}
          isLoading={isLoading}
          onDelete={handleDeleteReport}
          onViewDetails={handleViewDetails}
          onPreview={handlePreviewReport}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10))
            setPage(0)
          }}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <ReportGrid
          reports={reportsByType.executive}
          isLoading={isLoading}
          onDelete={handleDeleteReport}
          onViewDetails={handleViewDetails}
          onPreview={handlePreviewReport}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10))
            setPage(0)
          }}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <ReportGrid
          reports={reportsByType.technical}
          isLoading={isLoading}
          onDelete={handleDeleteReport}
          onViewDetails={handleViewDetails}
          onPreview={handlePreviewReport}
          viewMode={viewMode}
          setViewMode={setViewMode}
          page={page}
          rowsPerPage={rowsPerPage}
          onPageChange={(event, newPage) => setPage(newPage)}
          onRowsPerPageChange={(event) => {
            setRowsPerPage(parseInt(event.target.value, 10))
            setPage(0)
          }}
        />
      </TabPanel>

      {/* Create Report Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Generate New Report</DialogTitle>
        <DialogContent>
          <ReportForm
            onSubmit={handleCreateReport}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Report Details Dialog */}
      <Dialog
        open={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>Report Details - {selectedReport?.title}</DialogTitle>
        <DialogContent>
          {selectedReport && (
            <ReportDetails report={selectedReport} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Report Preview Dialog */}
      <Dialog
        open={showPreviewDialog}
        onClose={() => setShowPreviewDialog(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '95vh' }
        }}
      >
        <DialogTitle>Report Preview - {selectedReport?.title}</DialogTitle>
        <DialogContent>
          {selectedReport && (
            <ReportPreview report={selectedReport} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPreviewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Export Reports</DialogTitle>
        <DialogContent>
          <ReportExport
            reports={filteredReports}
            onClose={() => setShowExportDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default Reports
