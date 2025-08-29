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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  LinearProgress,
} from '@mui/material'
import {
  Folder as FolderIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  PlayArrow as PlayIcon,
  Settings as SettingsIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  BugReport as BugIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  Psychology as AIIcon,
  ExpandMore as ExpandMoreIcon,
  Link as LinkIcon,
  Description as DescriptionIcon,
  CalendarToday as CalendarIcon,
  Schedule as ScheduleIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

import APIService, { Project, Target, Scan } from '../services/api'
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
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const Projects: React.FC = () => {
  const [tabValue, setTabValue] = useState(0)
  const [newProjectDialog, setNewProjectDialog] = useState(false)
  const [editProjectDialog, setEditProjectDialog] = useState(false)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [projectForm, setProjectForm] = useState({
    name: '',
    description: '',
    targets: [] as number[],
    configuration: {},
  })

  const { connected } = useWebSocketStore()
  const queryClient = useQueryClient()

  // Fetch data
  const { data: projectsData, isLoading: projectsLoading, error: projectsError } = useQuery({
    queryKey: ['projects'],
    queryFn: () => APIService.listProjects(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: targetsData, isLoading: targetsLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: () => APIService.listTargets({ limit: 100 }),
  })

  const { data: scansData, isLoading: scansLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: () => APIService.listScans({ limit: 100 }),
  })

  // Mutations
  const createProjectMutation = useMutation({
    mutationFn: (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) =>
      APIService.createProject(project),
    onSuccess: () => {
      toast.success('Project created successfully')
      setNewProjectDialog(false)
      setProjectForm({ name: '', description: '', targets: [], configuration: {} })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: () => {
      toast.error('Failed to create project')
    },
  })

  const updateProjectMutation = useMutation({
    mutationFn: ({ projectId, updates }: { projectId: number; updates: Partial<Project> }) =>
      APIService.updateProject(projectId, updates),
    onSuccess: () => {
      toast.success('Project updated successfully')
      setEditProjectDialog(false)
      setSelectedProject(null)
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: () => {
      toast.error('Failed to update project')
    },
  })

  const deleteProjectMutation = useMutation({
    mutationFn: (projectId: number) => APIService.deleteProject(projectId),
    onSuccess: () => {
      toast.success('Project deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: () => {
      toast.error('Failed to delete project')
    },
  })

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleCreateProject = () => {
    if (!projectForm.name.trim()) {
      toast.error('Please enter a project name')
      return
    }
    createProjectMutation.mutate(projectForm)
  }

  const handleEditProject = (project: Project) => {
    setSelectedProject(project)
    setProjectForm({
      name: project.name,
      description: project.description || '',
      targets: project.targets || [],
      configuration: project.configuration || {},
    })
    setEditProjectDialog(true)
  }

  const handleUpdateProject = () => {
    if (!selectedProject) return
    updateProjectMutation.mutate({
      projectId: selectedProject.id,
      updates: projectForm,
    })
  }

  const handleDeleteProject = (projectId: number) => {
    if (window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      deleteProjectMutation.mutate(projectId)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'success'
      case 'paused': return 'warning'
      case 'archived': return 'default'
      default: return 'default'
    }
  }

  const projects = projectsData || []
  const targets = targetsData?.targets || []
  const scans = scansData?.scans || []

  if (projectsError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load projects data. Please check your connection and try again.
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
            Project Management
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
          onClick={() => setNewProjectDialog(true)}
        >
          New Project
        </Button>
      </Box>

      {/* Project Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <FolderIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="primary">
                {projectsLoading ? <Skeleton width={60} /> : projects.length}
              </Typography>
              <Typography color="text.secondary">
                Total Projects
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <LinkIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {targetsLoading ? <Skeleton width={60} /> : targets.length}
              </Typography>
              <Typography color="text.secondary">
                Total Targets
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TimelineIcon color="info" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="info.main">
                {scansLoading ? <Skeleton width={60} /> : scans.length}
              </Typography>
              <Typography color="text.secondary">
                Total Scans
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <BugIcon color="warning" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" color="warning.main">
                {projectsLoading ? <Skeleton width={60} /> : 
                  projects.reduce((acc, project) => acc + (project.targets?.length || 0), 0)
                }
              </Typography>
              <Typography color="text.secondary">
                Active Targets
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="project management tabs">
          <Tab label="All Projects" />
          <Tab label="Project Analytics" />
          <Tab label="Templates" />
          <Tab label="Settings" />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* All Projects */}
        <Grid container spacing={3}>
          {projectsLoading ? (
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
          ) : projects.length === 0 ? (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <FolderIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No Projects Created
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Create your first project to start organizing your security testing activities
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setNewProjectDialog(true)}
                  >
                    Create Project
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ) : (
            projects.map((project) => (
              <Grid item xs={12} md={6} lg={4} key={project.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6" noWrap sx={{ maxWidth: '70%' }}>
                        {project.name}
                      </Typography>
                      <Chip
                        label={project.status}
                        color={getStatusColor(project.status) as any}
                        size="small"
                      />
                    </Box>
                    
                    {project.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {project.description}
                      </Typography>
                    )}
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <LinkIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {project.targets?.length || 0} targets
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <TimelineIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {scans.filter(s => project.targets?.includes(s.target_id)).length} scans
                      </Typography>
                    </Box>
                    
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                      Created: {new Date(project.created_at).toLocaleDateString()}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          size="small"
                          startIcon={<PlayIcon />}
                          onClick={() => {/* Start project scan */}}
                        >
                          Scan
                        </Button>
                        <Button
                          size="small"
                          startIcon={<AssessmentIcon />}
                          onClick={() => {/* View project report */}}
                        >
                          Report
                        </Button>
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="View Details">
                          <IconButton size="small" onClick={() => setSelectedProject(project)}>
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Project">
                          <IconButton size="small" onClick={() => handleEditProject(project)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Project">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDeleteProject(project.id)}
                          >
                            <DeleteIcon />
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
        {/* Project Analytics */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Project Activity Overview
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Project</TableCell>
                        <TableCell>Targets</TableCell>
                        <TableCell>Scans</TableCell>
                        <TableCell>Findings</TableCell>
                        <TableCell>Last Activity</TableCell>
                        <TableCell>Health</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {projectsLoading ? (
                        Array.from({ length: 5 }).map((_, index) => (
                          <TableRow key={index}>
                            <TableCell><Skeleton height={20} /></TableCell>
                            <TableCell><Skeleton height={20} /></TableCell>
                            <TableCell><Skeleton height={20} /></TableCell>
                            <TableCell><Skeleton height={20} /></TableCell>
                            <TableCell><Skeleton height={20} /></TableCell>
                            <TableCell><Skeleton height={20} /></TableCell>
                          </TableRow>
                        ))
                      ) : (
                        projects.map((project) => {
                          const projectScans = scans.filter(s => project.targets?.includes(s.target_id))
                          const lastScan = projectScans.sort((a, b) => 
                            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                          )[0]
                          
                          return (
                            <TableRow key={project.id}>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Avatar sx={{ width: 32, height: 32 }}>
                                    {project.name.charAt(0).toUpperCase()}
                                  </Avatar>
                                  <Typography variant="body2">{project.name}</Typography>
                                </Box>
                              </TableCell>
                              <TableCell>{project.targets?.length || 0}</TableCell>
                              <TableCell>{projectScans.length}</TableCell>
                              <TableCell>
                                {/* This would need to be calculated from findings data */}
                                <Typography variant="body2">-</Typography>
                              </TableCell>
                              <TableCell>
                                {lastScan ? new Date(lastScan.created_at).toLocaleDateString() : 'Never'}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={project.status}
                                  color={getStatusColor(project.status) as any}
                                  size="small"
                                />
                              </TableCell>
                            </TableRow>
                          )
                        })
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Project Health Summary
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Active Projects"
                      secondary={`${projects.filter(p => p.status === 'active').length} projects`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <WarningIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Paused Projects"
                      secondary={`${projects.filter(p => p.status === 'paused').length} projects`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Total Targets"
                      secondary={`${targets.length} targets`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <TimelineIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Total Scans"
                      secondary={`${scans.length} scans`}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        {/* Templates */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Web Application Testing
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Comprehensive security testing for web applications
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Targets:</strong> Web applications, APIs, SPAs
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Scans:</strong> Recon, Access Control, Authentication
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>AI:</strong> Enabled for pattern detection
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setProjectForm({
                      name: 'Web App Security Project',
                      description: 'Comprehensive web application security testing',
                      targets: [],
                      configuration: { template: 'web_app' },
                    })
                    setNewProjectDialog(true)
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
                  API Security Assessment
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Focused testing for REST and GraphQL APIs
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Targets:</strong> REST APIs, GraphQL endpoints
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Scans:</strong> Endpoint discovery, Parameter testing
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>AI:</strong> API pattern analysis
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setProjectForm({
                      name: 'API Security Project',
                      description: 'API-focused security assessment',
                      targets: [],
                      configuration: { template: 'api' },
                    })
                    setNewProjectDialog(true)
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
                  Mobile App Backend
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Security testing for mobile application backends
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    <strong>Targets:</strong> Mobile APIs, Authentication services
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Scans:</strong> Auth bypass, Session management
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>AI:</strong> Behavioral analysis
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setProjectForm({
                      name: 'Mobile Backend Security',
                      description: 'Mobile application backend security testing',
                      targets: [],
                      configuration: { template: 'mobile' },
                    })
                    setNewProjectDialog(true)
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
                  Custom Project
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create a custom project with your own configuration
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setNewProjectDialog(true)}
                >
                  Create Custom
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        {/* Settings */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Project Management Settings
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Auto-scan projects on creation"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable project templates"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={<Switch />}
                  label="Require project approval"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Auto-archive inactive projects"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>

      {/* New Project Dialog */}
      <Dialog
        open={newProjectDialog}
        onClose={() => setNewProjectDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Project Name"
                placeholder="Enter project name"
                value={projectForm.name}
                onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
                helperText="Choose a descriptive name for your project"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                placeholder="Enter project description"
                multiline
                rows={3}
                value={projectForm.description}
                onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
                helperText="Describe the purpose and scope of this project"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Targets</InputLabel>
                <Select
                  multiple
                  value={projectForm.targets}
                  label="Targets"
                  onChange={(e) => setProjectForm({ ...projectForm, targets: e.target.value as number[] })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const target = targets.find(t => t.id === value)
                        return (
                          <Chip key={value} label={target?.name || target?.base_url || `ID: ${value}`} size="small" />
                        )
                      })}
                    </Box>
                  )}
                >
                  {targets.map((target) => (
                    <MenuItem key={target.id} value={target.id}>
                      {target.name || target.base_url}
                    </MenuItem>
                  ))}
                </Select>
                <Typography variant="caption" color="text.secondary">
                  Select the targets to include in this project
                </Typography>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewProjectDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateProject}
            variant="contained"
            disabled={createProjectMutation.isPending}
          >
            {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Project Dialog */}
      <Dialog
        open={editProjectDialog}
        onClose={() => setEditProjectDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Project: {selectedProject?.name}</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Project Name"
                value={projectForm.name}
                onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={projectForm.description}
                onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Targets</InputLabel>
                <Select
                  multiple
                  value={projectForm.targets}
                  label="Targets"
                  onChange={(e) => setProjectForm({ ...projectForm, targets: e.target.value as number[] })}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const target = targets.find(t => t.id === value)
                        return (
                          <Chip key={value} label={target?.name || target?.base_url || `ID: ${value}`} size="small" />
                        )
                      })}
                    </Box>
                  )}
                >
                  {targets.map((target) => (
                    <MenuItem key={target.id} value={target.id}>
                      {target.name || target.base_url}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditProjectDialog(false)}>Cancel</Button>
          <Button
            onClick={handleUpdateProject}
            variant="contained"
            disabled={updateProjectMutation.isPending}
          >
            {updateProjectMutation.isPending ? 'Updating...' : 'Update Project'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Projects
