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
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Checkbox,
  Slider,
  FormGroup,
  List,
  ListItem,
  ListItemButton,
  ListItemAvatar,
  Avatar,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Storage as SessionIcon,
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
  Upload as UploadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Replay as ReplayIcon,
  Timeline as TimelineIcon,
  AccountTree as TreeIcon,
  NetworkCheck as NetworkIcon,
  Http as HttpIcon,
  Lock as LockIcon,
  Public as PublicIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

import { sessionsAPI } from '../services/api'
import { Session, Project, Scan, Finding } from '../types'
import SessionCard from '../components/sessions/SessionCard'
import SessionForm from '../components/sessions/SessionForm'
import SessionFilters from '../components/sessions/SessionFilters'
import SessionStats from '../components/sessions/SessionStats'
import SessionDetails from '../components/sessions/SessionDetails'
import SessionTimeline from '../components/sessions/SessionTimeline'
import SessionExport from '../components/sessions/SessionExport'
import SessionVisualizer from '../components/sessions/SessionVisualizer'

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
      id={`sessions-tabpanel-${index}`}
      aria-labelledby={`sessions-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const Sessions: React.FC = () => {
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
  const [showVisualizerDialog, setShowVisualizerDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [selectedSession, setSelectedSession] = useState<Session | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'timeline' | 'tree'>('grid')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch sessions with auto-refresh
  const {
    data: sessionsData,
    isLoading,
    error,
    refetch,
  } = useQuery(['sessions'], sessionsAPI.getAll, {
    refetchInterval: autoRefresh ? 15000 : false, // Refresh every 15 seconds if enabled
  })

  const sessions = sessionsData?.sessions || []

  // Create session mutation
  const createSessionMutation = useMutation(sessionsAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions'])
      toast.success('Session created successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to create session: ${error.message}`)
    },
  })

  // Delete session mutation
  const deleteSessionMutation = useMutation(sessionsAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions'])
      toast.success('Session deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete session: ${error.message}`)
    },
  })

  // Replay session mutation
  const replaySessionMutation = useMutation(sessionsAPI.replay, {
    onSuccess: () => {
      queryClient.invalidateQueries(['sessions'])
      toast.success('Session replay started successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to replay session: ${error.message}`)
    },
  })

  // Filter sessions based on search and filters
  const filteredSessions = sessions.filter((session) => {
    const matchesSearch = session.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.type?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(session.status)
    const matchesType = typeFilter.length === 0 || typeFilter.includes(session.type)
    const matchesProject = projectFilter.length === 0 || projectFilter.includes(session.project_id)
    const matchesScan = scanFilter.length === 0 || projectFilter.includes(session.scan_id)
    
    return matchesSearch && matchesStatus && matchesType && matchesProject && matchesScan
  })

  // Group sessions by status
  const sessionsByStatus = {
    active: filteredSessions.filter(s => s.status === 'active'),
    inactive: filteredSessions.filter(s => s.status === 'inactive'),
    expired: filteredSessions.filter(s => s.status === 'expired'),
    suspended: filteredSessions.filter(s => s.status === 'suspended'),
  }

  // Group sessions by type
  const sessionsByType = {
    http: filteredSessions.filter(s => s.type === 'http'),
    https: filteredSessions.filter(s => s.type === 'https'),
    websocket: filteredSessions.filter(s => s.type === 'websocket'),
    api: filteredSessions.filter(s => s.type === 'api'),
    custom: filteredSessions.filter(s => s.type === 'custom'),
  }

  const handleCreateSession = (sessionData: any) => {
    createSessionMutation.mutate(sessionData)
    setShowCreateDialog(false)
  }

  const handleDeleteSession = (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      deleteSessionMutation.mutate(sessionId)
    }
  }

  const handleReplaySession = (sessionId: string) => {
    replaySessionMutation.mutate(sessionId)
  }

  const handleViewDetails = (session: Session) => {
    setSelectedSession(session)
    setShowDetailsDialog(true)
  }

  const handleVisualizeSession = (session: Session) => {
    setSelectedSession(session)
    setShowVisualizerDialog(true)
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
          Failed to load sessions: {(error as any).message}
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
            Session Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage, visualize, and manipulate HTTP sessions and requests
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
            startIcon={<UploadIcon />}
            onClick={() => setShowExportDialog(true)}
          >
            Import/Export
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowCreateDialog(true)}
          >
            New Session
          </Button>
        </Box>
      </Box>

      {/* Sessions Statistics */}
      <SessionStats sessions={sessions} />

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search sessions..."
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
              <SessionFilters
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
                typeFilter={typeFilter}
                setTypeFilter={setTypeFilter}
                projectFilter={projectFilter}
                setProjectFilter={setProjectFilter}
                scanFilter={scanFilter}
                setScanFilter={setScanFilter}
                sessions={sessions}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="sessions tabs">
          <Tab 
            label={`All Sessions (${filteredSessions.length})`} 
            icon={<SessionIcon />}
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={sessionsByStatus.active.length} color="success">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircle />
                  Active
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={sessionsByType.http.length} color="primary">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HttpIcon />
                  HTTP
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={sessionsByType.https.length} color="info">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LockIcon />
                  HTTPS
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={sessionsByType.api.length} color="warning">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CodeIcon />
                  API
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <SessionGrid
          sessions={filteredSessions}
          isLoading={isLoading}
          onDelete={handleDeleteSession}
          onViewDetails={handleViewDetails}
          onVisualize={handleVisualizeSession}
          onReplay={handleReplaySession}
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
        <SessionGrid
          sessions={sessionsByStatus.active}
          isLoading={isLoading}
          onDelete={handleDeleteSession}
          onViewDetails={handleViewDetails}
          onVisualize={handleVisualizeSession}
          onReplay={handleReplaySession}
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
        <SessionGrid
          sessions={sessionsByType.http}
          isLoading={isLoading}
          onDelete={handleDeleteSession}
          onViewDetails={handleViewDetails}
          onVisualize={handleVisualizeSession}
          onReplay={handleReplaySession}
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
        <SessionGrid
          sessions={sessionsByType.https}
          isLoading={isLoading}
          onDelete={handleDeleteSession}
          onViewDetails={handleViewDetails}
          onVisualize={handleVisualizeSession}
          onReplay={handleReplaySession}
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
        <SessionGrid
          sessions={sessionsByType.api}
          isLoading={isLoading}
          onDelete={handleDeleteSession}
          onViewDetails={handleViewDetails}
          onVisualize={handleVisualizeSession}
          onReplay={handleReplaySession}
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

      {/* Create Session Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create New Session</DialogTitle>
        <DialogContent>
          <SessionForm
            onSubmit={handleCreateSession}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Session Details Dialog */}
      <Dialog
        open={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>Session Details - {selectedSession?.name}</DialogTitle>
        <DialogContent>
          {selectedSession && (
            <SessionDetails session={selectedSession} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Session Visualizer Dialog */}
      <Dialog
        open={showVisualizerDialog}
        onClose={() => setShowVisualizerDialog(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '95vh' }
        }}
      >
        <DialogTitle>Session Visualization - {selectedSession?.name}</DialogTitle>
        <DialogContent>
          {selectedSession && (
            <SessionVisualizer session={selectedSession} />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowVisualizerDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Import/Export Dialog */}
      <Dialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Import/Export Sessions</DialogTitle>
        <DialogContent>
          <SessionExport
            sessions={filteredSessions}
            onClose={() => setShowExportDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default Sessions
