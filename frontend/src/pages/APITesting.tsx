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
  List,
  ListItem,
  ListItemButton,
  ListItemAvatar,
  Avatar,
  FormHelperText,
  Input,
  OutlinedInput,
  SelectChangeEvent,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Code as CodeIcon,
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
  Description as HTMLIcon,
  TableChart as CSVIcon,
  DataObject as JSONIcon,
  Upload as UploadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Replay as ReplayIcon,
  AccountTree as TreeIcon,
  NetworkCheck as NetworkIcon,
  Http as HttpIcon,
  Lock as LockIcon,
  Public as PublicIcon,
  Send as SendIcon,
  Save as SaveIcon,
  Folder as FolderIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  BugReport as BugIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
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

import { apiTestingAPI } from '../services/api'
import { APIRequest, APIResponse, Project, Scan, Finding } from '../types'
import GraphQLPlayground from '../components/api/GraphQLPlayground'
import RESTRequestBuilder from '../components/api/RESTRequestBuilder'
import RequestHistory from '../components/api/RequestHistory'
import ResponseViewer from '../components/api/ResponseViewer'
import APITestingStats from '../components/api/APITestingStats'
import RequestTemplates from '../components/api/RequestTemplates'
import APIConfiguration from '../components/api/APIConfiguration'

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
      id={`api-testing-tabpanel-${index}`}
      aria-labelledby={`api-testing-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const APITesting: React.FC = () => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [currentRequest, setCurrentRequest] = useState<APIRequest | null>(null)
  const [currentResponse, setCurrentResponse] = useState<APIResponse | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [showConfigDialog, setShowConfigDialog] = useState(false)
  const [showTemplatesDialog, setShowTemplatesDialog] = useState(false)
  const [showHistoryDialog, setShowHistoryDialog] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch API testing history with auto-refresh
  const {
    data: historyData,
    isLoading,
    error,
    refetch,
  } = useQuery(['api-testing-history'], apiTestingAPI.getHistory, {
    refetchInterval: autoRefresh ? 30000 : false, // Refresh every 30 seconds if enabled
  })

  const history = historyData?.history || []

  // Execute API request mutation
  const executeRequestMutation = useMutation(apiTestingAPI.execute, {
    onSuccess: (response) => {
      setCurrentResponse(response)
      setIsExecuting(false)
      toast.success('Request executed successfully!')
      queryClient.invalidateQueries(['api-testing-history'])
    },
    onError: (error: any) => {
      setIsExecuting(false)
      toast.error(`Failed to execute request: ${error.message}`)
    },
  })

  // Save request template mutation
  const saveTemplateMutation = useMutation(apiTestingAPI.saveTemplate, {
    onSuccess: () => {
      toast.success('Request template saved successfully!')
      queryClient.invalidateQueries(['api-testing-templates'])
    },
    onError: (error: any) => {
      toast.error(`Failed to save template: ${error.message}`)
    },
  })

  const handleExecuteRequest = (request: APIRequest) => {
    setCurrentRequest(request)
    setIsExecuting(true)
    executeRequestMutation.mutate(request)
  }

  const handleSaveTemplate = (template: any) => {
    saveTemplateMutation.mutate(template)
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
          Failed to load API testing history: {(error as any).message}
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
            API Testing & GraphQL Playground
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Test APIs, explore GraphQL endpoints, and build custom requests
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
            startIcon={<HistoryIcon />}
            onClick={() => setShowHistoryDialog(true)}
          >
            History
          </Button>
          <Button
            variant="outlined"
            startIcon={<FolderIcon />}
            onClick={() => setShowTemplatesDialog(true)}
          >
            Templates
          </Button>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setShowConfigDialog(true)}
          >
            Config
          </Button>
        </Box>
      </Box>

      {/* API Testing Statistics */}
      <APITestingStats history={history} />

      {/* Main Testing Interface */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="api testing tabs">
              <Tab 
                label="GraphQL Playground" 
                icon={<CodeIcon />}
                iconPosition="start"
              />
              <Tab 
                label="REST API Builder" 
                icon={<HttpIcon />}
                iconPosition="start"
              />
              <Tab 
                label="Response Viewer" 
                icon={<ViewIcon />}
                iconPosition="start"
              />
            </Tabs>
          </Box>

          {/* Tab Panels */}
          <TabPanel value={tabValue} index={0}>
            <GraphQLPlayground
              onExecute={handleExecuteRequest}
              isExecuting={isExecuting}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <RESTRequestBuilder
              onExecute={handleExecuteRequest}
              isExecuting={isExecuting}
              onSaveTemplate={handleSaveTemplate}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <ResponseViewer
              request={currentRequest}
              response={currentResponse}
              isExecuting={isExecuting}
            />
          </TabPanel>
        </CardContent>
      </Card>

      {/* Recent Requests */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon />
            Recent Requests
          </Typography>
          <RequestHistory
            history={history.slice(0, 10)}
            onReplay={handleExecuteRequest}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* Configuration Dialog */}
      <Dialog
        open={showConfigDialog}
        onClose={() => setShowConfigDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>API Testing Configuration</DialogTitle>
        <DialogContent>
          <APIConfiguration
            onSave={() => {
              setShowConfigDialog(false)
              toast.success('Configuration saved successfully!')
            }}
            onCancel={() => setShowConfigDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Templates Dialog */}
      <Dialog
        open={showTemplatesDialog}
        onClose={() => setShowTemplatesDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '80vh' }
        }}
      >
        <DialogTitle>Request Templates</DialogTitle>
        <DialogContent>
          <RequestTemplates
            onSelect={(template) => {
              setCurrentRequest(template)
              setShowTemplatesDialog(false)
              toast.success('Template loaded successfully!')
            }}
            onClose={() => setShowTemplatesDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog
        open={showHistoryDialog}
        onClose={() => setShowHistoryDialog(false)}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>Request History</DialogTitle>
        <DialogContent>
          <RequestHistory
            history={history}
            onReplay={handleExecuteRequest}
            isLoading={isLoading}
            showPagination={true}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHistoryDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default APITesting
