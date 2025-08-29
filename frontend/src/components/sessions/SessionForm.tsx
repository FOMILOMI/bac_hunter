import React from 'react'
import {
  Box,
  TextField,
  Button,
  Grid,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material'
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material'

interface SessionFormProps {
  session?: any
  onSubmit: (data: any) => void
  onCancel: () => void
}

const SessionForm: React.FC<SessionFormProps> = ({ session, onSubmit, onCancel }) => {
  const [formData, setFormData] = React.useState({
    name: session?.name || '',
    type: session?.type || 'scan',
    description: session?.description || '',
    auto_start: session?.auto_start || false,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 600 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>
        {session ? 'Edit Session' : 'Create New Session'}
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Session Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </Grid>
        
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Session Type</InputLabel>
            <Select
              value={formData.type}
              label="Session Type"
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            >
              <MenuItem value="scan">Security Scan</MenuItem>
              <MenuItem value="test">Penetration Test</MenuItem>
              <MenuItem value="audit">Security Audit</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </Grid>
        
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.auto_start}
                onChange={(e) => setFormData({ ...formData, auto_start: e.target.checked })}
              />
            }
            label="Auto-start session"
          />
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button onClick={onCancel} startIcon={<CancelIcon />}>
          Cancel
        </Button>
        <Button type="submit" variant="contained" startIcon={<SaveIcon />}>
          {session ? 'Update' : 'Create'} Session
        </Button>
      </Box>
    </Box>
  )
}

export default SessionForm