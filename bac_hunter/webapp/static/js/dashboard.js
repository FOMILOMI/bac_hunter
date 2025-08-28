// BAC Hunter Dashboard JavaScript

class BACDashboard {
    constructor() {
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadInitialData();
    }

    setupEventListeners() {
        // New project form
        const newProjectForm = document.getElementById('new-project-form');
        if (newProjectForm) {
            newProjectForm.addEventListener('submit', (e) => this.handleNewProject(e));
        }

        // Quick scan form
        const quickScanForm = document.getElementById('quick-scan-form');
        if (quickScanForm) {
            quickScanForm.addEventListener('submit', (e) => this.handleQuickScan(e));
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }
    }

    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.subscribeToUpdates();
            };
            
            this.websocket.onmessage = (event) => {
                this.handleWebSocketMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.handleWebSocketDisconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }

    handleWebSocketDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connectWebSocket();
            }, delay);
        }
    }

    subscribeToUpdates() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'subscribe_updates'
            }));
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'scan_progress':
                this.updateScanProgress(data);
                break;
            case 'new_finding':
                this.addNewFinding(data);
                break;
            case 'ai_insight':
                this.addAIInsight(data);
                break;
            case 'project_update':
                this.updateProject(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    async loadInitialData() {
        try {
            // Load projects
            const projectsResponse = await fetch('/api/v2/projects');
            if (projectsResponse.ok) {
                const projects = await projectsResponse.json();
                this.renderProjects(projects);
            }

            // Load statistics
            const statsResponse = await fetch('/api/v2/stats');
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                this.updateStats(stats);
            }

            // Load recent activity
            const activityResponse = await fetch('/api/v2/activity');
            if (activityResponse.ok) {
                const activity = await activityResponse.json();
                this.renderRecentActivity(activity);
            }
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showNotification('Failed to load dashboard data', 'error');
        }
    }

    async handleNewProject(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const projectData = {
            name: formData.get('name'),
            description: formData.get('description'),
            target_url: formData.get('target_url'),
            scan_config: {
                scan_type: formData.get('scan_type') || 'comprehensive',
                ai_enabled: formData.get('ai_enabled') === 'on',
                rl_optimization: formData.get('rl_optimization') === 'on'
            }
        };

        try {
            const response = await fetch('/api/v2/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(projectData)
            });

            if (response.ok) {
                const project = await response.json();
                this.showNotification('Project created successfully', 'success');
                this.addProjectToList(project);
                event.target.reset();
            } else {
                const error = await response.json();
                this.showNotification(`Failed to create project: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to create project:', error);
            this.showNotification('Failed to create project', 'error');
        }
    }

    async handleQuickScan(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const target = formData.get('target');
        
        if (!target) {
            this.showNotification('Please enter a target URL', 'error');
            return;
        }

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `target=${encodeURIComponent(target)}`
            });

            if (response.ok) {
                this.showNotification('Quick scan started', 'success');
                this.refreshData();
            } else {
                const error = await response.json();
                this.showNotification(`Scan failed: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to start scan:', error);
            this.showNotification('Failed to start scan', 'error');
        }
    }

    renderProjects(projects) {
        const projectsContainer = document.getElementById('projects-container');
        if (!projectsContainer) return;

        projectsContainer.innerHTML = '';
        
        projects.forEach(project => {
            const projectCard = this.createProjectCard(project);
            projectsContainer.appendChild(projectCard);
        });
    }

    createProjectCard(project) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4 mb-4';
        
        col.innerHTML = `
            <div class="card project-card" onclick="dashboard.openProject('${project.id}')">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${project.name}</h6>
                </div>
                <div class="card-body">
                    <p class="text-muted">${project.description}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="status-badge status-${project.status}">${project.status}</span>
                        <small class="text-muted">${project.finding_count} findings</small>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">${project.target_url}</small>
                    </div>
                </div>
            </div>
        `;
        
        return col;
    }

    updateStats(stats) {
        const elements = {
            'total-projects': stats.total_projects || 0,
            'active-scans': stats.active_scans || 0,
            'total-findings': stats.total_findings || 0,
            'ai-insights-count': stats.ai_insights_count || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    renderRecentActivity(activity) {
        const activityList = document.getElementById('recent-activity');
        if (!activityList) return;

        activityList.innerHTML = '';
        
        activity.forEach(item => {
            const activityItem = document.createElement('div');
            activityItem.className = 'list-group-item';
            activityItem.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${item.title}</h6>
                    <small class="text-muted">${new Date(item.timestamp).toLocaleTimeString()}</small>
                </div>
                <p class="mb-1">${item.description}</p>
            `;
            activityList.appendChild(activityItem);
        });
    }

    updateScanProgress(data) {
        const progressElement = document.querySelector(`[data-scan-id="${data.scan_id}"] .progress-bar`);
        if (progressElement) {
            progressElement.style.width = `${data.progress}%`;
            progressElement.textContent = `${data.progress}%`;
        }
    }

    addNewFinding(data) {
        const activityList = document.getElementById('recent-activity');
        if (!activityList) return;

        const activityItem = document.createElement('div');
        activityItem.className = 'list-group-item';
        activityItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">New ${data.severity} finding detected</h6>
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
            </div>
            <p class="mb-1">${data.description}</p>
        `;
        
        activityList.insertBefore(activityItem, activityList.firstChild);
        
        // Keep only last 10 items
        while (activityList.children.length > 10) {
            activityList.removeChild(activityList.lastChild);
        }
    }

    addAIInsight(data) {
        const recommendationsDiv = document.getElementById('ai-recommendations');
        if (!recommendationsDiv) return;

        const insightDiv = document.createElement('div');
        insightDiv.className = 'ai-insight';
        insightDiv.innerHTML = `
            <h6><i class="fas fa-lightbulb"></i> ${data.title}</h6>
            <p class="mb-0">${data.description}</p>
        `;
        
        recommendationsDiv.insertBefore(insightDiv, recommendationsDiv.firstChild);
        
        // Keep only last 5 insights
        while (recommendationsDiv.children.length > 5) {
            recommendationsDiv.removeChild(recommendationsDiv.lastChild);
        }
    }

    addProjectToList(project) {
        const projectsContainer = document.getElementById('projects-container');
        if (!projectsContainer) return;

        const projectCard = this.createProjectCard(project);
        projectsContainer.insertBefore(projectCard, projectsContainer.firstChild);
    }

    updateProject(data) {
        // Update project in the list
        const projectElement = document.querySelector(`[data-project-id="${data.project_id}"]`);
        if (projectElement) {
            // Update project status and other details
            const statusElement = projectElement.querySelector('.status-badge');
            if (statusElement) {
                statusElement.className = `status-badge status-${data.status}`;
                statusElement.textContent = data.status;
            }
        }
    }

    async refreshData() {
        await this.loadInitialData();
        this.showNotification('Data refreshed', 'success');
    }

    openProject(projectId) {
        window.location.href = `/project/${projectId}`;
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new BACDashboard();
});