import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  useTheme,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material'
import {
  Psychology,
  TrendingUp,
  Security,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Visibility,
  AutoAwesome
} from '@mui/icons-material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { toast } from 'react-hot-toast'

import { api } from '../../services/api'

interface AIInsightsCardProps {
  className?: string
}

const AIInsightsCard: React.FC<AIInsightsCardProps> = ({ className }) => {
  const theme = useTheme()
  const queryClient = useQueryClient()
  
  // State
  const [showAllInsights, setShowAllInsights] = useState(false)
  
  // Mutations
  const refreshInsightsMutation = useMutation({
    mutationFn: () => api.triggerAIAnalysis({
      target_url: 'dashboard',
      analysis_type: 'comprehensive'
    }),
    onSuccess: () => {
      toast.success('AI insights refreshed')
      queryClient.invalidateQueries({ queryKey: ['ai-insights'] })
    },
    onError: (error) => {
      toast.error('Failed to refresh AI insights')
      console.error('AI insights refresh error:', error)
    }
  })
  
  // Mock AI insights data (replace with real API data)
  const aiInsights = [
    {
      id: 1,
      type: 'anomaly',
      severity: 'high',
      title: 'Unusual Authentication Patterns',
      description: 'Detected multiple failed login attempts from unusual locations',
      confidence: 0.89,
      timestamp: '2 hours ago',
      category: 'authentication'
    },
    {
      id: 2,
      type: 'vulnerability',
      severity: 'critical',
      title: 'Potential IDOR Vulnerability',
      description: 'High probability of broken access control in user profile endpoints',
      confidence: 0.92,
      timestamp: '4 hours ago',
      category: 'access_control'
    },
    {
      id: 3,
      type: 'recommendation',
      severity: 'medium',
      title: 'Enable Advanced Evasion',
      description: 'Consider enabling stealth mode for sensitive targets',
      confidence: 0.78,
      timestamp: '6 hours ago',
      category: 'strategy'
    },
    {
      id: 4,
      type: 'trend',
      severity: 'low',
      title: 'Performance Optimization',
      description: 'Scan completion times have improved by 15% this week',
      confidence: 0.85,
      timestamp: '1 day ago',
      category: 'performance'
    }
  ]
  
  // Filter insights based on showAllInsights state
  const displayedInsights = showAllInsights ? aiInsights : aiInsights.slice(0, 2)
  
  // Get insight configuration
  const getInsightConfig = (insight: any) => {
    switch (insight.type) {
      case 'anomaly':
        return {
          icon: Warning,
          color: theme.palette.warning.main,
          bgColor: theme.palette.warning.light
        }
      case 'vulnerability':
        return {
          icon: Error,
          color: theme.palette.error.main,
          bgColor: theme.palette.error.light
        }
      case 'recommendation':
        return {
          icon: CheckCircle,
          color: theme.palette.info.main,
          bgColor: theme.palette.info.light
        }
      case 'trend':
        return {
          icon: TrendingUp,
          color: theme.palette.success.main,
          bgColor: theme.palette.success.light
        }
      default:
        return {
          icon: Psychology,
          color: theme.palette.grey[500],
          bgColor: theme.palette.grey[100]
        }
    }
  }
  
  // Get severity configuration
  const getSeverityConfig = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return {
          color: theme.palette.error.main,
          label: 'Critical'
        }
      case 'high':
        return {
          color: theme.palette.error.dark,
          label: 'High'
        }
      case 'medium':
        return {
          color: theme.palette.warning.main,
          label: 'Medium'
        }
      case 'low':
        return {
          color: theme.palette.success.main,
          label: 'Low'
        }
      default:
        return {
          color: theme.palette.grey[500],
          label: severity
        }
    }
  }
  
  // Handle refresh insights
  const handleRefreshInsights = () => {
    refreshInsightsMutation.mutate()
  }
  
  // Handle view all insights
  const handleViewAll = () => {
    window.location.href = '/ai-insights'
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <Card className={className} sx={{ height: '100%' }}>
        <CardContent>
          {/* Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Psychology sx={{ color: theme.palette.secondary.main, fontSize: 28 }} />
              <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                AI Insights
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Refresh Insights" arrow>
                <IconButton
                  size="small"
                  onClick={handleRefreshInsights}
                  disabled={refreshInsightsMutation.isPending}
                  sx={{
                    color: theme.palette.primary.main,
                    '&:hover': {
                      backgroundColor: `${theme.palette.primary.main}10`
                    }
                  }}
                >
                  <Refresh />
                </IconButton>
              </Tooltip>
              
              <Chip
                icon={<AutoAwesome />}
                label="AI Powered"
                size="small"
                sx={{
                  backgroundColor: theme.palette.secondary.main,
                  color: 'white',
                  fontWeight: 'bold'
                }}
              />
            </Box>
          </Box>
          
          {/* AI Status Alert */}
          <Alert 
            severity="info" 
            icon={<Psychology />}
            sx={{ mb: 3 }}
          >
            <Typography variant="body2">
              AI models are actively analyzing security patterns and providing real-time insights
            </Typography>
          </Alert>
          
          {/* Insights List */}
          <List sx={{ mb: 2 }}>
            {displayedInsights.map((insight, index) => {
              const insightConfig = getInsightConfig(insight)
              const severityConfig = getSeverityConfig(insight.severity)
              const InsightIcon = insightConfig.icon
              
              return (
                <motion.div
                  key={insight.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <ListItem
                    sx={{
                      px: 0,
                      py: 1,
                      '&:hover': {
                        backgroundColor: theme.palette.action.hover,
                        borderRadius: 1
                      }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 32,
                          height: 32,
                          borderRadius: '50%',
                          backgroundColor: insightConfig.bgColor,
                          color: insightConfig.color
                        }}
                      >
                        <InsightIcon sx={{ fontSize: 18 }} />
                      </Box>
                    </ListItemIcon>
                    
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {insight.title}
                          </Typography>
                          
                          <Chip
                            label={severityConfig.label}
                            size="small"
                            sx={{
                              backgroundColor: severityConfig.color,
                              color: 'white',
                              fontSize: '0.7rem',
                              height: 20
                            }}
                          />
                          
                          <Typography variant="caption" color="text.secondary">
                            {insight.confidence * 100}% confidence
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                            {insight.description}
                          </Typography>
                          
                          <Typography variant="caption" color="text.secondary">
                            {insight.timestamp} • {insight.category.replace('_', ' ')}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  
                  {index < displayedInsights.length - 1 && (
                    <Divider sx={{ my: 1 }} />
                  )}
                </motion.div>
              )
            })}
          </List>
          
          {/* View All Button */}
          {!showAllInsights && aiInsights.length > 2 && (
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setShowAllInsights(true)}
                startIcon={<Visibility />}
              >
                View All Insights
              </Button>
            </Box>
          )}
          
          {/* AI Model Status */}
          <Box sx={{ 
            p: 2, 
            backgroundColor: theme.palette.grey[50], 
            borderRadius: 1,
            border: `1px solid ${theme.palette.divider}`
          }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
              AI Model Status
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <CheckCircle sx={{ fontSize: 16, color: theme.palette.success.main }} />
              <Typography variant="caption" color="text.secondary">
                Anomaly Detection: Active (89% accuracy)
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <CheckCircle sx={{ fontSize: 16, color: theme.palette.success.main }} />
              <Typography variant="caption" color="text.secondary">
                Vulnerability Prediction: Active (92% accuracy)
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckCircle sx={{ fontSize: 16, color: theme.palette.success.main }} />
              <Typography variant="caption" color="text.secondary">
                Semantic Analysis: Active (87% accuracy)
              </Typography>
            </Box>
          </Box>
          
          {/* Action Button */}
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Button
              variant="contained"
              fullWidth
              onClick={handleViewAll}
              startIcon={<Psychology />}
              sx={{
                background: `linear-gradient(135deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`,
                '&:hover': {
                  background: `linear-gradient(135deg, ${theme.palette.secondary.dark}, ${theme.palette.secondary.main})`
                }
              }}
            >
              View AI Dashboard
            </Button>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default AIInsightsCard