#!/usr/bin/env python3
"""
Complete Frontend Fix Script - Creates all missing files and fixes issues
"""

import os
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent
frontend_services = project_root / "frontend" / "src" / "services"

# Create services directory if it doesn't exist
frontend_services.mkdir(parents=True, exist_ok=True)

# Complete API service code
api_service_code = """import axios from 'axios';

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
      error.message = error.response.data?.error || error.response.data?.message || `Server error: ${error.response.status}`;
    } else if (error.request) {
      error.message = 'No response from server. Please check your connection.';
    }
    return Promise.reject(error);
  }
);

export const analysisService = {
  startAnalysis: async (formData) => {
    return await apiClient.post('/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getAnalysisStatus: async (workflowId) => {
    return await apiClient.get(`/analysis/${workflowId}/status`);
  },
  getAnalysisResults: async (workflowId) => {
    return await apiClient.get(`/analysis/${workflowId}/results`);
  },
  getSampleData: async () => {
    return { data: {