import React, { useState } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Add as AddIcon,
  PlayArrow as ScanIcon,
  Assessment as ReportIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const QuickActions: React.FC = () => {
  const navigate = useNavigate()
  const [newProjectOpen, setNewProjectOpen] = useState(false)
  const [projectData, setProjectData] = useState({
    name: '',
    target_url: '',
    description: '',
    scan_type: 'comprehensive',
  })

  const handleCreateProject = () => {
    // Here you would call the API to create a project
    toast.success('Project created successfully!')
    setNewProjectOpen(false)
    setProjectData({ name: '', target_url: '', description: '', scan_type: 'comprehensive' })
    navigate('/projects')
  }

  const quickActions = [
    {
      title: 'New Project',
      description: 'Start a new security assessment',
      icon: <AddIcon />,
      color: 'primary',
      action: () => setNewProjectOpen(true),
    },
    {
      title: 'Quick Scan',
      description: 'Run a quick vulnerability scan',
      icon: <ScanIcon />,
      color: 'success',
      action: () => navigate('/scans?quick=true'),
    },
    {
      title: 'Generate Report',
      description: 'Create a security report',
      icon: <ReportIcon />,
      color: 'info',
      action: () => navigate('/reports'),
    },
    {
      title: 'Import Session',
      description: 'Upload HAR or session file',
      icon: <UploadIcon />,
      color: 'secondary',
      action: () => navigate('/sessions?import=true'),
    },
    {
      title: 'Export Data',
      description: 'Download findings and reports',
      icon: <DownloadIcon />,
      color: 'warning',
      action: () => navigate('/reports?export=true'),
    },
    {
      title: 'Settings',
      description: 'Configure scan preferences',
      icon: <SettingsIcon />,
      color: 'default',
      action: () => navigate('/settings'),
    },
  ]

  return (
    <>
      <Card sx={{ height: '100%' }}>
        <CardHeader
          title="Quick Actions"
          titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
          subheader="Common tasks and shortcuts"
        />
        <CardContent sx={{ pt: 0 }}>
          <List disablePadding>
            {quickActions.map((action, index) => (
              <ListItem
                key={index}
                button
                onClick={action.action}
                sx={{
                  borderRadius: 2,
                  mb: 1,
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: action.color === 'default' ? 'text.secondary' : `${action.color}.main`,
                    minWidth: 40,
                  }}
                >
                  {action.icon}
                </ListItemIcon>
                <ListItemText
                  primary={action.title}
                  secondary={action.description}
                  primaryTypographyProps={{ fontWeight: 500 }}
                  secondaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
            ))}
          </List>

          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              fullWidth
              startIcon={<AddIcon />}
              onClick={() => setNewProjectOpen(true)}
              sx={{ mb: 1 }}
            >
              New Project
            </Button>
            <Button
              variant="outlined"
              fullWidth
              startIcon={<ScanIcon />}
              onClick={() => navigate('/scans')}
            >
              View All Scans
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* New Project Dialog */}
      <Dialog
        open={newProjectOpen}
        onClose={() => setNewProjectOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="Project Name"
              value={projectData.name}
              onChange={(e) => setProjectData({ ...projectData, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Target URL"
              value={projectData.target_url}
              onChange={(e) => setProjectData({ ...projectData, target_url: e.target.value })}
              fullWidth
              required
              placeholder="https://example.com"
              type="url"
            />
            <TextField
              label="Description"
              value={projectData.description}
              onChange={(e) => setProjectData({ ...projectData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth>
              <InputLabel>Scan Type</InputLabel>
              <Select
                value={projectData.scan_type}
                onChange={(e) => setProjectData({ ...projectData, scan_type: e.target.value })}
                label="Scan Type"
              >
                <MenuItem value="quick">Quick Scan</MenuItem>
                <MenuItem value="comprehensive">Comprehensive</MenuItem>
                <MenuItem value="stealth">Stealth Mode</MenuItem>
                <MenuItem value="aggressive">Aggressive</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewProjectOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateProject}
            variant="contained"
            disabled={!projectData.name || !projectData.target_url}
          >
            Create Project
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default QuickActions
