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
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Settings as SettingsIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  FolderOpen as ProjectIcon,
  BugReport as FindingIcon,
  PlayArrow as ScanIcon,
  Assessment as ReportIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'

import { projectsAPI } from '../services/api'
import { Project, ScanConfig } from '../types'
import ProjectCard from '../components/projects/ProjectCard'
import ProjectForm from '../components/projects/ProjectForm'
import ProjectFilters from '../components/projects/ProjectFilters'
import ProjectStats from '../components/projects/ProjectStats'
import ImportProjectDialog from '../components/projects/ImportProjectDialog'
import ExportProjectDialog from '../components/projects/ExportProjectDialog'

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
      id={`projects-tabpanel-${index}`}
      aria-labelledby={`projects-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const Projects: React.FC = () => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  const [tabValue, setTabValue] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  // Fetch projects
  const {
    data: projectsData,
    isLoading,
    error,
    refetch,
  } = useQuery(['projects'], projectsAPI.getAll, {
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const projects = projectsData?.projects || []

  // Create project mutation
  const createProjectMutation = useMutation(projectsAPI.create, {
    onSuccess: () => {
      queryClient.invalidateQueries(['projects'])
      toast.success('Project created successfully!')
      setShowCreateDialog(false)
    },
    onError: (error: any) => {
      toast.error(`Failed to create project: ${error.message}`)
    },
  })

  // Update project mutation
  const updateProjectMutation = useMutation(
    (data: { id: string; updates: Partial<Project> }) =>
      projectsAPI.update(data.id, data.updates),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['projects'])
        toast.success('Project updated successfully!')
        setEditingProject(null)
      },
      onError: (error: any) => {
        toast.error(`Failed to update project: ${error.message}`)
      },
    }
  )

  // Delete project mutation
  const deleteProjectMutation = useMutation(projectsAPI.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['projects'])
      toast.success('Project deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(`Failed to delete project: ${error.message}`)
    },
  })

  // Filter projects based on search and filters
  const filteredProjects = projects.filter((project) => {
    const matchesSearch = project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         project.target_url.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = statusFilter.length === 0 || statusFilter.includes(project.status)
    
    const matchesTags = tagFilter.length === 0 || 
                       project.tags?.some(tag => tagFilter.includes(tag))
    
    return matchesSearch && matchesStatus && matchesTags
  })

  // Group projects by status
  const projectsByStatus = {
    active: filteredProjects.filter(p => p.status === 'completed' || p.status === 'scanning'),
    scanning: filteredProjects.filter(p => p.status === 'scanning'),
    completed: filteredProjects.filter(p => p.status === 'completed'),
    failed: filteredProjects.filter(p => p.status === 'failed'),
    paused: filteredProjects.filter(p => p.status === 'paused'),
  }

  const handleCreateProject = (projectData: Partial<Project>) => {
    createProjectMutation.mutate(projectData)
  }

  const handleUpdateProject = (id: string, updates: Partial<Project>) => {
    updateProjectMutation.mutate({ id, updates })
  }

  const handleDeleteProject = (id: string) => {
    if (window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      deleteProjectMutation.mutate(id)
    }
  }

  const handleStartScan = (projectId: string) => {
    // This would integrate with the scan management system
    toast.success('Starting scan...')
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load projects: {(error as any).message}
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
            Project Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your security testing projects and configurations
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            onClick={() => setShowImportDialog(true)}
          >
            Import
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
            New Project
          </Button>
        </Box>
      </Box>

      {/* Project Statistics */}
      <ProjectStats projects={projects} />

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search projects..."
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
              <ProjectFilters
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
                tagFilter={tagFilter}
                setTagFilter={setTagFilter}
                projects={projects}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="project tabs">
          <Tab 
            label={`All Projects (${filteredProjects.length})`} 
            icon={<ProjectIcon />}
            iconPosition="start"
          />
          <Tab 
            label={`Active (${projectsByStatus.active.length})`} 
            icon={<ScanIcon />}
            iconPosition="start"
          />
          <Tab 
            label={`Scanning (${projectsByStatus.scanning.length})`} 
            icon={<PlayIcon />}
            iconPosition="start"
          />
          <Tab 
            label={`Completed (${projectsByStatus.completed.length})`} 
            icon={<CheckCircleIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <ProjectGrid
          projects={filteredProjects}
          isLoading={isLoading}
          onEdit={setEditingProject}
          onDelete={handleDeleteProject}
          onStartScan={handleStartScan}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <ProjectGrid
          projects={projectsByStatus.active}
          isLoading={isLoading}
          onEdit={setEditingProject}
          onDelete={handleDeleteProject}
          onStartScan={handleStartScan}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <ProjectGrid
          projects={projectsByStatus.scanning}
          isLoading={isLoading}
          onEdit={setEditingProject}
          onDelete={handleDeleteProject}
          onStartScan={handleStartScan}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <ProjectGrid
          projects={projectsByStatus.completed}
          isLoading={isLoading}
          onEdit={setEditingProject}
          onDelete={handleDeleteProject}
          onStartScan={handleStartScan}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </TabPanel>

      {/* Create Project Dialog */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <ProjectForm
            onSubmit={handleCreateProject}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Edit Project Dialog */}
      <Dialog
        open={!!editingProject}
        onClose={() => setEditingProject(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Project</DialogTitle>
        <DialogContent>
          {editingProject && (
            <ProjectForm
              project={editingProject}
              onSubmit={(updates) => handleUpdateProject(editingProject.id, updates)}
              onCancel={() => setEditingProject(null)}
              isEditing
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Import Dialog */}
      <ImportProjectDialog
        open={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        onImport={(data) => {
          // Handle import logic
          setShowImportDialog(false)
        }}
      />

      {/* Export Dialog */}
      <ExportProjectDialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        projects={projects}
      />
    </Box>
  )
}

export default Projects
