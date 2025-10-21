// Complete API Service for Biomerkin Frontend
const fs = require('fs');
const path = require('path');

const apiServiceContent = `import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 
                     process.env.REACT_APP_API_BASE_URL || 
                     'https://udu8m3n0lh.execute-api.us-east-1.amazonaws.com/prod';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      error.message = error.response.data?.error || \`Server error: \${error.response.status}\`;
    } else if (error.request) {
      error.message = 'No response from server';
    }
    return Promise.reject(error);
  }
);

export const analysisService = {
  startAnalysis: async (formData) => {
    return apiClient.post('/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  getWorkflowStatus: async (workflowId) => {
    return apiClient.get(\`/workflow/\${workflowId}/status\`);
  },
  
  getWorkflowResults: async (workflowId) => {
    return apiClient.get(\`/workflow/\${workflowId}/results\`);
  },
  
  getSampleData: async () => {
    return {
      data: {
        samples: [
          {
            type: 'brca1',
            filename: 'brca1_sample.fasta',
            content: '>BRCA1_sample\\nATGGATTTATCTGCTCTTCGCGTTGAAGAAGTACAAAATGTCATTAATGCTATGCAGAAAATCTTAGAGTGTCCCATCTGTCTGGAGTTGATCAAGGAACCTGTCTCCACAAAGTGTGACCACATATTTTGCAAAT'
          },
          {
            type: 'tp53',
            filename: 'tp53_sample.fasta',
            content: '>TP53_sample\\nATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAA'
          }
        ]
      }
    };
  }
};

export default apiClient;
`;

const apiPath = path.join(__dirname, '..', 'frontend', 'src', 'services', 'api.js');
fs.writeFileSync(apiPath, apiServiceContent);
console.log('✅ API service file created successfully');
