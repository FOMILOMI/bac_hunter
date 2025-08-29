import React from 'react'
import { Card, CardContent, CardHeader, Typography, Box, useTheme } from '@mui/material'
import { Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

interface SeverityChartProps {
  data: {
    critical: number
    high: number
    medium: number
    low: number
  }
}

const SeverityChart: React.FC<SeverityChartProps> = ({ data }) => {
  const theme = useTheme()

  const total = data.critical + data.high + data.medium + data.low

  const chartData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [
      {
        data: [data.critical, data.high, data.medium, data.low],
        backgroundColor: [
          theme.palette.error.main,
          theme.palette.warning.main,
          theme.palette.info.main,
          theme.palette.success.main,
        ],
        borderColor: [
          theme.palette.error.dark,
          theme.palette.warning.dark,
          theme.palette.info.dark,
          theme.palette.success.dark,
        ],
        borderWidth: 2,
        hoverBorderWidth: 3,
      },
    ],
  }

  const options: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
          color: theme.palette.text.primary,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: theme.palette.background.paper,
        titleColor: theme.palette.text.primary,
        bodyColor: theme.palette.text.primary,
        borderColor: theme.palette.divider,
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : '0'
            return `${context.label}: ${context.parsed} (${percentage}%)`
          },
        },
      },
    },
    cutout: '60%',
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title="Vulnerability Severity Distribution"
        titleTypographyProps={{ variant: 'h6', fontWeight: 600 }}
      />
      <CardContent>
        <Box sx={{ position: 'relative', height: 300 }}>
          {total > 0 ? (
            <>
              <Doughnut data={chartData} options={options} />
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                }}
              >
                <Typography variant="h4" sx={{ fontWeight: 700, color: theme.palette.primary.main }}>
                  {total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Findings
                </Typography>
              </Box>
            </>
          ) : (
            <Box
              sx={{
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                color: 'text.secondary',
              }}
            >
              <Typography variant="h6" sx={{ mb: 1 }}>
                No vulnerabilities found
              </Typography>
              <Typography variant="body2">
                Great! Your applications appear to be secure.
              </Typography>
            </Box>
          )}
        </Box>

        {total > 0 && (
          <Box sx={{ mt: 3, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="error.main" sx={{ fontWeight: 600 }}>
                {data.critical}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Critical
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="warning.main" sx={{ fontWeight: 600 }}>
                {data.high}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                High
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="info.main" sx={{ fontWeight: 600 }}>
                {data.medium}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Medium
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="success.main" sx={{ fontWeight: 600 }}>
                {data.low}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Low
              </Typography>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

export default SeverityChart
