import React from 'react'
import {
  Box,
  Grid,
  Skeleton,
  Typography,
  Button,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Chip,
} from '@mui/material'
import {
  ViewModule as GridIcon,
  ViewList as ListIcon,
  TableChart as TableIcon,
  Add as AddIcon,
  Visibility as ViewIcon,
  CheckCircle as ResolvedIcon,
  Cancel as FalsePositiveIcon,
} from '@mui/icons-material'
import { motion, AnimatePresence } from 'framer-motion'

import { Finding } from '../../types'
import FindingCard from './FindingCard'

interface FindingGridProps {
  findings: Finding[]
  isLoading: boolean
  onUpdateStatus: (id: string, status: string) => void
  onDelete: (id: string) => void
  onViewDetails: (finding: Finding) => void
  viewMode: 'grid' | 'list' | 'table'
  setViewMode: (mode: 'grid' | 'list' | 'table') => void
  page: number
  rowsPerPage: number
  onPageChange: (event: unknown, newPage: number) => void
  onRowsPerPageChange: (event: React.ChangeEvent<HTMLInputElement>) => void
}

const FindingGrid: React.FC<FindingGridProps> = ({
  findings,
  isLoading,
  onUpdateStatus,
  onDelete,
  onViewDetails,
  viewMode,
  setViewMode,
  page,
  rowsPerPage,
  onPageChange,
  onRowsPerPageChange,
}) => {
  const theme = useTheme()

  // Paginate findings
  const paginatedFindings = findings.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  if (isLoading) {
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h6" color="text.secondary">
            Loading findings...
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title="Grid View">
              <IconButton
                size="small"
                onClick={() => setViewMode('grid')}
                color={viewMode === 'grid' ? 'primary' : 'default'}
              >
                <GridIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="List View">
              <IconButton
                size="small"
                onClick={() => setViewMode('list')}
                color={viewMode === 'list' ? 'primary' : 'default'}
              >
                <ListIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Table View">
              <IconButton
                size="small"
                onClick={() => setViewMode('table')}
                color={viewMode === 'table' ? 'primary' : 'default'}
              >
                <TableIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Grid container spacing={3}>
          {Array.from({ length: 6 }).map((_, index) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
              <Skeleton
                variant="rectangular"
                height={500}
                sx={{ borderRadius: 2 }}
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    )
  }

  if (findings.length === 0) {
    return (
      <Box
        sx={{
          textAlign: 'center',
          py: 8,
          px: 3,
        }}
      >
        <Box
          sx={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 2rem',
            fontSize: '3rem',
            color: theme.palette.primary.main,
          }}
        >
          🔍
        </Box>
        
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
          No findings found
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
          {viewMode === 'grid' 
            ? 'Get started by running your first security scan. The findings will appear here once vulnerabilities are discovered.'
            : 'No findings match your current filters. Try adjusting your search criteria or run a new scan.'
          }
        </Typography>
        
        <Button
          variant="contained"
          size="large"
          startIcon={<AddIcon />}
          sx={{ px: 4, py: 1.5 }}
        >
          Run Security Scan
        </Button>
      </Box>
    )
  }

  return (
    <Box>
      {/* View Mode Toggle */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          {findings.length} finding{findings.length !== 1 ? 's' : ''} found
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Grid View">
            <IconButton
              size="small"
              onClick={() => setViewMode('grid')}
              color={viewMode === 'grid' ? 'primary' : 'default'}
              sx={{
                backgroundColor: viewMode === 'grid' 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent',
              }}
            >
              <GridIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="List View">
            <IconButton
              size="small"
              onClick={() => setViewMode('list')}
              color={viewMode === 'list' ? 'primary' : 'default'}
              sx={{
                backgroundColor: viewMode === 'list' 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent',
              }}
            >
              <ListIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Table View">
            <IconButton
              size="small"
              onClick={() => setViewMode('table')}
              color={viewMode === 'table' ? 'primary' : 'default'}
              sx={{
                backgroundColor: viewMode === 'table' 
                  ? alpha(theme.palette.primary.main, 0.1) 
                  : 'transparent',
              }}
            >
              <TableIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Findings Display */}
      <AnimatePresence mode="wait">
        {viewMode === 'grid' && (
          <Grid container spacing={3}>
            {paginatedFindings.map((finding, index) => (
              <Grid
                item
                xs={12}
                sm={6}
                md={4}
                lg={3}
                key={finding.id}
                component={motion.div}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <FindingCard
                  finding={finding}
                  onUpdateStatus={onUpdateStatus}
                  onDelete={onDelete}
                  onViewDetails={onViewDetails}
                />
              </Grid>
            ))}
          </Grid>
        )}

        {viewMode === 'list' && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {paginatedFindings.map((finding, index) => (
              <motion.div
                key={finding.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <FindingCard
                  finding={finding}
                  onUpdateStatus={onUpdateStatus}
                  onDelete={onDelete}
                  onViewDetails={onViewDetails}
                />
              </motion.div>
            ))}
          </Box>
        )}

        {viewMode === 'table' && (
          <Paper sx={{ width: '100%', overflow: 'hidden' }}>
            <TableContainer>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Title</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>CVSS Score</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedFindings.map((finding) => (
                    <TableRow
                      hover
                      key={finding.id}
                      sx={{ cursor: 'pointer' }}
                      onClick={() => onViewDetails(finding)}
                    >
                      <TableCell>
                        <Box>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {finding.title || `Finding ${finding.id}`}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {finding.description ? 
                              finding.description.length > 50 ? 
                                finding.description.substring(0, 50) + '...' : 
                                finding.description 
                              : 'No description'
                            }
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={finding.severity}
                          size="small"
                          color={finding.severity === 'critical' ? 'error' : 
                                 finding.severity === 'high' ? 'warning' : 
                                 finding.severity === 'medium' ? 'info' : 
                                 finding.severity === 'low' ? 'success' : 'default'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={finding.status?.replace('_', ' ') || 'unknown'}
                          size="small"
                          color={finding.status === 'open' ? 'error' : 
                                 finding.status === 'in_progress' ? 'warning' : 
                                 finding.status === 'resolved' ? 'success' : 
                                 finding.status === 'false_positive' ? 'info' : 'default'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {finding.type?.replace('_', ' ') || 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="warning.main" sx={{ fontWeight: 600 }}>
                          {finding.cvss_score || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {finding.created_at ? new Date(finding.created_at).toLocaleDateString() : 'Unknown'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5 }}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                onViewDetails(finding)
                              }}
                            >
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Mark as Resolved">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                onUpdateStatus(finding.id, 'resolved')
                              }}
                              color="success"
                            >
                              <ResolvedIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Mark as False Positive">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation()
                                onUpdateStatus(finding.id, 'false_positive')
                              }}
                              color="info"
                            >
                              <FalsePositiveIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            {/* Pagination */}
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={findings.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={onPageChange}
              onRowsPerPageChange={onRowsPerPageChange}
            />
          </Paper>
        )}
      </AnimatePresence>

      {/* Pagination for Grid/List views */}
      {(viewMode === 'grid' || viewMode === 'list') && findings.length > rowsPerPage && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <TablePagination
            rowsPerPageOptions={[10, 25, 50, 100]}
            component="div"
            count={findings.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={onPageChange}
            onRowsPerPageChange={onRowsPerPageChange}
          />
        </Box>
      )}
    </Box>
  )
}

export default FindingGrid
