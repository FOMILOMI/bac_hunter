import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
  useTheme,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  PlayArrow,
  Add,
  Security,
  BugReport,
  Target,
  Psychology,
  Speed,
  Settings,
  History,
  Download,
  Upload
} from '@mui/icons-material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { motion } from 'framer-motion'

import { api, ScanRequest } from '../../services/api'

interface QuickActionsPanelProps {
  className?: string
}

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({ className }) => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  
  // State
  const [quickScanOpen, setQuickScanOpen] = useState(false)
  const [targetUrl, setTargetUrl] = useState('')
  const [scanMode, setScanMode] = useState('standard')
  const [selectedPhases, setSelectedPhases] = useState<string[]>(['recon', 'access'])
  const [enableAI, setEnableAI] = useState(true)
  
  // Mutations
  const quickScanMutation = useMutation({
    mutationFn: (scanRequest: ScanRequest) => api.createScan(scanRequest),
    onSuccess: (data) => {
      toast.success(`Quick scan started for ${data.target}`)
      setQuickScanOpen(false)
      setTargetUrl('')
      
      // Refresh dashboard data
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (error) => {
      toast.error('Failed to start quick scan')
      console.error('Quick scan error:', error)
    }
  })
  
  // Handle quick scan
  const handleQuickScan = () => {
    if (!targetUrl.trim()) {
      toast.error('Please enter a target URL')
      return
    }
    
    const scanRequest: ScanRequest = {
      target: targetUrl.trim(),
      mode: scanMode,
      phases: selectedPhases,
      enable_ai: enableAI,
      max_rps: 2.0,
      timeout_minutes: 30,
      obey_robots: true
    }
    
    quickScanMutation.mutate(scanRequest)
  }
  
  // Phase options
  const phaseOptions = [
    { value: 'recon', label: 'Reconnaissance', description: 'Discover endpoints and structure' },
    { value: 'access', label: 'Access Control', description: 'Test authentication and authorization' },
    { value: 'audit', label: 'Security Audit', description: 'Comprehensive security assessment' },
    { value: 'exploit', label: 'Exploitation', description: 'Attempt to exploit vulnerabilities' }
  ]
  
  // Mode options
  const modeOptions = [
    { value: 'stealth', label: 'Stealth', description: 'Minimal detection risk' },
    { value: 'standard', label: 'Standard', description: 'Balanced speed and coverage' },
    { value: 'aggressive', label: 'Aggressive', description: 'Fast but higher detection risk' },
    { value: 'maximum', label: 'Maximum', description: 'Comprehensive but slow' }
  ]
  
  // Quick action buttons
  const quickActions = [
    {
      icon: <Target />,
      label: 'Add Target',
      description: 'Add new target for scanning',
      action: () => setQuickScanOpen(true),
      color: theme.palette.primary.main
    },
    {
      icon: <Security />,
      label: 'Security Check',
      description: 'Run security assessment',
      action: () => setQuickScanOpen(true),
      color: theme.palette.warning.main
    },
    {
      icon: <BugReport />,
      label: 'Vulnerability Scan',
      description: 'Find security vulnerabilities',
      action: () => setQuickScanOpen(true),
      color: theme.palette.error.main
    },
    {
      icon: <Psychology />,
      label: 'AI Analysis',
      description: 'Get AI-powered insights',
      action: () => window.location.href = '/ai-insights',
      color: theme.palette.secondary.main
    }
  ]
  
  return (
    <>
      <Card className={className} sx={{ height: '100%' }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
            Quick Actions
          </Typography>
          
          {/* Quick Action Buttons */}
          <Box sx={{ mb: 3 }}>
            {quickActions.map((action, index) => (
              <motion.div
                key={action.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={action.icon}
                  onClick={action.action}
                  sx={{
                    mb: 1,
                    justifyContent: 'flex-start',
                    textAlign: 'left',
                    borderColor: action.color,
                    color: action.color,
                    '&:hover': {
                      borderColor: action.color,
                      backgroundColor: `${action.color}10`
                    }
                  }}
                >
                  <Box sx={{ textAlign: 'left' }}>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {action.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {action.description}
                    </Typography>
                  </Box>
                </Button>
              </motion.div>
            ))}
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          {/* Recent Actions */}
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
            Recent Actions
          </Typography>
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <History sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                Last scan: 2 hours ago
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Download sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                Report generated: 1 day ago
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Upload sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                Target added: 3 days ago
              </Typography>
            </Box>
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          {/* Quick Scan Button */}
          <Button
            fullWidth
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={() => setQuickScanOpen(true)}
            sx={{
              background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              '&:hover': {
                background: `linear-gradient(135deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`
              }
            }}
          >
            Quick Security Scan
          </Button>
        </CardContent>
      </Card>
      
      {/* Quick Scan Dialog */}
      <Dialog
        open={quickScanOpen}
        onClose={() => setQuickScanOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Security />
            Quick Security Scan
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Configure and start a security scan for your target
          </Alert>
          
          <TextField
            fullWidth
            label="Target URL"
            placeholder="https://example.com"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            sx={{ mb: 2 }}
            helperText="Enter the target URL or domain to scan"
          />
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Scan Mode</InputLabel>
            <Select
              value={scanMode}
              onChange={(e) => setScanMode(e.target.value)}
              label="Scan Mode"
            >
              {modeOptions.map((mode) => (
                <MenuItem key={mode.value} value={mode.value}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {mode.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {mode.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Scan Phases</InputLabel>
            <Select
              multiple
              value={selectedPhases}
              onChange={(e) => setSelectedPhases(typeof e.target.value === 'string' ? [e.target.value] : e.target.value)}
              label="Scan Phases"
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={phaseOptions.find(p => p.value === value)?.label || value}
                      size="small"
                    />
                  ))}
                </Box>
              )}
            >
              {phaseOptions.map((phase) => (
                <MenuItem key={phase.value} value={phase.value}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                      {phase.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {phase.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Psychology sx={{ color: 'text.secondary' }} />
            <Typography variant="body2">
              Enable AI-powered analysis for enhanced detection
            </Typography>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setQuickScanOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleQuickScan}
            variant="contained"
            disabled={quickScanMutation.isPending || !targetUrl.trim()}
            startIcon={quickScanMutation.isPending ? <Speed /> : <PlayArrow />}
          >
            {quickScanMutation.isPending ? 'Starting Scan...' : 'Start Scan'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default QuickActionsPanel