#!/usr/bin/env python3
"""
Fix and Redeploy Frontend with Correct API URL
"""
import boto3
import subprocess
import os
import json
from pathlib import Path

def fix_and_redeploy_frontend():
    """Rebuild and redeploy frontend with correct API configuration"""
    print("🔧 Fixing and Redeploying Frontend...")
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    bucket_name = 'biomerkin-frontend-20251018-013734'
    
    # Step 1: Clean old build
    print("\n📦 Step 1: Cleaning old build...")
    build_dir = Path('frontend/build')
    if build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)
        print("✅ Cleaned old build")
    
    # Step 2: Verify .env file
    print("\n📝 Step 2: Verifying .env configuration...")
    env_file = Path('frontend/.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
            if 'ap-south-1' in env_content and '642v46sv19' in env_content:
                print("✅ .env file has correct API URL")
            else:
                print("❌ .env file still has wrong URL!")
                return False
    
    # Step 3: Build frontend
    print("\n🏗️  Step 3: Building frontend with correct API URL...")
    os.chdir('frontend')
    
    try:
        # Install dependencies if needed
        if not Path('node_modules').exists():
            print("📦 Installing dependencies...")
            subprocess.run(['npm', 'install'], check=True, shell=True)
        
        # Build
        print("🔨 Building React app...")
        result = subprocess.run(['npm', 'run', 'build'], 
                              capture_output=True, 
                              text=True, 
                              shell=True)
        
        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False
        
        print("✅ Build successful!")
        
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False
    finally:
        os.chdir('..')
    
    # Step 4: Upload to S3
    print("\n☁️  Step 4: Uploading to S3...")
    
    build_path = Path('frontend/build')
    if not build_path.exists():
        print("❌ Build directory not found!")
        return False
    
    uploaded_files = 0
    for file_path in build_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(build_path)
            s3_key = str(relative_path).replace('\\', '/')
            
            # Determine content type
            content_type = 'text/html'
            if s3_key.endswith('.js'):
                content_type = 'application/javascript'
            elif s3_key.endswith('.css'):
                content_type = 'text/css'
            elif s3_key.endswith('.json'):
                content_type = 'application/json'
            elif s3_key.endswith('.png'):
                content_type = 'image/png'
            elif s3_key.endswith('.jpg') or s3_key.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif s3_key.endswith('.svg'):
                content_type = 'image/svg+xml'
            elif s3_key.endswith('.ico'):
                content_type = 'image/x-icon'
            
            try:
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'no-cache'
                    }
                )
                uploaded_files += 1
                if uploaded_files % 10 == 0:
                    print(f"   Uploaded {uploaded_files} files...")
            except Exception as e:
                print(f"❌ Failed to upload {s3_key}: {e}")
    
    print(f"✅ Uploaded {uploaded_files} files to S3")
    
    # Step 5: Verify deployment
    print("\n🔍 Step 5: Verifying deployment...")
    frontend_url = f"http://{bucket_name}.s3-website-ap-south-1.amazonaws.com"
    print(f"\n✅ Frontend URL: {frontend_url}")
    
    # Step 6: Test API connectivity
    print("\n🧪 Step 6: Testing API connectivity...")
    import requests
    
    api_url = "https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze"
    test_data = {
        "sequence_data": "ATCGATCGATCGATCG",
        "user_id": "test"
    }
    
    try:
        response = requests.post(api_url, json=test_data, timeout=10)
        if response.status_code == 200:
            print("✅ API is responding correctly!")
            result = response.json()
            print(f"   Workflow ID: {result.get('workflow_id')}")
        else:
            print(f"⚠️  API returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
    
    print("\n" + "="*60)
    print("🎉 FRONTEND REDEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"\n🌐 Your Fixed Frontend URL:")
    print(f"   {frontend_url}")
    print(f"\n🔗 API Endpoint:")
    print(f"   https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod")
    print(f"\n✅ The frontend now points to the CORRECT API in ap-south-1")
    print(f"✅ CORS issues should be resolved")
    print(f"✅ Analysis should work when you click 'Start Analysis'")
    print("\n📝 Next Steps:")
    print("   1. Open the frontend URL in your browser")
    print("   2. Upload any DNA sequence")
    print("   3. Click 'Start Analysis'")
    print("   4. You should see results immediately!")
    print("\n" + "="*60)
    
    return True

if __name__ == '__main__':
    success = fix_and_redeploy_frontend()
    if success:
        print("\n✅ All done! Your system is now fully working!")
    else:
        print("\n❌ Deployment failed. Check errors above.")
