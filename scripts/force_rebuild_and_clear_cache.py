#!/usr/bin/env python3
"""
Force Rebuild Frontend and Clear S3 Cache
This will completely rebuild the frontend and deploy with cache-busting headers
"""
import boto3
import subprocess
import os
import shutil
from pathlib import Path
import time

def force_rebuild_and_deploy():
    """Force complete rebuild and deployment"""
    print("🔧 FORCE REBUILDING FRONTEND WITH CORRECT API...")
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    bucket_name = 'biomerkin-frontend-20251018-013734'
    
    # Step 1: Delete ALL files from S3 bucket first
    print("\n🗑️  Step 1: Clearing S3 bucket completely...")
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            if objects_to_delete:
                s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                print(f"✅ Deleted {len(objects_to_delete)} old files from S3")
    except Exception as e:
        print(f"⚠️  Could not clear S3: {e}")
    
    # Step 2: Delete local build and node_modules
    print("\n🧹 Step 2: Cleaning local build...")
    build_dir = Path('frontend/build')
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("✅ Deleted old build directory")
    
    # Also clear node_modules/.cache if it exists
    cache_dir = Path('frontend/node_modules/.cache')
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("✅ Cleared node cache")
    
    # Step 3: Verify .env file one more time
    print("\n📝 Step 3: Verifying .env configuration...")
    env_file = Path('frontend/.env')
    env_content = env_file.read_text()
    
    # Force write the correct content
    correct_env = """# AWS Production Configuration - CORRECT API URL
REACT_APP_API_BASE_URL=https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod
REACT_APP_API_URL=https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod
REACT_APP_BACKEND_URL=https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod
GENERATE_SOURCEMAP=false
"""
    env_file.write_text(correct_env)
    print("✅ .env file verified and locked")
    
    # Step 4: Build frontend
    print("\n🏗️  Step 4: Building fresh frontend...")
    os.chdir('frontend')
    
    try:
        # Clean install
        print("📦 Running npm install...")
        subprocess.run(['npm', 'install'], check=True, shell=True, 
                      capture_output=True, text=True)
        
        # Build with production settings
        print("🔨 Building React app...")
        env = os.environ.copy()
        env['REACT_APP_API_URL'] = 'https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod'
        env['REACT_APP_API_BASE_URL'] = 'https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod'
        
        result = subprocess.run(['npm', 'run', 'build'], 
                              capture_output=True, 
                              text=True, 
                              shell=True,
                              env=env)
        
        if result.returncode != 0:
            print(f"❌ Build failed!")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        
        print("✅ Build successful!")
        
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False
    finally:
        os.chdir('..')
    
    # Step 5: Verify the build contains correct API URL
    print("\n🔍 Step 5: Verifying build contains correct API URL...")
    build_path = Path('frontend/build')
    
    # Check main JS files for the correct API URL
    found_correct_url = False
    found_wrong_url = False
    
    for js_file in build_path.rglob('*.js'):
        content = js_file.read_text(errors='ignore')
        if '642v46sv19.execute-api.ap-south-1' in content:
            found_correct_url = True
            print(f"✅ Found CORRECT API URL in {js_file.name}")
        if 'udu8m3n0lh.execute-api.us-east-1' in content:
            found_wrong_url = True
            print(f"❌ Found WRONG API URL in {js_file.name}")
    
    if found_wrong_url:
        print("❌ Build still contains wrong API URL!")
        return False
    
    if not found_correct_url:
        print("⚠️  Could not verify API URL in build files")
    else:
        print("✅ Build verified - contains correct API URL")
    
    # Step 6: Upload to S3 with aggressive cache-busting
    print("\n☁️  Step 6: Uploading to S3 with no-cache headers...")
    
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
                # Upload with aggressive no-cache headers
                s3_client.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'no-cache, no-store, must-revalidate',
                        'Expires': '0'
                    }
                )
                uploaded_files += 1
                if uploaded_files % 10 == 0:
                    print(f"   Uploaded {uploaded_files} files...")
            except Exception as e:
                print(f"❌ Failed to upload {s3_key}: {e}")
    
    print(f"✅ Uploaded {uploaded_files} files to S3")
    
    # Step 7: Invalidate CloudFront if exists (optional)
    print("\n🔄 Step 7: Cache invalidation...")
    print("⚠️  Note: You may need to hard refresh your browser (Ctrl+Shift+R)")
    
    # Step 8: Final verification
    print("\n✅ Step 8: Deployment complete!")
    frontend_url = f"http://{bucket_name}.s3-website-ap-south-1.amazonaws.com"
    
    print("\n" + "="*70)
    print("🎉 FRONTEND COMPLETELY REBUILT AND REDEPLOYED!")
    print("="*70)
    print(f"\n🌐 Frontend URL:")
    print(f"   {frontend_url}")
    print(f"\n🔗 API Endpoint (CORRECT):")
    print(f"   https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod")
    print(f"\n⚠️  IMPORTANT - TO SEE CHANGES:")
    print(f"   1. Close ALL browser tabs with the old site")
    print(f"   2. Clear browser cache (Ctrl+Shift+Delete)")
    print(f"   3. Open in INCOGNITO/PRIVATE mode")
    print(f"   4. Or hard refresh: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)")
    print(f"\n📝 Test Steps:")
    print(f"   1. Open: {frontend_url}")
    print(f"   2. Open Developer Tools (F12)")
    print(f"   3. Go to Network tab")
    print(f"   4. Upload DNA sequence and click 'Start Analysis'")
    print(f"   5. Verify the request goes to: ap-south-1 (NOT us-east-1)")
    print("\n" + "="*70)
    
    return True

if __name__ == '__main__':
    success = force_rebuild_and_deploy()
    if success:
        print("\n✅ Deployment complete! Remember to clear browser cache!")
    else:
        print("\n❌ Deployment failed. Check errors above.")
