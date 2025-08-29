# BAC Hunter Frontend

Advanced React-based user interface for the BAC Hunter security testing platform.

## 🚀 Features

- **Modern UI/UX**: Built with React 18, TypeScript, and Material-UI
- **Real-time Updates**: WebSocket integration for live scan monitoring
- **Advanced Visualizations**: Interactive charts and graphs using Chart.js and D3.js
- **AI-Powered Insights**: Dedicated interface for AI recommendations and analysis
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Dark/Light Theme**: Customizable theme with system preference detection
- **Progressive Web App**: Offline support and installable as PWA

## 🛠 Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI) v5
- **State Management**: Zustand
- **Data Fetching**: React Query
- **Charts**: Chart.js, Recharts, D3.js
- **Routing**: React Router v6
- **Styling**: Emotion (CSS-in-JS)
- **Icons**: Material Icons
- **Notifications**: React Hot Toast
- **Animations**: Framer Motion

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── dashboard/       # Dashboard-specific components
│   │   ├── Layout.tsx       # Main layout component
│   │   └── ...
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx   # Main dashboard
│   │   ├── Projects.tsx    # Project management
│   │   ├── Findings.tsx    # Vulnerability findings
│   │   └── ...
│   ├── services/           # API and external services
│   │   └── api.ts          # API client
│   ├── store/              # State management
│   │   └── index.ts        # Zustand stores
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts        # Global types
│   ├── theme.ts            # Material-UI theme
│   ├── App.tsx             # Root component
│   └── main.tsx            # Entry point
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite configuration
└── tsconfig.json           # TypeScript configuration
```

## 🏃‍♂️ Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- BAC Hunter backend running on port 8000

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```

3. **Open browser:**
   Navigate to `http://localhost:3000`

### Production Build

1. **Build for production:**
   ```bash
   npm run build
   ```

2. **Preview production build:**
   ```bash
   npm run preview
   ```

The built files will be in the `../bac_hunter/webapp/static/dist` directory, ready to be served by the FastAPI backend.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
VITE_APP_TITLE=BAC Hunter
```

### Proxy Configuration

The development server is configured to proxy API requests to the backend:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    }
  }
}
```

## 📊 Dashboard Features

### Real-time Statistics
- Live project and scan counters
- Vulnerability severity distribution
- System health monitoring
- Performance metrics

### Interactive Charts
- Vulnerability severity pie chart
- Activity trend lines
- Network topology graphs
- Heatmaps for vulnerability distribution

### AI Insights Widget
- Real-time AI recommendations
- Confidence scoring
- Priority-based insights
- Learning progress indicators

### Project Management
- Project overview cards
- Status indicators
- Quick actions
- Recent activity timeline

## 🎨 Theming

The application supports both dark and light themes with automatic system preference detection:

```typescript
// theme.ts
export const theme = createTheme({
  palette: {
    mode: 'dark', // or 'light'
    primary: { main: '#3498db' },
    secondary: { main: '#2c3e50' },
    // ... custom color palette
  }
})
```

## 🔌 API Integration

### REST API Client
```typescript
// services/api.ts
export const projectsAPI = {
  getAll: () => api.get('/projects'),
  create: (data) => api.post('/projects', data),
  // ... other endpoints
}
```

### WebSocket Connection
```typescript
// Real-time updates
const ws = createWebSocketConnection('/ws')
ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  // Handle real-time updates
}
```

## 🧪 Development

### Code Quality
- **Linting**: ESLint with TypeScript rules
- **Type Checking**: Strict TypeScript configuration
- **Formatting**: Prettier integration

### Testing
```bash
npm run test          # Run tests
npm run test:coverage # Run with coverage
```

### Build Analysis
```bash
npm run build:analyze # Analyze bundle size
```

## 📱 Progressive Web App

The application is configured as a PWA with:
- Service worker for offline support
- Web app manifest for installation
- Optimized caching strategies
- Background sync capabilities

## 🚀 Deployment

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
# Files are built to ../bac_hunter/webapp/static/dist/
# Start the FastAPI backend to serve the frontend
```

### Docker
```bash
# Build frontend
docker build -t bac-hunter-frontend .

# Or use the main BAC Hunter Docker setup
cd ..
docker-compose up
```

## 🔒 Security Features

- **CSP Headers**: Content Security Policy implementation
- **XSS Protection**: Input sanitization and validation
- **CSRF Protection**: Token-based request validation
- **Secure WebSocket**: WSS in production
- **Authentication**: JWT token management

## 📈 Performance Optimizations

- **Code Splitting**: Automatic route-based splitting
- **Lazy Loading**: Dynamic imports for heavy components
- **Bundle Optimization**: Tree shaking and minification
- **Caching**: Aggressive caching strategies
- **Virtual Scrolling**: For large data sets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of BAC Hunter and follows the same license terms.

## 🆘 Support

For issues and questions:
1. Check the main BAC Hunter documentation
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**BAC Hunter Frontend v3.0** - Advanced Security Testing Platform Interface
