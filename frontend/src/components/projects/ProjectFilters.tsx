import React, { useState, useMemo } from 'react'
import {
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  SelectChangeEvent,
  Button,
  IconButton,
  Tooltip,
  Popover,
  Typography,
  Divider,
  FormControlLabel,
  Checkbox,
  Slider,
  TextField,
  useTheme,
  alpha,
} from '@mui/material'
import {
  FilterList as FilterIcon,
  Clear as ClearIcon,
  Tune as TuneIcon,
  DateRange as DateIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material'

import { Project } from '../../types'

interface ProjectFiltersProps {
  statusFilter: string[]
  setStatusFilter: (statuses: string[]) => void
  tagFilter: string[]
  setTagFilter: (tags: string[]) => void
  projects: Project[]
}

const ProjectFilters: React.FC<ProjectFiltersProps> = ({
  statusFilter,
  setStatusFilter,
  tagFilter,
  setTagFilter,
  projects,
}) => {
  const theme = useTheme()
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const [advancedFilters, setAdvancedFilters] = useState({
    dateRange: [null, null] as [Date | null, Date | null],
    scanType: [] as string[],
    hasFindings: null as boolean | null,
    minFindings: 0,
    maxFindings: 100,
  })

  // Extract unique values for filters
  const availableStatuses = useMemo(() => {
    const statuses = [...new Set(projects.map(p => p.status))]
    return statuses.sort()
  }, [projects])

  const availableTags = useMemo(() => {
    const allTags = projects.flatMap(p => p.tags || [])
    const uniqueTags = [...new Set(allTags)]
    return uniqueTags.sort()
  }, [projects])

  const availableScanTypes = useMemo(() => {
    const scanTypes = [...new Set(projects.map(p => p.scan_config?.scan_type).filter(Boolean))]
    return scanTypes.sort()
  }, [projects])

  const handleStatusChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value
    setStatusFilter(typeof value === 'string' ? value.split(',') : value)
  }

  const handleTagChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value
    setTagFilter(typeof value === 'string' ? value.split(',') : value)
  }

  const handleAdvancedFilterChange = (key: string, value: any) => {
    setAdvancedFilters(prev => ({ ...prev, [key]: value }))
  }

  const clearAllFilters = () => {
    setStatusFilter([])
    setTagFilter([])
    setAdvancedFilters({
      dateRange: [null, null],
      scanType: [],
      hasFindings: null,
      minFindings: 0,
      maxFindings: 100,
    })
  }

  const hasActiveFilters = statusFilter.length > 0 || tagFilter.length > 0 || 
    advancedFilters.dateRange.some(d => d !== null) ||
    advancedFilters.scanType.length > 0 ||
    advancedFilters.hasFindings !== null ||
    advancedFilters.minFindings > 0 ||
    advancedFilters.maxFindings < 100

  const openAdvancedFilters = Boolean(anchorEl)

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
      {/* Status Filter */}
      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel>Status</InputLabel>
        <Select
          multiple
          value={statusFilter}
          onChange={handleStatusChange}
          input={<OutlinedInput label="Status" />}
          renderValue={(selected) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selected.map((value) => (
                <Chip
                  key={value}
                  label={value}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.75rem', height: 20 }}
                />
              ))}
            </Box>
          )}
        >
          {availableStatuses.map((status) => (
            <MenuItem key={status} value={status}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={statusFilter.indexOf(status) > -1}
                    size="small"
                  />
                }
                label={status}
                sx={{ margin: 0 }}
              />
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Tag Filter */}
      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel>Tags</InputLabel>
        <Select
          multiple
          value={tagFilter}
          onChange={handleTagChange}
          input={<OutlinedInput label="Tags" />}
          renderValue={(selected) => (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {selected.map((value) => (
                <Chip
                  key={value}
                  label={value}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.75rem', height: 20 }}
                />
              ))}
            </Box>
          )}
        >
          {availableTags.map((tag) => (
            <MenuItem key={tag} value={tag}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={tagFilter.indexOf(tag) > -1}
                    size="small"
                  />
                }
                label={tag}
                sx={{ margin: 0 }}
              />
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Advanced Filters Button */}
      <Tooltip title="Advanced Filters">
        <IconButton
          onClick={(event) => setAnchorEl(event.currentTarget)}
          sx={{
            backgroundColor: hasActiveFilters 
              ? alpha(theme.palette.primary.main, 0.1) 
              : 'transparent',
            color: hasActiveFilters ? 'primary.main' : 'inherit',
          }}
        >
          <TuneIcon />
        </IconButton>
      </Tooltip>

      {/* Clear Filters Button */}
      {hasActiveFilters && (
        <Tooltip title="Clear All Filters">
          <IconButton
            onClick={clearAllFilters}
            size="small"
            color="error"
          >
            <ClearIcon />
          </IconButton>
        </Tooltip>
      )}

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, ml: 'auto' }}>
          {statusFilter.map(status => (
            <Chip
              key={`status-${status}`}
              label={`Status: ${status}`}
              size="small"
              onDelete={() => setStatusFilter(statusFilter.filter(s => s !== status))}
              color="primary"
              variant="outlined"
            />
          ))}
          {tagFilter.map(tag => (
            <Chip
              key={`tag-${tag}`}
              label={`Tag: ${tag}`}
              size="small"
              onDelete={() => setTagFilter(tagFilter.filter(t => t !== tag))}
              color="secondary"
              variant="outlined"
            />
          ))}
        </Box>
      )}

      {/* Advanced Filters Popover */}
      <Popover
        open={openAdvancedFilters}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: {
            width: 400,
            maxHeight: 600,
            p: 3,
          },
        }}
      >
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <TuneIcon />
          Advanced Filters
        </Typography>

        <Divider sx={{ mb: 2 }} />

        {/* Scan Type Filter */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Scan Type
          </Typography>
          <FormControl fullWidth size="small">
            <Select
              multiple
              value={advancedFilters.scanType}
              onChange={(e) => handleAdvancedFilterChange('scanType', e.target.value)}
              input={<OutlinedInput />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {availableScanTypes.map((scanType) => (
                <MenuItem key={scanType} value={scanType}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={advancedFilters.scanType.indexOf(scanType) > -1}
                        size="small"
                      />
                    }
                    label={scanType}
                    sx={{ margin: 0 }}
                  />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Findings Range Filter */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Findings Count Range
          </Typography>
          <Box sx={{ px: 2 }}>
            <Slider
              value={[advancedFilters.minFindings, advancedFilters.maxFindings]}
              onChange={(_, value) => {
                const [min, max] = value as number[]
                handleAdvancedFilterChange('minFindings', min)
                handleAdvancedFilterChange('maxFindings', max)
              }}
              valueLabelDisplay="auto"
              min={0}
              max={100}
              step={1}
            />
          </Box>
          <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
            <TextField
              label="Min"
              type="number"
              size="small"
              value={advancedFilters.minFindings}
              onChange={(e) => handleAdvancedFilterChange('minFindings', parseInt(e.target.value) || 0)}
              inputProps={{ min: 0, max: advancedFilters.maxFindings }}
              sx={{ width: '50%' }}
            />
            <TextField
              label="Max"
              type="number"
              size="small"
              value={advancedFilters.maxFindings}
              onChange={(e) => handleAdvancedFilterChange('maxFindings', parseInt(e.target.value) || 100)}
              inputProps={{ min: advancedFilters.minFindings, max: 1000 }}
              sx={{ width: '50%' }}
            />
          </Box>
        </Box>

        {/* Has Findings Filter */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Findings Status
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={advancedFilters.hasFindings === true}
                  onChange={(e) => handleAdvancedFilterChange('hasFindings', e.target.checked ? true : null)}
                  size="small"
                />
              }
              label="Has Findings"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={advancedFilters.hasFindings === false}
                  onChange={(e) => handleAdvancedFilterChange('hasFindings', e.target.checked ? false : null)}
                  size="small"
                />
              }
              label="No Findings"
            />
          </Box>
        </Box>

        {/* Date Range Filter */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <DateIcon fontSize="small" />
            Date Range
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="From"
              type="date"
              size="small"
              value={advancedFilters.dateRange[0]?.toISOString().split('T')[0] || ''}
              onChange={(e) => {
                const date = e.target.value ? new Date(e.target.value) : null
                handleAdvancedFilterChange('dateRange', [date, advancedFilters.dateRange[1]])
              }}
              InputLabelProps={{ shrink: true }}
              sx={{ flexGrow: 1 }}
            />
            <TextField
              label="To"
              type="date"
              size="small"
              value={advancedFilters.dateRange[1]?.toISOString().split('T')[0] || ''}
              onChange={(e) => {
                const date = e.target.value ? new Date(e.target.value) : null
                handleAdvancedFilterChange('dateRange', [advancedFilters.dateRange[0], date])
              }}
              InputLabelProps={{ shrink: true }}
              sx={{ flexGrow: 1 }}
            />
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Filter Actions */}
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
          <Button
            onClick={() => setAnchorEl(null)}
            variant="outlined"
            size="small"
          >
            Close
          </Button>
          <Button
            onClick={clearAllFilters}
            variant="outlined"
            size="small"
            color="error"
          >
            Clear All
          </Button>
          <Button
            onClick={() => setAnchorEl(null)}
            variant="contained"
            size="small"
          >
            Apply Filters
          </Button>
        </Box>
      </Popover>
    </Box>
  )
}

export default ProjectFilters
