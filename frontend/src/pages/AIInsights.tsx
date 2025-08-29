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
  Rating,
  Slider,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Psychology as AIIcon,
  TrendingUp as TrendIcon,
  Lightbulb as InsightIcon,
  Security as SecurityIcon,
  BugReport as FindingIcon,
  Assessment as ReportIcon,
  Refresh as RefreshIcon,
  Download as ExportIcon,
  Share as ShareIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Star as StarIcon,
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
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

import { aiInsightsAPI } from '../services/api'
import { AIInsight, Project, Scan } from '../types'
import AIInsightCard from '../components/ai/AIInsightCard'
import AIInsightForm from '../components/ai/AIInsightForm'
import AIInsightFilters from '../components/ai/AIInsightFilters'
import AIInsightStats from '../components/ai/AIInsightStats'
import AIInsightDetails from '../components/ai/AIInsightDetails'
import AIInsightTimeline from '../components/ai/AIInsightTimeline'
import AIInsightExport from '../components/ai/AIInsightExport'

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
      id={`ai-insights-tabpanel-${index}`}
      aria-labelledby={`ai-insights-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const AIInsights: React.FC = () => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string[]>([])
  const [confidenceFilter, setConfidenceFilter] = useState<number[]>([0, 100])
  const [projectFilter, setProjectFilter] = useState<string[]>([])
  const [scanFilter, setScanFilter] = useState<string[]>([])
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailsDialog, setShowDetailsDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [selectedInsight, setSelectedInsight] = useState<AIInsight | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'timeline'>('grid')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [showConfidenceSlider, setShowConfidenceSlider] = useState(false)

  // Fetch AI insights with auto-refresh
  const {
    data: insightsData,
    isLoading,
    error,
    refetch,
  } = useQuery(['ai-insights'], aiInsightsAPI.getAll, {
    refetchInterval: autoRefresh ? 15000 : false, // Refresh every 15 seconds if enabled
  })

  const insights = insightsData?.insights || []

  // Update insight feedback mutations
  const updateFeedbackMutation = useMutation(aiInsightsAPI.updateFeedback, {
    onSuccess: () => {
      queryClient.invalidateQueries(['ai-insights'])
      toast.success('Feedback submitted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to submit feedback: ${error.message}`)
    },
  })

  // Delete insight mutation
  const deleteInsightMutation = useMutation(aiInsightsAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['ai-insights'])
      toast.success('Insight deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete insight: ${error.message}`)
    },
  })

  // Filter insights based on search and filters
  const filteredInsights = insights.filter((insight) => {
    const matchesSearch = insight.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         insight.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         insight.recommendation?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         insight.category?.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesCategory = categoryFilter.length === 0 || categoryFilter.includes(insight.category)
    const matchesConfidence = insight.confidence >= confidenceFilter[0] && insight.confidence <= confidenceFilter[1]
    const matchesProject = projectFilter.length === 0 || projectFilter.includes(insight.project_id)
    const matchesScan = scanFilter.length === 0 || projectFilter.includes(insight.scan_id)
    
    return matchesSearch && matchesCategory && matchesConfidence && matchesProject && matchesScan
  })

  // Group insights by category
  const insightsByCategory = {
    security: filteredInsights.filter(i => i.category === 'security'),
    performance: filteredInsights.filter(i => i.category === 'performance'),
    compliance: filteredInsights.filter(i => i.category === 'compliance'),
    best_practices: filteredInsights.filter(i => i.category === 'best_practices'),
    optimization: filteredInsights.filter(i => i.category === 'optimization'),
  }

  // Group insights by confidence level
  const insightsByConfidence = {
    high: filteredInsights.filter(i => i.confidence >= 80),
    medium: filteredInsights.filter(i => i.confidence >= 50 && i.confidence < 80),
    low: filteredInsights.filter(i => i.confidence < 50),
  }

  const handleCreateInsight = (insightData: any) => {
    // Implementation for creating new AI insights
    toast.success('AI Insight created successfully!')
    setShowCreateDialog(false)
  }

  const handleUpdateFeedback = (insightId: string, feedback: any) => {
    updateFeedbackMutation.mutate({ insightId, feedback })
  }

  const handleDeleteInsight = (insightId: string) => {
    if (window.confirm('Are you sure you want to delete this AI insight? This action cannot be undone.')) {
      deleteInsightMutation.mutate(insightId)
    }
  }

  const handleViewDetails = (insight: AIInsight) => {
    setSelectedInsight(insight)
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

  const handleConfidenceChange = (event: Event, newValue: number | number[]) => {
    setConfidenceFilter(newValue as number[])
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load AI insights: {(error as any).message}
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
            AI Insights & Recommendations
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Intelligent analysis and actionable recommendations powered by AI
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
            Generate Insight
          </Button>
        </Box>
      </Box>

      {/* AI Insights Statistics */}
      <AIInsightStats insights={insights} />

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search AI insights..."
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
              <AIInsightFilters
                categoryFilter={categoryFilter}
                setCategoryFilter={setCategoryFilter}
                confidenceFilter={confidenceFilter}
                setConfidenceFilter={setConfidenceFilter}
                projectFilter={projectFilter}
                setProjectFilter={setProjectFilter}
                scanFilter={scanFilter}
                setScanFilter={setScanFilter}
                insights={insights}
                showConfidenceSlider={showConfidenceSlider}
                setShowConfidenceSlider={setShowConfidenceSlider}
                onConfidenceChange={handleConfidenceChange}
              />
            </Grid>
          </Grid>
          
          {/* Confidence Slider */}
          {showConfidenceSlider && (
            <Box sx={{ mt: 2, px: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Confidence Range: {confidenceFilter[0]}% - {confidenceFilter[1]}%
              </Typography>
              <Slider
                value={confidenceFilter}
                onChange={handleConfidenceChange}
                valueLabelDisplay="auto"
                min={0}
                max={100}
                step={5}
                marks={[
                  { value: 0, label: '0%' },
                  { value: 25, label: '25%' },
                  { value: 50, label: '50%' },
                  { value: 75, label: '75%' },
                  { value: 100, label: '100%' },
                ]}
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="ai insights tabs">
          <Tab 
            label={`All Insights (${filteredInsights.length})`} 
            icon={<AIIcon />}
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={insightsByCategory.security.length} color="error">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SecurityIcon />
                  Security
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={insightsByCategory.performance.length} color="warning">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SpeedIcon />
                  Performance
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={insightsByConfidence.high.length} color="success">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <StarIcon />
                  High Confidence
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
          <Tab 
            label={
              <Badge badgeContent={insightsByCategory.compliance.length} color="info">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircle />
                  Compliance
                </Box>
              </Badge>
            }
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <AIInsightGrid
          insights={filteredInsights}
          isLoading={isLoading}
          onUpdateFeedback={handleUpdateFeedback}
          onDelete={handleDeleteInsight}
          onViewDetails={handleViewDetails}
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
        <AIInsightGrid
          insights={insightsByCategory.security}
          isLoading={isLoading}
          onUpdateFeedback={handleUpdateFeedback}
          onDelete={handleDeleteInsight}
          onViewDetails={handleViewDetails}
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
        <AIInsightGrid
          insights={insightsByCategory.performance}
          isLoading={isLoading}
          onUpdateFeedback={handleUpdateFeedback}
          onDelete={handleDeleteInsight}
          onViewDetails={handleViewDetails}
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
        <AIInsightGrid
          insights={insightsByConfidence.high}
          isLoading={isLoading}
          onUpdateFeedback={handleUpdateFeedback}
          onDelete={handleDeleteInsight}
          onViewDetails={handleViewDetails}
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
        <AIInsightGrid
          insights={insightsByCategory.compliance}
          isLoading={isLoading}
          onUpdateFeedback={handleUpdateFeedback}
          onDelete={handleDeleteInsight}
          onViewDetails={handleViewDetails}
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

      {/* Create AI Insight Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Generate AI Insight</DialogTitle>
        <DialogContent>
          <AIInsightForm
            onSubmit={handleCreateInsight}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* AI Insight Details Dialog */}
      <Dialog
        open={showDetailsDialog}
        onClose={() => setShowDetailsDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>AI Insight Details - {selectedInsight?.title}</DialogTitle>
        <DialogContent>
          {selectedInsight && (
            <AIInsightDetails insight={selectedInsight} />
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
        <DialogTitle>Export AI Insights</DialogTitle>
        <DialogContent>
          <AIInsightExport
            insights={filteredInsights}
            onClose={() => setShowExportDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default AIInsights
