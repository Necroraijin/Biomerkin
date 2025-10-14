import axios from 'axios';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3001/api',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add request timestamp
    config.metadata = { startTime: new Date() };
    
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Calculate request duration
    const duration = new Date() - response.config.metadata.startTime;
    console.log(`API Response: ${response.status} ${response.config.url} (${duration}ms)`);
    
    return response;
  },
  (error) => {
    const duration = error.config?.metadata ? new Date() - error.config.metadata.startTime : 0;
    console.error(`API Error: ${error.response?.status || 'Network'} ${error.config?.url} (${duration}ms)`, error);
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Unauthorized - clear auth token and redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      // Rate limited - show user-friendly message
      error.userMessage = 'Too many requests. Please wait a moment and try again.';
    } else if (error.code === 'ECONNABORTED') {
      // Timeout
      error.userMessage = 'Request timed out. Please check your connection and try again.';
    } else if (!error.response) {
      // Network error
      error.userMessage = 'Network error. Please check your connection and try again.';
    }
    
    return Promise.reject(error);
  }
);

// API service methods
export const analysisService = {
  // Start a new analysis
  startAnalysis: (formData) => {
    return api.post('/analysis/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Get analysis status
  getAnalysisStatus: (workflowId) => {
    return api.get(`/analysis/status/${workflowId}`);
  },
  
  // Get analysis results
  getAnalysisResults: (workflowId) => {
    return api.get(`/analysis/results/${workflowId}`);
  },
  
  // Download analysis report
  downloadReport: (workflowId, format = 'pdf') => {
    return api.get(`/analysis/report/${workflowId}`, {
      params: { format },
      responseType: 'blob',
    });
  },
  
  // Get sample data
  getSampleData: () => {
    return api.get('/analysis/samples');
  },
  
  // Cancel analysis
  cancelAnalysis: (workflowId) => {
    return api.post(`/analysis/cancel/${workflowId}`);
  },
};

export const demoService = {
  // Get demo scenarios
  getDemoScenarios: () => {
    return api.get('/demo/scenarios');
  },
  
  // Start demo analysis
  startDemo: (scenarioId) => {
    return api.post(`/demo/start/${scenarioId}`);
  },
  
  // Get demo results
  getDemoResults: (demoId) => {
    return api.get(`/demo/results/${demoId}`);
  },
};

export const systemService = {
  // Get system health
  getHealth: () => {
    return api.get('/health');
  },
  
  // Get system metrics
  getMetrics: () => {
    return api.get('/metrics');
  },
  
  // Get agent status
  getAgentStatus: () => {
    return api.get('/agents/status');
  },
};

// Utility functions
export const handleApiError = (error) => {
  if (error.userMessage) {
    return error.userMessage;
  }
  
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  return 'An unexpected error occurred. Please try again.';
};

export const isNetworkError = (error) => {
  return !error.response && error.code !== 'ECONNABORTED';
};

export const isTimeoutError = (error) => {
  return error.code === 'ECONNABORTED';
};

export const isServerError = (error) => {
  return error.response && error.response.status >= 500;
};

export const isClientError = (error) => {
  return error.response && error.response.status >= 400 && error.response.status < 500;
};

// Export the configured axios instance as default
export default api;