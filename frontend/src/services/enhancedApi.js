import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for long-running analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging and auth
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response || error.message);
    
    // Handle specific error cases
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Handle unauthorized
          console.error('Unauthorized access');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 500:
          console.error('Server error');
          break;
        default:
          console.error(`Error ${error.response.status}: ${error.response.data?.error || 'Unknown error'}`);
      }
    }
    
    return Promise.reject(error);
  }
);

/**
 * Enhanced API Service for Biomerkin Analysis
 * Provides comprehensive API methods for dataset handling and analysis
 */
const enhancedApiService = {
  /**
   * Upload and validate dataset
   */
  async uploadAndValidateDataset(file) {
    try {
      // Step 1: Upload file to S3 via presigned URL
      const uploadUrlResponse = await apiClient.post('/upload-url', {
        filename: file.name,
        content_type: file.type || 'application/octet-stream',
      });
      
      const { upload_url, file_key } = uploadUrlResponse.data;
      
      // Step 2: Upload file directly to S3
      await axios.put(upload_url, file, {
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
        },
      });
      
      // Step 3: Validate the uploaded dataset
      const validationResponse = await apiClient.post('/validate-dataset', {
        file_key,
      });
      
      return {
        file_key,
        validation: validationResponse.data.validation,
        success: true,
      };
    } catch (error) {
      console.error('Upload and validation error:', error);
      throw error;
    }
  },

  /**
   * Validate dataset without uploading
   */
  async validateDataset(fileKey) {
    try {
      const response = await apiClient.post('/validate-dataset', {
        file_key: fileKey,
      });
      return response.data;
    } catch (error) {
      console.error('Validation error:', error);
      throw error;
    }
  },

  /**
   * Start comprehensive analysis
   */
  async startAnalysis(fileKey, options = {}) {
    try {
      const response = await apiClient.post('/analyze', {
        file_key: fileKey,
        options: {
          enable_enhanced_bedrock: true,
          include_literature: true,
          include_drug_discovery: true,
          generate_medical_report: true,
          ...options,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Analysis start error:', error);
      throw error;
    }
  },

  /**
   * Get workflow status
   */
  async getWorkflowStatus(workflowId) {
    try {
      const response = await apiClient.get(`/workflows/${workflowId}/status`);
      return response.data;
    } catch (error) {
      console.error('Status check error:', error);
      throw error;
    }
  },

  /**
   * Get analysis results
   */
  async getAnalysisResults(workflowId) {
    try {
      const response = await apiClient.get(`/workflows/${workflowId}/results`);
      return response.data;
    } catch (error) {
      console.error('Results fetch error:', error);
      throw error;
    }
  },

  /**
   * Download medical report
   */
  async downloadMedicalReport(workflowId, format = 'pdf') {
    try {
      const response = await apiClient.get(`/workflows/${workflowId}/report`, {
        params: { format },
        responseType: 'blob',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `medical_report_${workflowId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true };
    } catch (error) {
      console.error('Report download error:', error);
      throw error;
    }
  },

  /**
   * List all workflows
   */
  async listWorkflows(filters = {}) {
    try {
      const response = await apiClient.get('/workflows', {
        params: filters,
      });
      return response.data;
    } catch (error) {
      console.error('Workflows list error:', error);
      throw error;
    }
  },

  /**
   * Delete workflow
   */
  async deleteWorkflow(workflowId) {
    try {
      const response = await apiClient.delete(`/workflows/${workflowId}`);
      return response.data;
    } catch (error) {
      console.error('Workflow deletion error:', error);
      throw error;
    }
  },

  /**
   * Get system health status
   */
  async getSystemHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  },

  /**
   * Get sample datasets
   */
  async getSampleDatasets() {
    try {
      const response = await apiClient.get('/samples');
      return response.data;
    } catch (error) {
      console.error('Sample datasets error:', error);
      throw error;
    }
  },

  /**
   * Load sample dataset
   */
  async loadSampleDataset(sampleId) {
    try {
      const response = await apiClient.post('/samples/load', {
        sample_id: sampleId,
      });
      return response.data;
    } catch (error) {
      console.error('Load sample error:', error);
      throw error;
    }
  },

  /**
   * Real-time progress tracking using polling
   */
  async trackProgress(workflowId, onProgress, intervalMs = 2000) {
    const pollStatus = async () => {
      try {
        const status = await this.getWorkflowStatus(workflowId);
        
        if (onProgress) {
          onProgress(status);
        }
        
        // Continue polling if not completed
        if (status.status === 'running' || status.status === 'pending') {
          setTimeout(pollStatus, intervalMs);
        }
        
        return status;
      } catch (error) {
        console.error('Progress tracking error:', error);
        // Retry after delay
        setTimeout(pollStatus, intervalMs);
      }
    };
    
    // Start polling
    return pollStatus();
  },

  /**
   * Batch analysis for multiple files
   */
  async batchAnalysis(fileKeys, options = {}) {
    try {
      const response = await apiClient.post('/analyze/batch', {
        file_keys: fileKeys,
        options,
      });
      return response.data;
    } catch (error) {
      console.error('Batch analysis error:', error);
      throw error;
    }
  },

  /**
   * Compare multiple analysis results
   */
  async compareAnalyses(workflowIds) {
    try {
      const response = await apiClient.post('/analyze/compare', {
        workflow_ids: workflowIds,
      });
      return response.data;
    } catch (error) {
      console.error('Analysis comparison error:', error);
      throw error;
    }
  },

  /**
   * Export results in various formats
   */
  async exportResults(workflowId, format = 'json') {
    try {
      const response = await apiClient.get(`/workflows/${workflowId}/export`, {
        params: { format },
        responseType: format === 'json' ? 'json' : 'blob',
      });
      
      if (format !== 'json') {
        // Download file
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `results_${workflowId}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      }
      
      return response.data;
    } catch (error) {
      console.error('Export error:', error);
      throw error;
    }
  },

  /**
   * Get analysis statistics
   */
  async getAnalysisStatistics(workflowId) {
    try {
      const response = await apiClient.get(`/workflows/${workflowId}/statistics`);
      return response.data;
    } catch (error) {
      console.error('Statistics error:', error);
      throw error;
    }
  },

  /**
   * Provide feedback on analysis
   */
  async submitFeedback(workflowId, feedback) {
    try {
      const response = await apiClient.post(`/workflows/${workflowId}/feedback`, {
        rating: feedback.rating,
        comments: feedback.comments,
        accuracy_score: feedback.accuracyScore,
      });
      return response.data;
    } catch (error) {
      console.error('Feedback submission error:', error);
      throw error;
    }
  },
};

export default enhancedApiService;

// Export individual methods for convenience
export const {
  uploadAndValidateDataset,
  validateDataset,
  startAnalysis,
  getWorkflowStatus,
  getAnalysisResults,
  downloadMedicalReport,
  listWorkflows,
  deleteWorkflow,
  getSystemHealth,
  getSampleDatasets,
  loadSampleDataset,
  trackProgress,
  batchAnalysis,
  compareAnalyses,
  exportResults,
  getAnalysisStatistics,
  submitFeedback,
} = enhancedApiService;

