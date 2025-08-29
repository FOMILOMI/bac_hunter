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
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Tabs,
  Tab,
  Badge,
  CircularProgress,
} from '@mui/material'
import {
  Psychology as AIIcon,
  Brain as BrainIcon,
  TrendingUp as TrendingUpIcon,
  BugReport as BugIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Code as CodeIcon,
  DataObject as DataIcon,
  AutoAwesome as AutoAwesomeIcon,
  Science as ScienceIcon,
  Analytics as AnalyticsIcon,
  ShowChart as ShowChartIcon,
  Memory as MemoryIcon,
  PsychologyAlt as PsychologyAltIcon,
  Lightbulb as LightbulbIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'

import APIService, { AIAnalysisRequest } from '../services/api'
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
      id={`ai-tabpanel-${index}`}
      aria-labelledby={`ai-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const AIInsights: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const [analysisDialog, setAnalysisDialog] = useState(false)
  const [selectedAnalysis, setSelectedAnalysis] = useState<any>(null)
  const [analysisConfig, setAnalysisConfig] = useState<AIAnalysisRequest>({
    target_id: 0,
    analysis_type: 'comprehensive',
    custom_prompt: '',
  })

  const { connected } = useWebSocketStore()
  const queryClient = useQueryClient()

  // Fetch AI data
  const { data: aiModels, isLoading: modelsLoading } = useQuery({
    queryKey: ['ai-models'],
    queryFn: () => APIService.listAIModels(),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: predictions, isLoading: predictionsLoading } = useQuery({
    queryKey: ['ai-predictions'],
    queryFn: () => APIService.getAIPredictions(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: targetsData, isLoading: targetsLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: () => APIService.listTargets({ limit: 100 }),
  })

  // AI Analysis mutation
  const aiAnalysisMutation = useMutation({
    mutationFn: (request: AIAnalysisRequest) => APIService.triggerAIAnalysis(request),
    onSuccess: (data) => {
      toast.success(`AI analysis started: ${data.analysis_id}`)
      setAnalysisDialog(false)
      queryClient.invalidateQueries({ queryKey: ['ai-predictions'] })
    },
    onError: (error) => {
      toast.error('Failed to start AI analysis')
    },
  })

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleAnalysis = () => {
    if (!analysisConfig.target_id) {
      toast.error('Please select a target')
      return
    }
    aiAnalysisMutation.mutate(analysisConfig)
  }

  // Mock data for charts (replace with real data)
  const modelPerformanceData = [
    { model: 'BAC ML Engine', accuracy: 95, precision: 92, recall: 89, f1: 90 },
    { model: 'Anomaly Detector', accuracy: 87, precision: 85, recall: 88, f1: 86 },
    { model: 'Pattern Analyzer', accuracy: 73, precision: 71, recall: 75, f1: 73 },
    { model: 'Semantic Analyzer', accuracy: 91, precision: 89, recall: 93, f1: 91 },
  ]

  const predictionTrends = [
    { time: '00:00', confidence: 85, accuracy: 92 },
    { time: '04:00', confidence: 88, accuracy: 94 },
    { time: '08:00', confidence: 91, accuracy: 96 },
    { time: '12:00', confidence: 89, accuracy: 93 },
    { time: '16:00', confidence: 93, accuracy: 97 },
    { time: '20:00', confidence: 87, accuracy: 91 },
  ]

  const vulnerabilityDistribution = [
    { type: 'IDOR', count: 45, ai_confidence: 92 },
    { type: 'Auth Bypass', count: 32, ai_confidence: 88 },
    { type: 'Privilege Escalation', count: 28, ai_confidence: 85 },
    { type: 'Info Disclosure', count: 38, ai_confidence: 90 },
    { type: 'Business Logic', count: 25, ai_confidence: 78 },
  ]

  const targets = targetsData?.targets || []
  const models = aiModels?.models || []

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            AI Insights & Intelligence
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <StatusIndicator connected={connected} />
            <Typography variant="body2" color="text.secondary">
              {connected ? 'Connected to BAC Hunter AI Engine' : 'Disconnected'}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => queryClient.invalidateQueries()}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AIIcon />}
            onClick={() => setAnalysisDialog(true)}
          >
            New Analysis
          </Button>
        </Box>
      </Box>

      {/* AI Status Overview */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AIIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="primary">
                {modelsLoading ? <Skeleton width={60} /> : models.length}
              </Typography>
              <Typography color="text.secondary">
                Active AI Models
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BrainIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {predictionsLoading ? <Skeleton width={60} /> : (predictions?.total || 0)}
              </Typography>
              <Typography color="text.secondary">
                AI Predictions
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUpIcon color="info" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="info.main">
                94.2%
              </Typography>
              <Typography color="text.secondary">
                Average Accuracy
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <SpeedIcon color="warning" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="warning.main">
                2.3s
              </Typography>
              <Typography color="text.secondary">
                Avg Response Time
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="AI insights tabs">
          <Tab label="Model Performance" />
          <Tab label="Predictions & Insights" />
          <Tab label="Vulnerability Analysis" />
          <Tab label="AI Training" />
          <Tab label="Configuration" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* Model Performance */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Performance Metrics
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={modelPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="model" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="accuracy" fill="#2196f3" name="Accuracy" />
                    <Bar dataKey="precision" fill="#4caf50" name="Precision" />
                    <Bar dataKey="recall" fill="#ff9800" name="Recall" />
                    <Bar dataKey="f1" fill="#9c27b0" name="F1 Score" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Status
                </Typography>
                <List dense>
                  {modelsLoading ? (
                    Array.from({ length: 4 }).map((_, index) => (
                      <ListItem key={index}>
                        <Skeleton height={20} width="100%" />
                      </ListItem>
                    ))
                  ) : (
                    models.map((model: any) => (
                      <ListItem key={model.name}>
                        <ListItemIcon>
                          <AIIcon color="success" />
                        </ListItemIcon>
                        <ListItemText
                          primary={model.name}
                          secondary={`${model.status} - v${model.version}`}
                        />
                        <Chip
                          label={model.status}
                          color={model.status === 'active' ? 'success' : 'warning'}
                          size="small"
                        />
                      </ListItem>
                    ))
                  )}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Predictions & Insights */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Prediction Confidence Trends
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={predictionTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="confidence" stroke="#2196f3" strokeWidth={2} name="Confidence" />
                    <Line type="monotone" dataKey="accuracy" stroke="#4caf50" strokeWidth={2} name="Accuracy" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent AI Insights
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      <strong>Pattern Detected:</strong> Multiple endpoints with similar response patterns
                    </Typography>
                  </Alert>
                  <Alert severity="warning" sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      <strong>Anomaly:</strong> Unusual response times in auth endpoints
                    </Typography>
                  </Alert>
                  <Alert severity="success">
                    <Typography variant="body2">
                      <strong>Recommendation:</strong> Enable advanced evasion techniques
                    </Typography>
                  </Alert>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Vulnerability Analysis */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Vulnerability Distribution by AI Confidence
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={vulnerabilityDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="count" fill="#f44336" name="Count" />
                    <Bar dataKey="ai_confidence" fill="#2196f3" name="AI Confidence" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Confidence vs Human Validation
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={vulnerabilityDistribution}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="type" />
                    <PolarRadiusAxis />
                    <Radar
                      name="AI Confidence"
                      dataKey="ai_confidence"
                      stroke="#2196f3"
                      fill="#2196f3"
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* AI Training */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Training Progress
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Pattern Analyzer - Training in Progress
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={73}
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    73% complete - ETA: 2 hours
                  </Typography>
                </Box>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Semantic Analyzer - Fine-tuning
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={45}
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    45% complete - ETA: 4 hours
                  </Typography>
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Reinforcement Learning Optimizer - Completed
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={100}
                    sx={{ height: 8, borderRadius: 4, mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    100% complete - Ready for deployment
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Training Statistics
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <MemoryIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Training Data Size"
                      secondary="2.3M samples"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <SpeedIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Training Speed"
                      secondary="1.2k samples/sec"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AnalyticsIcon color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="GPU Utilization"
                      secondary="87%"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        {/* Configuration */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Engine Configuration
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Enable real-time learning"
                  />
                </Box>
                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Auto-update models"
                  />
                </Box>
                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={<Switch />}
                    label="Enable experimental features"
                  />
                </Box>
                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Send anonymous usage data"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Settings
                </Typography>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" gutterBottom>
                    Max Concurrent AI Operations
                  </Typography>
                  <Slider
                    value={5}
                    min={1}
                    max={10}
                    marks
                    valueLabelDisplay="auto"
                    disabled
                  />
                </Box>
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" gutterBottom>
                    AI Response Timeout (seconds)
                  </Typography>
                  <Slider
                    value={30}
                    min={10}
                    max={60}
                    marks
                    valueLabelDisplay="auto"
                    disabled
                  />
                </Box>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Model Cache Size (MB)
                  </Typography>
                  <Slider
                    value={512}
                    min={128}
                    max={1024}
                    marks
                    valueLabelDisplay="auto"
                    disabled
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* AI Analysis Dialog */}
      <Dialog
        open={analysisDialog}
        onClose={() => setAnalysisDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AIIcon color="primary" />
            <Typography variant="h6">
              New AI Analysis
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Target</InputLabel>
                <Select
                  value={analysisConfig.target_id}
                  label="Target"
                  onChange={(e) => setAnalysisConfig({ ...analysisConfig, target_id: e.target.value as number })}
                >
                  <MenuItem value={0}>Select a target</MenuItem>
                  {targets.map((target) => (
                    <MenuItem key={target.id} value={target.id}>
                      {target.name || target.base_url}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Analysis Type</InputLabel>
                <Select
                  value={analysisConfig.analysis_type}
                  label="Analysis Type"
                  onChange={(e) => setAnalysisConfig({ ...analysisConfig, analysis_type: e.target.value })}
                >
                  <MenuItem value="comprehensive">Comprehensive Analysis</MenuItem>
                  <MenuItem value="vulnerability">Vulnerability Assessment</MenuItem>
                  <MenuItem value="behavioral">Behavioral Analysis</MenuItem>
                  <MenuItem value="anomaly">Anomaly Detection</MenuItem>
                  <MenuItem value="pattern">Pattern Recognition</MenuItem>
                  <MenuItem value="custom">Custom Analysis</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Custom Prompt (Optional)"
                placeholder="Enter custom analysis instructions..."
                multiline
                rows={4}
                value={analysisConfig.custom_prompt}
                onChange={(e) => setAnalysisConfig({ ...analysisConfig, custom_prompt: e.target.value })}
                helperText="Provide specific instructions for the AI analysis"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="body2">
                  <strong>AI Analysis Capabilities:</strong> This will trigger advanced AI models to analyze the target for vulnerabilities, patterns, and anomalies. The analysis may take several minutes depending on the complexity.
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialog(false)}>Cancel</Button>
          <Button
            onClick={handleAnalysis}
            variant="contained"
            disabled={aiAnalysisMutation.isPending || !analysisConfig.target_id}
            startIcon={aiAnalysisMutation.isPending ? <CircularProgress size={16} /> : <AIIcon />}
          >
            {aiAnalysisMutation.isPending ? 'Starting Analysis...' : 'Start AI Analysis'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AIInsights
