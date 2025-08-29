import React from 'react'
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Button,
  Grid,
  InputAdornment,
  useTheme,
  SelectChangeEvent,
} from '@mui/material'
import {
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material'

interface ReportFiltersProps {
  searchTerm: string
  onSearchChange: (search: string) => void
  statusFilter: string[]
  onStatusFilterChange: (status: string[]) => void
  typeFilter: string[]
  onTypeFilterChange: (types: string[]) => void
  formatFilter: string[]
  onFormatFilterChange: (formats: string[]) => void
  onClearFilters: () => void
}

const ReportFilters: React.FC<ReportFiltersProps> = ({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  typeFilter,
  onTypeFilterChange,
  formatFilter,
  onFormatFilterChange,
  onClearFilters
}) => {
  const theme = useTheme()

  const statusOptions = ['draft', 'generating', 'completed', 'failed', 'scheduled']
  const typeOptions = ['executive', 'technical', 'compliance', 'detailed', 'custom']
  const formatOptions = ['pdf', 'html', 'json', 'csv']

  const handleStatusChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value
    onStatusFilterChange(typeof value === 'string' ? value.split(',') : value)
  }

  const handleTypeChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value
    onTypeFilterChange(typeof value === 'string' ? value.split(',') : value)
  }

  const handleFormatChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value
    onFormatFilterChange(typeof value === 'string' ? value.split(',') : value)
  }

  const hasActiveFilters = searchTerm || statusFilter.length > 0 || typeFilter.length > 0 || formatFilter.length > 0

  return (
    <Box sx={{ mb: 3 }}>
      <Grid container spacing={2} alignItems="center">
        {/* Search */}
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        {/* Status Filter */}
        <Grid item xs={12} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              multiple
              value={statusFilter}
              onChange={handleStatusChange}
              input={<OutlinedInput label="Status" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {statusOptions.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Type Filter */}
        <Grid item xs={12} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Type</InputLabel>
            <Select
              multiple
              value={typeFilter}
              onChange={handleTypeChange}
              input={<OutlinedInput label="Type" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {typeOptions.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Format Filter */}
        <Grid item xs={12} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Format</InputLabel>
            <Select
              multiple
              value={formatFilter}
              onChange={handleFormatChange}
              input={<OutlinedInput label="Format" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((value) => (
                    <Chip key={value} label={value.toUpperCase()} size="small" />
                  ))}
                </Box>
              )}
            >
              {formatOptions.map((format) => (
                <MenuItem key={format} value={format}>
                  {format.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Clear Filters */}
        <Grid item xs={12} md={2}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={onClearFilters}
            disabled={!hasActiveFilters}
          >
            Clear Filters
          </Button>
        </Grid>
      </Grid>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {searchTerm && (
            <Chip
              label={`Search: "${searchTerm}"`}
              onDelete={() => onSearchChange('')}
              size="small"
            />
          )}
          {statusFilter.map((status) => (
            <Chip
              key={`status-${status}`}
              label={`Status: ${status}`}
              onDelete={() => onStatusFilterChange(statusFilter.filter(s => s !== status))}
              size="small"
              color="primary"
              variant="outlined"
            />
          ))}
          {typeFilter.map((type) => (
            <Chip
              key={`type-${type}`}
              label={`Type: ${type}`}
              onDelete={() => onTypeFilterChange(typeFilter.filter(t => t !== type))}
              size="small"
              color="secondary"
              variant="outlined"
            />
          ))}
          {formatFilter.map((format) => (
            <Chip
              key={`format-${format}`}
              label={`Format: ${format.toUpperCase()}`}
              onDelete={() => onFormatFilterChange(formatFilter.filter(f => f !== format))}
              size="small"
              color="info"
              variant="outlined"
            />
          ))}
        </Box>
      )}
    </Box>
  )
}

export default ReportFilters