
// Enhanced API service with multi-model support
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL ||
  process.env.REACT_APP_API_BASE_URL ||
  'https://zb9j38oxx5.execute-api.us-east-1.amazonaws.com/prod';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      error.message = error.response.data?.error || `Server error: ${error.response.status}`;
    } else if (error.request) {
      error.message = 'No response from server';
    }
    return Promise.reject(error);
  }
);

export const analysisService = {
  // Enhanced analysis with multi-model support
  startAnalysis: async (sequenceData) => {
    // Send as JSON directly (matching test.html)
    return apiClient.post('/analyze', {
      sequence: sequenceData,
      analysis_type: 'genomics',
      use_multi_model: true,
      real_time: true
    });
  },

  // Real-time multi-model analysis
  analyzeWithMultiModel: async (sequenceData) => {
    return apiClient.post('/analyze', {
      sequence: sequenceData,
      analysis_type: 'genomics',
      use_multi_model: true,
      real_time: true
    });
  },

  getWorkflowStatus: async (workflowId) => {
    return apiClient.get(`/workflow/${workflowId}/status`);
  },

  getWorkflowResults: async (workflowId) => {
    return apiClient.get(`/workflow/${workflowId}/results`);
  },

  getAnalysisResults: async (workflowId) => {
    return apiClient.get(`/workflow/${workflowId}/results`);
  },

  getSampleData: async () => {
    return {
      data: {
        samples: [
          {
            type: 'brca1',
            filename: 'brca1_sample.fasta',
            content: '>BRCA1_sample\nATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAAT'
          },
          {
            type: 'tp53',
            filename: 'tp53_sample.fasta',
            content: '>TP53_sample\nATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAA'
          }
        ]
      }
    };
  }
};

export const handleApiError = (error) => {
  if (error.response) {
    return error.response.data?.error || `Server error: ${error.response.status}`;
  } else if (error.request) {
    return 'No response from server';
  }
  return error.message || 'Unknown error occurred';
};

export const demoService = {
  getDemoScenarios: async () => {
    return {
      data: {
        scenarios: [
          {
            id: 'brca1',
            name: 'BRCA1 Gene Analysis',
            description: 'Breast cancer susceptibility gene',
            sequence: '>BRCA1_sample\nATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAAT'
          }
        ]
      }
    };
  }
};

export default apiClient;
