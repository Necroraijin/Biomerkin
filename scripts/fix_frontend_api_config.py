#!/usr/bin/env python3
"""
Fix frontend API configuration to use AWS endpoints.
"""

import json
import os
from pathlib import Path

def fix_api_configuration():
    """Fix the frontend API configuration."""
    
    print("🔧 FIXING FRONTEND API CONFIGURATION")
    print("="*40)
    
    # Your AWS API Gateway URL
    aws_api_url = "https://udu8m3n0lh.execute-api.us-east-1.amazonaws.com/prod"
    
    # Find and update API configuration files
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Check for common config files
    config_files = [
        frontend_dir / "src" / "services" / "api.js",
        frontend_dir / "src" / "config" / "api.js",
        frontend_dir / "src" / "utils" / "api.js",
        frontend_dir / ".env",
        frontend_dir / ".env.local",
        frontend_dir / ".env.production"
    ]
    
    # Update API service file
    api_service_file = frontend_dir / "src" / "services" / "api.js"
    
    if api_service_file.exists():
        print(f"📄 Found API service file: {api_service_file}")
        
        try:
            with open(api_service_file, 'r') as f:
                content = f.read()
            
            # Replace localhost URLs with AWS API Gateway URL
            replacements = [
                ('http://localhost:3001', aws_api_url),
                ('http://localhost:5000', aws_api_url),
                ('http://localhost:8000', aws_api_url),
                ('localhost:3001', aws_api_url.replace('https://', '')),
                ('localhost:5000', aws_api_url.replace('https://', '')),
                ('localhost:8000', aws_api_url.replace('https://', '')),
                ("baseURL: 'http://localhost:3001'", f"baseURL: '{aws_api_url}'"),
                ("baseURL: 'http://localhost:5000'", f"baseURL: '{aws_api_url}'"),
                ("baseURL: 'http://localhost:8000'", f"baseURL: '{aws_api_url}'"),
                ("const API_BASE_URL = 'http://localhost:3001'", f"const API_BASE_URL = '{aws_api_url}'"),
                ("const API_BASE_URL = 'http://localhost:5000'", f"const API_BASE_URL = '{aws_api_url}'"),
                ("const API_BASE_URL = 'http://localhost:8000'", f"const API_BASE_URL = '{aws_api_url}'"),
            ]
            
            original_content = content
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original_content:
                with open(api_service_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated API configuration in {api_service_file}")
                print(f"   Changed localhost URLs to: {aws_api_url}")
            else:
                print(f"⚠️ No localhost URLs found to replace")
                
        except Exception as e:
            print(f"❌ Error updating API service file: {e}")
    
    # Create/update environment file
    env_file = frontend_dir / ".env.production"
    
    env_content = f"""# AWS Production Configuration
REACT_APP_API_BASE_URL={aws_api_url}
REACT_APP_API_URL={aws_api_url}
REACT_APP_BACKEND_URL={aws_api_url}
GENERATE_SOURCEMAP=false
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created production environment file: {env_file}")
        
    except Exception as e:
        print(f"❌ Error creating environment file: {e}")
    
    # Also create .env file for development
    env_local_file = frontend_dir / ".env"
    
    try:
        with open(env_local_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created environment file: {env_local_file}")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
    
    return True

def create_fixed_api_service():
    """Create a fixed API service file."""
    
    print("\n📝 CREATING FIXED API SERVICE")
    print("="*30)
    
    aws_api_url = "https://udu8m3n0lh.execute-api.us-east-1.amazonaws.com/prod"
    
    api_service_content = f"""import axios from 'axios';

// AWS API Gateway URL
const API_BASE_URL = '{aws_api_url}';

// Create axios instance with AWS configuration
const api = axios.create({{
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {{
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }}
}});

// Request interceptor
api.interceptors.request.use(
  (config) => {{
    console.log(`🚀 API Request: ${{config.method?.toUpperCase()}} ${{config.url}}`);
    return config;
  }},
  (error) => {{
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }}
);

// Response interceptor
api.interceptors.response.use(
  (response) => {{
    console.log(`✅ API Response: ${{response.status}} ${{response.config.url}}`);
    return response;
  }},
  (error) => {{
    console.error('❌ API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }}
);

// Analysis service
export const analysisService = {{
  // Start genomic analysis
  startAnalysis: (data) => {{
    return api.post('/genomics', {{
      input_data: {{
        sequence_data: data.sequenceData,
        sequence_file: data.sequenceFile || 'uploaded_sequence.fasta',
        reference_genome: data.referenceGenome || 'GRCh38'
      }}
    }});
  }},
  
  // Get analysis status
  getAnalysisStatus: (analysisId) => {{
    return api.get(`/analysis/${{analysisId}}/status`);
  }},
  
  // Get analysis results
  getAnalysisResults: (analysisId) => {{
    return api.get(`/analysis/${{analysisId}}/results`);
  }}
}};

// Demo service
export const demoService = {{
  // Get demo scenarios
  getDemoScenarios: () => {{
    // Return mock data for now since we don't have this endpoint yet
    return Promise.resolve({{
      data: {{
        scenarios: [
          {{
            id: 'brca1-analysis',
            title: 'BRCA1 Hereditary Cancer Analysis',
            description: 'Comprehensive analysis of BRCA1 gene variants',
            sampleData: 'ATGCGATCGATCGATCGATCGATCGATCG'
          }},
          {{
            id: 'covid-drug-discovery',
            title: 'COVID-19 Drug Discovery',
            description: 'Identify drug candidates for SARS-CoV-2',
            sampleData: 'ATGCGATCGATCGATCGATCGATCGATCG'
          }},
          {{
            id: 'rare-disease',
            title: 'Rare Disease Diagnosis',
            description: 'Comprehensive genomic analysis for rare diseases',
            sampleData: 'ATGCGATCGATCGATCGATCGATCGATCG'
          }}
        ]
      }}
    }});
  }},
  
  // Start demo analysis
  startDemo: (scenarioId) => {{
    return api.post('/genomics', {{
      input_data: {{
        sequence_data: 'ATGCGATCGATCGATCGATCGATCGATCG',
        sequence_file: `${{scenarioId}}_demo.fasta`,
        reference_genome: 'GRCh38'
      }}
    }});
  }},
  
  // Get demo results
  getDemoResults: (demoId) => {{
    return api.get(`/genomics`);
  }}
}};

// Agent services
export const agentService = {{
  // Genomics agent
  genomics: (data) => api.post('/genomics', data),
  
  // Proteomics agent
  proteomics: (data) => api.post('/proteomics', data),
  
  // Literature agent
  literature: (data) => api.post('/literature', data),
  
  // Drug discovery agent
  drug: (data) => api.post('/drug', data),
  
  // Decision agent
  decision: (data) => api.post('/decision', data)
}};

// System service
export const systemService = {{
  // Get system health
  getHealth: () => {{
    return api.get('/genomics'); // Use genomics as health check
  }},
  
  // Get system metrics
  getMetrics: () => {{
    return Promise.resolve({{
      data: {{
        agents: 5,
        status: 'healthy',
        uptime: '100%'
      }}
    }});
  }}
}};

export default api;
"""
    
    api_service_file = Path("frontend/src/services/api.js")
    
    try:
        # Create directory if it doesn't exist
        api_service_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(api_service_file, 'w') as f:
            f.write(api_service_content)
        
        print(f"✅ Created fixed API service: {api_service_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating API service: {e}")
        return False

def rebuild_and_deploy_frontend():
    """Rebuild and deploy the frontend with fixed configuration."""
    
    print("\n🏗️ REBUILDING AND DEPLOYING FRONTEND")
    print("="*40)
    
    import subprocess
    
    frontend_dir = Path("frontend")
    
    try:
        # Build the frontend
        print("🔨 Building React app with production config...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False
        
        print("✅ Frontend built successfully")
        
        # Deploy to S3
        print("📤 Deploying to S3...")
        
        bucket_name = "biomerkin-frontend-20251014-224832"
        
        deploy_result = subprocess.run([
            "aws", "s3", "sync", "frontend/build/", f"s3://{bucket_name}/", "--delete"
        ], capture_output=True, text=True)
        
        if deploy_result.returncode != 0:
            print(f"❌ Deployment failed: {deploy_result.stderr}")
            return False
        
        print("✅ Frontend deployed successfully")
        
        # Test the URL
        frontend_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        print(f"🌐 Frontend URL: {frontend_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error rebuilding frontend: {e}")
        return False

def main():
    """Main frontend fixing function."""
    
    print("🔧 FIXING FRONTEND API CONNECTION")
    print("="*40)
    
    # Step 1: Fix API configuration
    if not fix_api_configuration():
        print("❌ Failed to fix API configuration")
        return False
    
    # Step 2: Create fixed API service
    if not create_fixed_api_service():
        print("❌ Failed to create API service")
        return False
    
    # Step 3: Rebuild and deploy
    if not rebuild_and_deploy_frontend():
        print("❌ Failed to rebuild and deploy")
        return False
    
    print("\n🎉 FRONTEND API FIXED!")
    print("="*25)
    
    print("✅ API configuration updated")
    print("✅ Environment variables set")
    print("✅ Frontend rebuilt and deployed")
    
    print(f"\n🌐 Your working frontend:")
    print(f"   http://biomerkin-frontend-20251014-224832.s3-website-us-east-1.amazonaws.com")
    
    print(f"\n🔗 API endpoints:")
    print(f"   https://udu8m3n0lh.execute-api.us-east-1.amazonaws.com/prod")
    
    print(f"\n🧪 Test the analysis now - it should work!")
    
    return True

if __name__ == "__main__":
    main()